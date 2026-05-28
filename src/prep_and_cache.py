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
        self._tac = TomlAppConfig()
        self._log = logging.getLogger(self._tac.logger_name)
        self._db = db
        so = StoreObjects()
        self._mf = so.get_object('MainFrame')
        self._org_data = {}
        self._fiscal_data = []

    async def organization(self, data, f_year, f_month):
        if data:
            # Make sure all fields were entered.
            empty_fields = [field for field, value in data.items()
                            if value in self._db._EMPTY_FIELDS]

            if len(empty_fields) != 0:
                ef = ', '.join([f for f in empty_fields])
                error = f"The '{ef}' field(s) must not be empty."
                self._log.warning(error)
            else:  # We add to the data dict.
                data, error = self._add_location_data(data)

                if data:  # Adding location can have errors.
                    sofy = data['start_of_fiscal_year']
                    p_year = sofy.year
                    p_month = sofy.month
                    p_day = sofy.day
                    # Need ISO date for the DB.
                    data['start_of_fiscal_year'] = sofy.isoformat()
                    earliest_fiscal_year = self.earliest_fiscal_year

                    if None in (f_year, f_month):
                        self.organization_data = data
                        await self.first_run_initialization(p_year, p_month,
                                                            p_day)
                        f_year = p_year
                        f_month = p_month
                    elif f_year == p_year:  # Update current year
                        self.organization_data = data
                    elif (f_year + 1) == p_year:
                        self.organization_data = data
                        await self.entered_next_year(p_year, p_month, p_day)
                    elif (earliest_fiscal_year and
                          (earliest_fiscal_year - 1) == p_year):
                        await self.entered_previous_year(p_year, p_month,
                                                         p_day)
                    else:
                        year = month = None
                        error = ("Cannot enter a year that is not immediately "
                                 "before or after the earliest or current "
                                 "year.")
                        self._log.warning(error)
                else:
                    self._log.warning(error)

            return await self._db._insert_update_config_data_table(
                f_year, month=f_month, data=data)

        # If no org data was entered.
        error = ("Organization Information data must be entered before "
                 "any other data can be entered.")
        self._log.warning(error)

    async def fiscal(self, data, f_year, f_month):
        items = [(f_year, f_month, 1, data['current_fiscal_year'],
                  data['work_on_this_fiscal_year'],
                  data['audit_complete'])]
        rowcount = await self._db.update_fiscal_year_table(items)
        self._log.debug("Inserted %s rows of fiscal year data.", rowcount)
        return data

    #async def fiscal_settings(self, ):

    async def first_run_initialization(self, year: int, month: int, day: int):
        """
        The first run of the application.

        .. note::

           1. Insert a year marked as current.
           2. Insert the next year.
           3. Insert all months.
           4. Insert fields from all panels.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        """
        # year, month, day, current, audit, work_on
        data = [(year, month, day, 1, 1, 0), (year+1, month, day, 0, 0, 0)]
        await self._db.insert_into_fiscal_year_table(data)
        # Populate the Badí months in the database.
        await self._db._insert_into_month_table()

        # Populate all panel fields in the database.
        for name, panel in self._mf.panels.items():
            if name in self._EXCLUDE_PANELS: continue
            panel_data = self._db.collect_panel_values(panel)
            await self._db._add_fields_to_field_type_table(panel_data)

    async def entered_next_year(self, year: int, month: int, day: int):
        """
        Follow up years.

        .. note::

           1. Update the previous current year making it not current.
           2. Update the previous next year to the current year.
           3. Insert a new next year.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        """
        data = [(year-1, month, day, 0, 0, 0), (year, month, day, 1, 1, 0)]
        await self._db.update_fiscal_year_table(data)
        await self._db.insert_into_fiscal_year_table(
            [(year+1, month, day, 0, 0, 0)])

    async def entered_previous_year(self, year: int, month: int, day: int):
        """
        Previous up years.

        .. note::

           Insert previous year.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        """
        await self._db.insert_into_fiscal_year_table(
            [(year, month, day, 0, 0, 0)])

    def _add_location_data(self, data: dict) -> dict:
        """
        Add the location data `iana_name`, `latitude` and, `longitude` to
        the organization data.

        :param dict data: The `organization` data.
        :returns: The updated `organization` data.
        :rtype: dict
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
                     "most likely UTC:00:00.")
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
    def organization_data(self) -> dict:
        """
        This property gets the organization data that are used throughout
        the application without having to do a select on the DB everytime.

        :returns: The organization data as defined by {<field name>: <value>}.
        :rtype: dict
        """
        return self._org_data

    @organization_data.setter
    def organization_data(self, values) -> None:
        """
        This property sets the organization constants that are used throughout
        the application without having to do a select on the DB everytime.

        .. note::

           Only the second and three fields are stored when the incoming
           values are a list otherwise the dict is used as is.

        :param list or dict values: A list of tuples where each tuple is the
                                    raw data for one field in the form of
                                    (PK, <field name>, <value>, <fiscal year>,
                                    <next year>, <ctime>, <mtime>).
        """
        if isinstance(values, list):
            self._org_data = {value[1]: value[2] for value in values}
        elif isinstance(values, dict):
            self._org_data = values
        else:
            msg = ("The argument 'value' must be a 'list' or 'dict', "
                   f"found {type(values)}.")
            self._log.error(msg)
            self._mf.statusbar_error = msg
            self._org_data = None

        assert isinstance(self._org_data, dict)

    @property
    def earliest_fiscal_year(self) -> tuple:
        """
        Get the earliest year in the `fiscal_year` table.
        """
        years = [items[1] for items in self.fiscal_years]
        return min(years) if years else ()

    @property
    def fiscal_years(self) -> list:
        return self._fiscal_data

    @fiscal_years.setter
    def fiscal_years(self, years: list) -> None:
        self._fiscal_data = years


class Cache:
    """
    Write-through cache, loaded once at startup, persists for the app lifetime.
    Supports lookup by ID and write-through DB updates.

    Storage keys
    ------------
    1. organization
    2. fiscal
    3. monthly
    """

    def __init__(self, db) -> None:
        """
        Constructor

        :param object db: The database self object.
        """
        self._db = db
        self._store: dict[str] = {}

    async def load(self, year: int, data: dict) -> None:
        """
        Call once at app startup to populate the cache from the DB.

        :param int year: Year of insert or update.
        :param dict data: Determine the data needed.

        .. note::

           The values are not needed when doing a select.
           organization data: {'longitude': 0.0, 'location_city_name': '',
                               'latitude': 0.0, 'location_prefix': 0,
                               'start_of_fiscal_year': <date>,
                               'locale_name': '', 'treasurer': '',
                               'total_membership': 0, 'iana_name': ''}
        """
        items = await self._db.select_from_config_data_table(data, year)
        values = {year: items} if items else {}
        self._store['organization'] = values
        items = await self._db.select_from_fiscal_year_table(year=year)
        values = {year: items} if items else {}
        self._store['fiscal'] = values
        items = await self._db._select_monthly_table(year)
        values = {year: items} if items else {}
        self._store['monthly'] = values

    @property
    def has_organization_cache_data(self) -> bool:
        """
        Check that the cache has Organization data.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._store.get('organization') is not None

    @property
    def has_fiscal_cache_data(self) -> bool:
        """
        Check that the cache has fiscal year data.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._store.get('fiacal') is not None

    @property
    def has_monthly_cache_data(self) -> bool:
        """
        Check that the cache has monthly data.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._store.get('monthly') is not None

    def get(self, entity_key: str, record_key: str) -> list | tuple:
        """
        Get records of the `entity_key` type. If a `record_key` is provided
        return just that record based on the `entity_key` type.

        :param str entity_key: This key determines the type of data returned.
        :param str record_key: This key determines a specific record in the
                               entity.
        :returns: Records based on the `entity_key`.
        :rtype: list
        """
        entity_data = self._store.get(entity_key, {})
        return entity_data.get(record_key)

    async def update(self, entity_key: str, record_key: str, changes: dict):
        """
        Update a record in the cache and push the change to the DB.

        :param str entity_key: This key determines the type of data returned.
        :param str record_key: This key determines a specific record in the
                               entity.
        :param dict data: The data to update.
        """
        record = self.get(entity_key, record_key)

        if record is None:
            raise KeyError(f"No {entity_key} record with key {record_key}")

        # Update cache first (instant, in-memory)
        year = changes.get('year')
        month = changes.get('month')
        data = changes.get('data')
        record = data

        # Then persist to DB
        match entity_key:
            case 'organization':
                await self._db.update_config_data_table(year, month, data)
            case 'fiscal':
                await self._db.update_fiscal_year_table(data)
            case 'monthly':
                await self._db.update_monthly_table(year, data)

    async def insert(self, entity_key: str, record_key: str, record: dict
                     ) -> dict:
        """
        Insert a new record into the DB and add it to the cache.

        :param str entity_key: This key determines the type of data returned.
        :param str record_key: This key determines a specific record in the
                               entity.
        :param dict data: The data to insert.
        :returns: The actual data inserted.
        :rtype: list
        """
        # DB returns full record
        match entity_key:
            case 'organization':
                year = record['year']
                month = record['month']
                data = record['data']
                await self._db.insert_into_config_data_table(year, month, data)
            case 'fiscal':
                data = record['data']
                await self._db.insert_into_fiscal_year_table(data)
            case 'monthly':
                year = record['year']
                data = record['data']
                await self._db.insert_into_monthly_table(year, data)

        self._store.setdefault(entity_key, {})[record_key] = data
        return data
