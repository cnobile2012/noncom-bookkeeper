# -*- coding: utf-8 -*-
#
# src/base_database.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import aiosqlite

from zoneinfo import ZoneInfo

from geopy.geocoders import Nominatim
from geopy import exc
from timezonefinder import TimezoneFinder

from .config import Settings
from .populate_collect_panel import PopulateCollect


class BaseDatabase(PopulateCollect, Settings):
    """
    This class provides the commonly used method for all basebase
    configurations.

    https://sqlite.org/
    https://www.w3schools.com/sql/
    https://docs.wxpython.org/
    """
    _T_FISCAL_YEAR = 'fiscal_year'
    _T_MONTH = 'month'
    _T_FIELD_TYPE = 'field_type'
    _T_REPORT_TYPE = 'report_type'
    _T_DATA = 'data'
    _T_REPORT_PIVOT = 'report_pivot'
    _SCHEMA = (
        (_T_FISCAL_YEAR,
         'pk INTEGER NOT NULL PRIMARY KEY',  # fy1fk or fy2fk in data
         'year INTEGER UNIQUE NOT NULL',
         'month INTEGER NOT NULL',
         'day INTEGER NOT NULL',
         'current INTEGER NOT NULL',
         'work_on INTEGER NOT NULL',
         'audit INTEGER NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_MONTH,
         'pk INTEGER NOT NULL PRIMARY KEY',  # mfk in data
         'month TEXT UNIQUE NOT NULL',
         'ord INTEGER UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_FIELD_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',  # ffk in data
         'field TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_DATA,
         'pk INTEGER NOT NULL PRIMARY KEY',  # dfk in report_pivot
         'value NOT NULL',
         'fy1fk INTEGER NOT NULL',
         'fy2fk INTEGER NOT NULL',
         'mfk INTEGER NULL',
         'ffk INTEGER NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_REPORT_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',  # rfk in report_pivot
         'report TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_REPORT_PIVOT,
         'rfk INTERGER NOT NULL', 'dfk INTEGER NOT NULL',
         f'FOREIGN KEY (rfk) REFERENCES {_T_REPORT_TYPE} (pk)',
         f'FOREIGN KEY (dfk) REFERENCES {_T_DATA} (pk)'),
        )
    _TABLES = [table[0] for table in _SCHEMA]
    _TABLES.sort()
    _EMPTY_FIELDS = ('', '0')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._org_data = {}
        self._fiscal_data = []

    #
    # Schema methods
    #

    async def create_db(self):
        """
        Create the database based on the fields currently defined.
        """
        if (not os.path.exists(self.user_data_fullpath) or
            not await self.has_schema):
            async with aiosqlite.connect(self.user_data_fullpath) as db:
                for params in self._SCHEMA:
                    table = params[0]
                    fields = ', '.join([field for field in params[1:]])
                    query = f"CREATE TABLE IF NOT EXISTS {table}({fields})"
                    await db.execute(query)
                    await db.commit()

    @property
    async def has_schema(self) -> bool:
        """
        Checks that the schema has been created.

        :returns: True if the schema has been created and False if it has not
                  been created.
        :rtype: bool
        """
        query = "SELECT name FROM sqlite_master"
        table_names = [table[0]
                       for table in await self._do_select_query(query)
                       if not table[0].startswith('sqlite_')]
        table_names.sort()
        check = table_names == self._TABLES

        if not check:
            msg = ("Database table count is wrong it should be "
                   f"'{self._TABLES}' found '{table_names}'")
            self._log.error(msg)
            self._mf.statusbar_error = msg

        return check

    #
    # Initialization methods
    #

    async def populate_panels(self):
        """
        Populate all panels that have data in the database.
        """
        year, month = await self._get_current_fiscal_year()

        if None not in (year, month):
            self._log.info("Populating all panels.")
            self._fiscal_data = await self.select_from_fiscal_year_table()

            for name, panel in self._mf.panels.items():
                data = self._collect_panel_values(panel)
                values = await self.select_from_data_table(name, data, year,
                                                           month)

                # Needed when the app has been run at least one time before.
                if name == 'organization' and values:
                    self.organization_data = values

                # Add any new fields to the database.
                await self._add_fields_to_field_type_table(data)
                panel.initializing = True
                self.populate_panel_values(name, panel, values)
                panel.initializing = False

    async def save_to_database(self, name: str, panel: wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param str name: The internal name of the current panel.
        :param wx.Panel panel: Any of the panels that have collected data.
        :returns: None if no errors, otherwise the error message.
        :rtype: None or str

        .. note::

           1. Empty (default) organization data:
              {'locality_prefix': 0, 'locale_name': '',
               'total_membership': '', 'treasurer': '',
               'start_of_fiscal_year': '<today>',
               'location_city_name': ''}
        """
        error = None
        data = self._collect_panel_values(panel)
        # Make sure all fields were entered.
        empty_list = [field for field, value in data.items()
                      if value in self._EMPTY_FIELDS]

        if len(empty_list) != 0:
            ef = ', '.join([f for f in empty_list])
            error = f"The '{ef}' field(s) must not be empty."
            self._log.warning(error)
        else:
            year, month = await self._get_current_fiscal_year()
            seq_flag = False

            if name == 'organization':
                data = self._add_location_data(data)

                if not isinstance(data, dict):
                    error = data
                else:
                    sofy = data['start_of_fiscal_year']
                    entered_date = sofy.b_date
                    earliest_year = self.earliest_year
                    # Need ISO date for the DB.
                    data['start_of_fiscal_year'] = sofy.isoformat()

                    if not year or not month:            # First ever entry
                        self.organization_data = data
                        await self.first_run_initialization(entered_date)
                        year, month, day = entered_date
                    elif year == entered_date[0]:        # Update current year
                        self.organization_data = data
                        year, month, day = entered_date
                    elif (year + 1) == entered_date[0]:  # Next current year
                        self.organization_data = data
                        await self.entered_next_year(entered_date)
                        year, month, day = entered_date
                    elif (earliest_year and              # Previous year.
                          (earliest_year - 1) == entered_date[0]):
                        await self.entered_previous_year(entered_date)
                        year, month, day = entered_date
                    else:
                        year = month = None
                        seq_flag = True
                        error = ("Cannot enter a year that is not immediately "
                                 "before or after the earliest or current "
                                 "year.")

                    if year and month:
                        error = await self._insert_update_data_table(
                            name, year, month, data)
                        await self.populate_panels()
                    elif seq_flag:
                        self._log.warning(error)
                    else:  # If no org data was entered.
                        error = ("Cannot enter Fiscal Year data before the "
                                "Organization Information has been entered.")
                        self._log.warning(error)

        return error

    async def first_run_initialization(self, date: tuple):
        """
        The first run of the application.

        .. note::

           1. Insert a year marked as current.
           2. Insert the next year.
           3. Insert all months.
           4. Insert fields from all panels.

        :param tuple date: This is the UI entered date.
        """
        year, month, day = date
        # year, month, day, current, audit, work_on
        data = [(year, month, day, 1, 1, 0), (year+1, month, day, 0, 0, 0)]
        await self.insert_into_fiscal_year_table(data)
        # Populate the Badí months in the database.
        await self._insert_into_month_table()

        # Populate all panel fields in the database.
        for name, panel in self._mf.panels.items():
            panel_data = self._collect_panel_values(panel)
            await self._add_fields_to_field_type_table(panel_data)

    async def entered_next_year(self, date: tuple):
        """
        Follow up years.

        .. note::

           1. Update the previous current year.
           2. Update the previous next year to the current year.
           3. Insert a new next year.

        :param tuple date: This is the UI entered date.
        """
        year, month, day = date
        data = [(year-1, month, day, 0, 0, 0), (year, month, day, 1, 1, 0)]
        await self.update_fiscal_year_table(data)
        await self.insert_into_fiscal_year_table(
            [(year+1, month, day, 0, 0, 0)])

    async def entered_previous_year(self, date: tuple):
        """
        Previous up years.

        .. note::

           Insert previous year.

        :param tuple date: This is the UI entered date.
        """
        year, month, day = date
        await self.insert_into_fiscal_year_table([(year, month, day, 0, 0, 0)])

    async def _get_current_fiscal_year(self):
        """
        Get the current fiscal year.
        """
        fy = await self.select_from_fiscal_year_table(current=1)

        if len(fy):
            year = fy[0][1]
            month = fy[0][2]
        else:  # Only for first time use.
            year = month = None

        return year, month

    #
    # Database access methods.
    #

    async def _add_fields_to_field_type_table(self, data: dict) -> None:
        """
        Add fields to the field_type table if they don't already exist.

        :param dict data: The data from the Organization Information panel in
                          the form of: {<field name>: <value>,...}.
        """
        items = await self.select_from_field_type_table(data)
        old_fields = [item[1] for item in items]
        fields = self._find_fields(data, old_fields)

        if fields:
            await self.insert_into_field_type_table(fields)

    async def _insert_into_month_table(self) -> None:
        """
        Populate the `month` table with all months.
        """
        items = await self.select_from_month_table()
        months = self._ordered_month()

        if not items:  # Insert all months and their order.
            await self.insert_into_month_table(months)
        else:  # Insert only months and their order if not in the database.
            data = [item[1:3] for item in items]
            con_months = [(month, order) for order, month in months.items()]

            for item in data:
                if item not in con_months:
                    await self.insert_into_month_table(item)

    async def _insert_update_data_table(self, name: str, year: int, month: int,
                                        data: dict) -> None:
        """
        Insert or update `data` table.

        :param str name: Panel name.
        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>,...}.
        :returns: None if no errors. If an error a, error message.
        :rtype: None or str
        """
        error = None
        c_year, c_month = await self._get_current_fiscal_year()
        values = await self.select_from_data_table(name, data, c_year, c_month)

        if not values:  # Do insert
            await self.insert_into_data_table(year, month, data)
        else:
            insert_data = {}
            update_data = []
            #        field,    pk,      y1
            items = {item[1]: (item[0], item[3]) for item in values}

            for field, value in data.items():  # Loop through incoming data.
                pk, y1 = items.get(field, (None, None))  # Selected data

                if not pk or not y1:           # Error condition
                    error = f"Could not find field {field} in {data}."
                    self._log.error(error)
                    break

                if year != y1:                 # Insert
                    insert_data[field] = value
                else:                          # Update
                    update_data.append((pk, value))

            if insert_data:  # Do insert
                await self.insert_into_data_table(year, month, insert_data)

            if update_data:  # Do update
                await self.update_data_table(year, month, update_data)

        return error

    async def _do_select_query(self, query: str, params: tuple=()) -> list:
        """
        Do the actual query and return the results.

        :param str query: The SQL query to do.
        :returns: A list of the data.
        :rtype: list
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute(query, params) as cursor:
                values = await cursor.fetchall()

        return values

    async def _do_insert_query(self, query: str, data: list) -> None:
        """
        Do the insert query.

        :param str query: The SQL query to do.
        :param list data: Data to insert into the Data table.
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            try:
                await db.executemany(query, data)
            except Exception as e:
                self._log.error(str(e), exc_info=True)
            else:
                await db.commit()

    async def _do_update_query(self, query: str, data: list) -> None:
        """
        Do the update query.

        :param str query: The SQL query to do.
        :param list data: Data to update into the Data table.
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            try:
                await db.executemany(query, data)
            except Exception as e:
                self._log.error(str(e), exc_info=True)
            else:
                await db.commit()

    #
    # Utilitu methods
    #

    def _find_fields(self, new: list, old: list) -> set:
        """
        Find the fields to select or insert.

        :param list or dict new: The new fields in the form of:
                                 [<field name>,...].
        :param list old: The old fields in the form of: [<field name>,...].
        :returns: A list of fields.
        :rtype: list
        """
        new_fields = set(new)  # Just get the keys if a dict.
        old_fields = set(old)
        return new_fields - old_fields

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
            result = self._find_timezone(location_city_name)

            if isinstance(result, tuple):
                iana, lat, lon = result
                data['iana_name'] = iana
                data['latitude'] = lat
                data['longitude'] = lon
            else:
                data = None
                error = result
        else:
            error = ("The 'location_city_name' field was not found, this "
                     "will cause some dates to be set to the wrong timezone, "
                     "most likely UTC:00:00.")
            self._log.warning(error)
            data = None

        return data if isinstance(data, dict) else error

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

        return error if error else (iana, lat, lon)

    #
    # Properties
    #

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
    def organization_data(self, values: list) -> None:
        """
        This property sets the organization constants that are used throughout
        the application without having to do a select on the DB everytime.

        .. note::

           1. It is used in the `bahai_database.populate_panels`, and
              `generic_database.populate_panels` methods.
           2. Only the second and three fields are stored when the incoming
              values are a list otherwise the dict is used as is.

        :param list or dict values: A list of tuples where each tuple is the
                                    raw data for one field in the form of
                                    (PK, <field name>, <value>, <fiscal year>,
                                    <next year>, <c_time>, <m_time>).
        """
        if isinstance(values, list):
            self._org_data = {value[1]: value[2] for value in values}
        else:
            self._org_data = values

    @property
    def tzinfo(self):
        iana_name = self.organization_data.get('iana_name')
        return ZoneInfo(iana_name if iana_name else 'UTC')

    @property
    def earliest_year(self):
        """
        Get the earliest year in the `fiscal_year` table.
        """
        years = [items[1] for items in self._fiscal_data]
        return min(years) if years else None
