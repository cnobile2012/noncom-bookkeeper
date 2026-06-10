# -*- coding: utf-8 -*-
#
# src/prep_and_cache.py
#
__docformat__ = "restructuredtext en"

import logging

from geopy.geocoders import Nominatim
from geopy import exc
from timezonefinder import TimezoneFinder

from .config import TomlAppConfig
from .utilities import StoreObjects


class DataPreperation:
    """
    All data in the data and fiscal_year tables need to prepared before
    cached or saved to the database.
    """
    _EXCLUDE_PANELS = ('fiscal', 'monthly')

    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tac = TomlAppConfig()
        self._log = logging.getLogger(self._tac.logger_name)
        self.db = db
        so = StoreObjects()
        self._mf = so.get_object('MainFrame')

    async def organization(self, data, f_year, f_month) -> int:
        """
        Insert or update the organization data.

        :param dict data: The data to insert or update.
        :param int f_year: The fiscal year.
        :param int f_month: The month that the fiscal year starts.
        :returns: The row count caused by the insert or update.
        :rtype: int
        """
        if data:
            # Make sure all fields were entered.
            empty_fields = [field for field, value in data.items()
                            if value == '']

            if len(empty_fields) != 0:  # This should insert
                ef = ', '.join([f for f in empty_fields])
                error = f"The '{ef}' field(s) must not be empty."
                self._log.warning(error)
            else:  # This should update
                data, error = self._add_location_data(data)

                if data:  # Adding location can have errors.
                    sofy = data['start_of_fiscal_year']
                    p_year = sofy.year
                    p_month = sofy.month
                    p_day = sofy.day
                    # Need ISO date for the DB.
                    data['start_of_fiscal_year'] = sofy.isoformat()
                    earliest_fy = self._earliest_fiscal_year

                    if None in (f_year, f_month):
                        await self._first_run_initialization(
                            p_year, p_month, p_day)
                        f_year = p_year
                        f_month = p_month
                    elif (f_year + 1) == p_year:
                        await self._enter_next_year(p_year, p_month, p_day)
                    elif earliest_fy and (earliest_fy - 1) == p_year:
                        await self._enter_previous_year(
                            p_year, p_month, p_day)
                    else:
                        year = month = None
                        error = ("Cannot enter a year that is not immediately "
                                 "before or after the earliest or current "
                                 "year.")
                        self._log.warning(error)
                else:
                    self._log.warning(error)

            rowcount = await self.db._insert_update_config_data_table(
                f_year, month=f_month, data=data)
            return rowcount

        # If no org data was entered.
        error = ("Organization Information data must be entered before "
                 "any other data can be entered.")
        self._log.warning(error)
        return 0

    async def fiscal(self, data: dict, f_year: int, f_month: int) -> list:
        """
        Convert panel data to data appropreate for inserting into the database,
        then update it.

        :param dict data: Panel data.
        :param int f_year: The current fiscal year.
        :param int f_month: The current fiscal year month.
        :returns: The updated fiscal year data.
        :rtype: list
        """
        items = [(f_year, f_month, 1, data['current_fiscal_year'],
                  data['work_on_this_fiscal_year'], data['audit_complete'])]
        values = {'year': f_year, 'data': items}
        rowcount = await self.db.cache.update(
            self.db._T_FISCAL_YEAR, {'data': items})
        self._log.debug("Inserted %s row(s) of fiscal year data.", rowcount)
        return items

    async def _first_run_initialization(self, year: int, month: int, day: int):
        """
        The first run of the application.

        .. note::

           1. Insert a fiscal year marked as current.
           2. Insert the next fiscal year.
           3. Insert all months.
           4. Insert fields from all current panels.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        """
        # year, month, day, current, audit, work_on
        data = {'data':[(year, month, day, 1, 1, 0),
                        (year+1, month, day, 0, 0, 0)]}
        await self.db.cache.insert(self.db._T_FISCAL_YEAR, data)

        #await self.db.insert_into_fiscal_year_table(data)
        # Populate the Badí months in the database.
        data = {'data': self.db.ordered_month()}
        await self.db.cache.insert(self.db._T_MONTH, data)
        #await self.db._insert_into_month_table()

        # Populate all panel fields in the database.
        for name, panel in self._mf.panels.items():
            if name in self._EXCLUDE_PANELS: continue
            panel_data = self.db.collect_panel_values(panel)
            await self.db._add_fields_to_field_type_table(panel_data)

    async def _enter_next_year(self, year: int, month: int, day: int) -> int:
        """
        Enter the next fiscal year and update the previous two years.

        .. note::

           1. Update the previous current year making it not current.
           2. Update the previous next year to the current year.
           3. Insert a new next year.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        :returns: The number of DB rows affected.
        :rtype: int
        """
        rowcount = await self.db.cache.update(
            self.db._T_FISCAL_YEAR, {'data': [(year-1, month, day, 0, 0, 0),
                                              (year, month, day, 1, 1, 0)]})
        rowcount += await self.db.cache.insert(
            self.db._T_FISCAL_YEAR, {'data': [(year+1, month, day, 0, 0, 0)]})
        return rowcount

    async def _enter_previous_year(self, year: int, month: int, day: int
                                   ) -> int:
        """
        Enter the next year.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        :returns: The number of DB rows affected.
        :rtype: int
        """
        rowcount = await self.db.cache.insert(
            self.db._T_FISCAL_YEAR, {'data': [(year, month, day, 0, 0, 0)]})
        return rowcount

    def _add_location_data(self, data: dict) -> tuple:
        """
        Add the location data `iana_name`, `latitude` and, `longitude` to
        the organization data.

        :param dict data: The `organization` data.
        :returns: The updated `organization` data and any error that may
                  have happened.
        :rtype: tuple

        .. note::

           Organization data structure:
           {'iana_name': 'America/New_York', 'latitude': '<your latutude>',
            'locale_name': '<your locale>', 'locality_prefix': '0',
            'location_city_name': '<your city name>',
            'longitude': '<your longitude>',
            'start_of_fiscal_year': '0183-03-05', 'total_membership': '20',
            'treasurer': '<your treasurer>'}
        """
        location_city_name = data['location_city_name']

        if location_city_name:
            iana, lat, lon, error = self._find_timezone(location_city_name)

            if error is None:
                data['iana_name'] = iana
                data['latitude'] = lat
                data['longitude'] = lon
            else:
                data = None
        else:
            error = ("The 'location_city_name' field was not found, this "
                     "will cause some dates to be set to the wrong timezone, "
                     "most likely to UTC:00:00.")
            data = None

        return data, error

    def _find_timezone(self, address: str):
        """
        Find the IANA timezone name, latitude, and longitude.

        :param str address: The address, City, or town used to find the
                            required information.
        :returns: The IANA timezone name, latitude, and longitude.
        :rtype: tuple
        """
        error = None
        geolocator = Nominatim(user_agent='nc-bookkeeper')

        try:
            location = geolocator.geocode(address)
        except exc.GeocoderError as e:
            error = f"Could not get information on {address}"
            self._log.error(error + ", %s", e)
        else:
            error = None

        if location:
            lat = location.latitude
            lon = location.longitude
            tf = TimezoneFinder()
            iana = tf.timezone_at(lng=lon, lat=lat)
        elif error:
            iana = lat = lon = None
        else:
            iana = lat = lon = None
            error = f"Cannot find the timezone for '{address}'."

        return iana, lat, lon, error

    @property
    def _earliest_fiscal_year(self) -> tuple:
        """
        Get the earliest year in the `fiscal_year` table.
        """
        years = []

        for year in self.db.cache.available_years:
            fy = self.db.cache.get(self.db._T_FISCAL_YEAR, year=year)
            if not fy: break
            years.append(fy[0][1])

        return min(years) if years else None

    @property
    def organization_data(self) -> dict:
        """
        This property gets the organization data that are used throughout
        the application.

        :returns: The organization data as defined by {<field name>: <value>}.
        :rtype: dict
        """
        items = self.db.cache.get(self.db._T_DATA, r_type='organization')
        return {item[1]: item[2] for item in items}


class Cache:
    """
    Write-through cache, loaded once at startup, persists for the app lifetime.
    Supports write-through DB updates.
    """
    ORG_FIELDS = ['longitude', 'location_city_name', 'latitude',
                  'locality_prefix', 'start_of_fiscal_year', 'locale_name',
                  'treasurer', 'total_membership', 'iana_name']
    ORG_FIELDS.sort()

    def __init__(self, db, *args, **kwargs) -> None:
        """
        Constructor

        :param object db: The database self object.
        """
        super().__init__(*args, **kwargs)
        self._tac = TomlAppConfig()
        self.db = db
        self._log = logging.getLogger(self._tac.logger_name)
        self._flush_cache()
        self._year = None

    @property
    def has_cache(self):
        return self._store != {}

    def _flush_cache(self) -> None:
        """
        Remove all data from the cache.
        """
        self._store: dict[str] = {}
        self._year = None

    @property
    def year(self) -> int | None:
        return self._year

    @year.setter
    def year(self, year: int) -> None:
        self._year = year

    async def load(self) -> None:
        """
        Call once at app startup to populate the cache from the DB.

        .. note::

           1. The `field_type` data is stored by the table name only.
           2. The `config_data` is stored by the year and table name.
           3. The `fiscal_year` data is stored by the year and table name.
           4. The `month`  data is stored by the year and table name.
           5. The `monthly`  data is stored by the year and table name.
        """
        # field_type  -- Also sets the year.
        await self._load_field_type()
        # month
        await self._load_month()
        # fiscal_year
        await self._load_fiscal_year()

        if self.year:
            # config_data
            await self._load_config_data()
            # monthly
            await self._load_monthly()
            self._log.info("Loaded cache with DB data, year set to %s.",
                           self.year)

    async def reload(self, table_name: str) -> None:
        """
        Reload specific table data.
        """
        if self.has_cache and self.year:
            match table_name:
                case self.db._T_FIELD_TYPE:
                    await self._load_field_type()
                    #await self._load_config_data()  # dependency
                case self.db._T_FISCAL_YEAR:
                    await self._load_fiscal_year()
                case self.db._T_DATA:
                    await self._load_config_data()
                case self.db._T_MONTH:
                    await self._load_month()
                case self.db._T_MONTHLY:
                    await self._load_monthly()
                case _:
                    raise ValueError(f"Unknown table: {table_name}")

            self._log.info("Reloaded the %s table.", table_name)
        else:
            await self.load()

    async def _load_field_type(self) -> None:
        items = await self.db.select_from_field_type_table(None)
        self._store[self.db._T_FIELD_TYPE] = items

    async def _load_fiscal_year(self) -> None:
        items = await self.db.select_from_fiscal_year_table()

        if isinstance(items, tuple):
            items = [items]

        for fy in sorted(items, key=lambda x: x[1]):
            year = fy[1]

            if fy[4] == 1:  # Is current year
                self.year = year

            self._store[year] = {}
            self._store[year][self.db._T_FISCAL_YEAR] = [fy]

    async def _load_config_data(self) -> None:
        items = await self.db.select_from_config_data_table(
            self.fields, self.year)
        self._store[self.year][self.db._T_DATA] = items

    async def _load_month(self) -> None:
        items = await self.db.select_from_month_table()
        self._store[self.db._T_MONTH] = items

    async def _load_monthly(self) -> None:
        items = await self.db.select_from_monthly_table(self.year)
        self._store[self.year][self.db._T_MONTHLY] = items

    @property
    def has_fields_data(self) -> bool:
        """
        Check that the cache has fields data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self._store.get(self.db._T_FIELD_TYPE, {})) > 0

    @property
    def has_organization_cache_data(self) -> bool:
        """
        Check that the cache has Organization data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_DATA, r_type='organization')) > 0

    @property
    def has_budget_cache_data(self) -> bool:
        """
        Check that the cache has Budget data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_DATA, r_type='budget')) > 0

    @property
    def has_fiscal_cache_data(self) -> bool:
        """
        Check that the cache has fiscal year data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_FISCAL_YEAR)) > 0

    @property
    def has_month_cache_data(self) -> bool:
        """
        Check that the cache has month data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_MONTH)) > 0

    @property
    def has_monthly_cache_data(self) -> bool:
        """
        Check that the cache has monthly data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_MONTHLY)) > 0

    @property
    def fields(self):
        return [itm[1] for itm in self._store.get(self.db._T_FIELD_TYPE, ())]

    @property
    def get_bgt_fields(self):
        fields = self.fields
        bgt_fields = list(set(fields) - set(self.ORG_FIELDS)) if fields else []
        bgt_fields.sort()
        return bgt_fields

    @property
    def available_years(self):
        return [key for key in self._store.keys()
                if key != self.db._T_FIELD_TYPE]

    def get(self, table_name: str, *, year: int=None, r_type: str=None
            ) -> list:
        """
        Get records of the `table_name`. If a `r_type` is provided return
        just that record based on the `table_name` type.

        :param int year: The fiscal year.
        :param str table_name: The DB table to query.
        :param str r_type: This determines a specific record in the entity.
        :returns: Records based on the `table_name`.
        :rtype: list

        .. note::

           1. The `fields` data is accessed by the `fields` key.
           2. There are two types of `config_data` data.
              a. The `organization` data is accessed by the year, table name,
                 and type.
              b. The `budget` data is accessed by the year, table name, and
                 type.
           3. The `fiscal_year` data is accessed by the year and table name.
           4. The `month`  data is accessed by the year and table name.
           5. The `monthly`  data is accessed by the year and table name.
        """
        year = self.year if year is None else year

        match table_name:
            case self.db._T_FIELD_TYPE:
                data = self._store.get(self.db._T_FIELD_TYPE, [])
            case self.db._T_FISCAL_YEAR:
                data = self._store.get(year, {})
                data = data.get(self.db._T_FISCAL_YEAR, []) if data else []
            case self.db._T_DATA:
                if r_type is not None:
                    items = self._store.get(year, {}).get(self.db._T_DATA, [])

                    match r_type:
                        case 'organization':
                            fields = self.ORG_FIELDS
                        case 'budget':
                            fields = self.get_bgt_fields
                        case _:
                            assert r_type in ('organization', 'budget'), (
                                f"Invalid `r_type`, found {r_type}.")

                    data = [item for item in items if item[1] in fields]
                else:
                    data = {}
            case self.db._T_MONTH:
                data = self._store.get(self.db._T_MONTH, [])
            case self.db._T_MONTHLY:
                data = self._store.get(year, {}).get(self.db._T_MONTHLY, [])

        self._log.info("Retrived '%s' data.", table_name)
        return data

    async def insert(self, table_name: str, record: dict) -> int:
        """
        Insert a new record into the DB and add it to the cache. All records
        are in a dict even if there is only one item thus keeping a uniform
        interface.

        :param str table_name: The DB table to query to insert into.
        :param dict data: The data to insert.
        :returns: The insertion rowcount.
        :rtype: int
        """
        match table_name:
            case self.db._T_FIELD_TYPE:
                # Name, now, now
                data = record['data']
                rowcount= await self.db.insert_into_field_type_table(data)
                await self._load_field_type()
            case self.db._T_FISCAL_YEAR:
                data = record['data']
                rowcount = await self.db.insert_into_fiscal_year_table(data)
                await self._load_fiscal_year()
            case self.db._T_DATA:
                year = record['year']
                month = record['month']
                data = record['data']
                rowcount = await self.db.insert_into_config_data_table(
                    year, month, data)
                await self._load_config_data()
            case self.db._T_MONTH:
                data = record['data']
                rowcount = await self.db.insert_into_month_table(data)
                await self._load_month()
            case self.db._T_MONTHLY:
                year = record['year']
                data = record['data']
                rowcount = await self.db.insert_into_monthly_table(year, data)
                await self._load_monthly()
            case _:
                data = []
                rowcount = 0

        self._log.info("Inserted data into the %s table.", table_name)
        return rowcount

    async def update(self, table_name: str, changes: dict) -> int:
        """
        Update a record in the cache and push the change to the DB.

        :param str table_name: The DB table to update.
        :param dict changes: The data to update.
        :returns: The insertion rowcount.
        :rtype: int
        """
        data = changes.get('data')

        # Then persist to DB
        match table_name:
            case self.db._T_FISCAL_YEAR:
                rowcount = await self.db.update_fiscal_year_table(data)
                await self._load_fiscal_year()
            case self.db._T_DATA:
                rowcount = await self.db.update_config_data_table(data)
                await self._load_config_data()
            case self.db._T_MONTHLY:
                year = changes.get('year')
                rowcount = await self.db.update_monthly_table(year, data)
                await self._load_monthly()

        self._log.info("Updated data in the %s table.", table_name)
        return rowcount
