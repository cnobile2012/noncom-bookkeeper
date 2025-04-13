# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

import aiosqlite
import time
import datetime as dtime
import wx

from .config import TomlMetaData
from .utilities import StoreObjects

import ephem
from zoneinfo import ZoneInfo
from badidatetime import UTC, datetime

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


class Database(TomlMetaData):
    __YEAR = 'year'
    __MONTH = 'month'
    __FIELD_TYPE = 'field_type'
    __REPORT_TYPE = 'report_type'
    __DATA = 'data'
    __REPORT_PIVOT = 'report_pivot'
    _SCHEMA = (
        (__YEAR,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'start_date TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__MONTH,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'month TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__FIELD_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'field TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__REPORT_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'report TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__DATA,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'value NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL',
         'ffk INTEGER NOT NULL',
         'mfk INTEGER NOT NULL'),
        (__REPORT_PIVOT,
         'rfk INTERGER NOT NULL', 'dfk INTEGER NOT NULL',
         f'FOREIGN KEY (rfk) REFERENCES {__REPORT_TYPE} (pk)',
         f'FOREIGN KEY (dfk) REFERENCES {__DATA} (pk)'),
        )
    _TABLES = [table[0] for table in  _SCHEMA]
    _TABLES.sort()
    _EMPTY_FIELDS = ('', '0')
    __DEFAULT_LOCATION = 'Tehran Persia'
    __TIMEZONE = 'Asia/Tehran'
    __LAT = 35.6892523
    __LON = 51.3896004
    # ((MOD(year, 4) = 0) * ((MOD(year, 100) <> 0) + (MOD(year, 400) = 0)) = 1)
    LEAP_YEAR = lambda self, year: (
        (year % 4 == 0) * ((year % 100 != 0) + (year % 400 == 0)) == 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # [{pk: <value>, field: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._field_types = []
        # [{pk: <value>, report: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._report_types = []
        self._mf = StoreObjects().get_object('MainFrame')
        self._sunset_year_data = [] # Updated later
        self._org_data = None

    async def create_db(self):
        """
        Create the database based on the fields currently defined.
        """
        if not await self.has_schema:
            async with aiosqlite.connect(self.user_data_fullpath) as db:
                for params in self._SCHEMA:
                    table = params[0]
                    fields = ', '.join([field for field in params[1:]])
                    query = f"CREATE TABLE IF NOT EXISTS {table}({fields})"
                    await db.execute(query)
                    await db.commit()

    async def populate_panels(self):
        """
        Populate all panels that have data in the database.
        """
        for name, panel in self._mf.panels.items():
            data = self._collect_panel_values(panel)
            await self._add_fields_to_field_type_table(data)


            values = await self.select_from_data_table(b_year, b_month, data)

            if name == 'organization':
                self._org_data = {value[0]: value[2] for value in values}

            self.populate_panel_values(name, panel, values)

    @property
    async def has_schema(self) -> bool:
        """
        Checks that the schema has been created.

        :return: True if the schema has been created and False if it has not
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

    @property
    def has_org_info_data(self) -> bool:
        """
        Check that the db has the Organization Information.

        :return: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('organization')

    @property
    def has_budget_data(self) -> bool:
        """
        Check that the db has the Yearly Budget data.

        :return: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('budget')

    @property
    def has_month_data(self) -> bool:
        """
        Check that the db has the Organization Information.

        :return: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('month')

    def _check_panels_for_entries(self, name: str) -> bool:
        """
        Check that the given panel name has entries.

        :return: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        panel = self._mf.panels[name]
        data = self._collect_panel_values(panel)
        return all([item not in self._EMPTY_FIELDS for item in data.values()])

    async def save_to_database(self, panel: wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param panel: Any of the panels that has collected data.
        :type panel: wx.Panel
        """
        data = self._collect_panel_values(panel)

        for field, value in data.items():
            if value in self._EMPTY_FIELDS:
                msg = f"The '{field}' field must have data in it."
                self._log.warning(msg)
                self._mf.statusbar_warning = msg

            if name == 'organization' and self.config_type == 'bahai':
                print(data)
                start_year = data['start_year']
                tz, lat, lon = self._find_timezone(address)
                self._sunset_year_data[:] = self._get_sunset_datetimes(
                    start_year, tz)
                month = None
            else:
                start_time = None
                month = None


        # *** TODO *** Lots more to do here.



        await self._insert_values_in_data_table(data)
        panel.dirty = False

    def _collect_panel_values(self, panel: wx.Panel,
                              convert_to_utc: bool=False) -> dict:
        """
        Collects the data from the panel's widgets.

        :param panel: The panel to collect data from.
        :type panel: wx.Panel
        :param convert_to_utc: True if wx.DateTime field's should be
                               converted to UTC and False if they are not
                               to be converted (default is False).
        :return: A dictonary of db field names and values.
        :rtype: dict
        """
        data = {}

        for c_set in self._find_children(panel):
            name0 = c_set[0].__class__.__name__
            name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
            db_name = self._make_db_name(c_set[0].GetLabelText())

            if name0 == 'RadioBox':
                data[db_name] = self._scrub_value(c_set[0].GetSelection())
            elif name0 == 'ComboBox':
                data[db_name] = c_set[0].GetSelection()
            elif name0 == 'StaticText':
                value = c_set[1].GetValue()

                if name1 == 'TextCtrl':
                    financial = True if c_set[1].financial else False
                    data[db_name] = self._scrub_value(value,
                                                      financial=financial)
                elif name1 == 'DatePickerCtrl':
                    data[db_name] = self._scrub_value(value, convert_to_utc)

        return data

    def populate_panel_values(self, name: str, panel: wx.Panel,
                              values: list) -> None:
        """
        Poplulate the named panel with the database values.

        :param name: The name of the panel.
        :type name: str
        :param values: The database values to be used to poplulate the panel.
        :type values: list
        """
        if (data := {item[0]: item[1:] for item in values}):
            for c_set in self._find_children(panel):
                name0 = c_set[0].__class__.__name__
                name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
                db_name = self._make_db_name(c_set[0].GetLabelText())
                value = data[db_name][1]

                if name0 == 'RadioBox':
                    c_set[0].SetSelection(value)
                elif name0 == 'ComboBox':
                    c_set[0].SetSelection(value)
                elif name0 == 'StaticText':
                    if name1 == 'TextCtrl':
                        financial = True if c_set[1].financial else False
                        value = self.db_to_value(value) if financial else value

                        if name == 'month':
                            if (not value
                                and db_name == 'total_membership_month'):
                                value = self._org_data['total_membership']
                            elif not value and db_name == 'treasurer_month':
                                value = self._org_data['treasurer']
                        c_set[1].SetValue(value)
                    elif name1 == 'DatePickerCtrl':
                        c_set[1].SetValue(
                            self._convert_date_to_local_time(value))

    def _find_children(self, panel: wx.Panel) -> list:
        """
        Find the children in the panel that hold data.

        :param panel: The panel to collect data from.
        :type panel: wx.Panel
        :return: A list of child sets.
        :rtype: list
        """
        children = []

        for child in panel.GetChildren():
            add = False
            name = child.__class__.__name__

            if (name == 'StaticLine' or
                name == 'StaticText' and not child.GetLabel().endswith(':')):
                continue
            elif name == 'ComboBox':
                add = True

            children.append(child)
            if add: children.append(None)

        return [children[i:i+2] for i in range(0, len(children), 2)]

    async def _add_fields_to_field_type_table(self, data: dict) -> None:
        """
        Add fields to the FieldType table if they don't already exist.

        :param data: The data from the Organization Information panel in the
                     form of: {<field name>: <value>,...}.
        :type data: dict
        """
        items = await self._select_from_field_type_table(data)
        old_fields = [item[1] for item in items]
        fields = self._find_fields(data, old_fields)

        if fields:
            await self._insert_field_type_data(fields)

    async def _select_from_field_type_table(self, data: dict) -> list:
        """
        Read from the FieldType the fields in the data argument.

        :param data: The data from the Organization Information panel in the
                     form of: {<field name>: <value>,...}.
        :type data: dict
        :return: The values read from the FieldType table in the form of
                 [(<pk>, <field>, <rids>, <c_time>, <m_time>), ...].
        :rtype: list of tuples
        """
        assert data, f"There must be valid data, found '{data}'."
        fields = '", "'.join(data)
        query = (f'SELECT * FROM {self.__FIELD_TYPE} WHERE field IN '
                 f'("{fields}");')
        return await self._do_select_query(query)

    async def _insert_field_type_data(self, fields: set) -> None:
        """
        Insert fields into the FieldType table.

        :param fields: The fields from any panel in the form of:
                       [<field name>,...].
        :type fields: set
        """
        now = dtime.datetime.utcnow().isoformat()
        data = [(field, now, now) for field in fields]
        query = (f"INSERT INTO {self.__FIELD_TYPE} (field, c_time, m_time) "
                 "VALUES (?, ?, ?)")
        await self._do_insert_query(query, data)

    async def select_from_data_table(self, year: int, month: int,
                                     data: dict) -> list:
        """
        Reads a row or rows from the Data table.

        .. note::

           We convert a Baha'i year and month to a Gregorian year and month.

        :param year: A Baha'i year
        :type year: int
        :param month: A Baha'i month
        :type month: int
        :param data: The data from the any panel  in the form of:
                     {<field name>: <value>,...}.
        :type data: dict
        :return: A list of rows from the Data table.
        :rtype: list
        """
        fields = '", "'.join(data)

        if year and month:
            params = (str(year), str(year+1), month)
            query = (
                'SELECT d.pk, f.field, d.value, d.c_time, d.m_time, '
                'y1.start_date, y2.start_date AS end_date, m.month '
                f'FROM {self.__DATA} d '
                f'JOIN {self.__FIELD_TYPE} f ON f.pk = d.ffk '
                f'AND field IN ("{fields}")'
                f'JOIN {self.__YEAR} y1 ON substr(y1.start_date, 1, 4) = ?'
                f'JOIN {self.__YEAR} y2 ON substr(y2.start_date, 1, 4) = ?'
                f'JOIN {self.__MONTH} m ON m.pk = d.mfk AND month = ?'
                )
        else:
            pass


        return await self._do_select_query(query, params)

    async def _insert_values_in_data_table(self, data: dict) -> None:
        """
        Insert values into the Data table.

        :param data: The data from the any panel  in the form of:
                     {<field name>: <value>,...}.
        :type data: dict
        """
        values = await self.select_from_data_table(data)
        now = dtime.datetime.utcnow().isoformat()

        if not values: # Do insert
            items = await self._select_from_field_type_table(data)
            query = (f"INSERT INTO {self.__DATA} (value, fk, c_time, m_time) "
                     "VALUES (:value, :fk, :c_time, :m_time);")
            fields = []

            for item in items:
                pk, field, rids, c_time, m_time = item
                fields.append({'value': data[field], 'fk': pk,
                               'c_time': now, 'm_time': now})

            await self._do_insert_query(query, fields)
        else: # Do update
            query = (f"UPDATE {self.__DATA} SET value = :value, "
                     "m_time = :m_time WHERE fk = :pk")
            fields = []

            for item in values:
                field, pk = item[:2]
                fields.append({'pk': pk,'value': data[field], 'm_time': now})

            await self._do_update_query(query, fields)

    async def _do_select_query(self, query: str, params: tuple=()) -> list:
        """
        Do the actual query and return the results.

        :param query: The SQL query to do.
        :type query: str
        :return: A list of the data.
        :rtype: list
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute(query, params) as cursor:
                values = await cursor.fetchall()

        return values

    async def _do_insert_query(self, query: str, data: list) -> None:
        """
        Do the insert query.

        :param query: The SQL query to do.
        :type query: str
        :param data: Data to insert into the Data table.
        :type data: list
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            await db.executemany(query, data)
            await db.commit()

    async def _do_update_query(self, query: str, data: list) -> None:
        """
        Do the update query.

        :param query: The SQL query to do.
        :type query: str
        :param data: Data to insert into the Data table.
        :type data: list
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            await db.executemany(query, data)
            await db.commit()

    def _find_fields(self, new: list, old: list) -> set:
        """
        Find the fields to select or insert.

        :param new: The new fields in the form of: [<field name>,...].
        :type new: list or dict (only keys used)
        :param old: The old fields in the form of: [<field name>,...].
        :type old: list
        :return: A list of fields.
        :rtype: list
        """
        new_fields = set(new) # Just get the keys if a dict.
        old_fields = set(old)
        return new_fields - old_fields

    def _make_db_name(self, name: str):
        name = name.replace('(', '').replace(')', '')
        return name.replace(' ', '_').replace(':', '').lower()

    def _scrub_value(self, value, convert_to_utc: bool=False,
                     financial: bool=False):
        if financial:
            value = self.value_to_db(value) if value != '' else '0'
        elif isinstance(value, str):
            value = value.strip()
        elif isinstance(value, wx.DateTime):
            # We convert into an ISO 8601 format for the db.
            if convert_to_utc: value = value.ToUTC()
            value = value.FormatISOCombined()

        return value

    def _convert_date_to_local_time(self, value: str,
                                    convert_from_utc: bool=False
                                    ) -> wx.DateTime:
        """
        """
        dt = wx.DateTime()
        dt.ParseISOCombined(value)

        if convert_from_utc:
            tz = time.localtime().tm_zone
            dt = dt.ToTimezone(dt.TimeZone(tz))

        return dt

    def value_to_db(self, value: str) -> int:
        """
        Convert the text currency value to an integer.

        .. note::

           We store currency values as integers.
           Example $1952.14 in the db is 195214.

        :param value: A currency value from a field.
        :type value: str
        :return: An integer value suttable for putting in the database.
        :rtype: int
        """
        assert isinstance(value, str), ("The argument 'value' can only be a "
                                        f"string found {type(value)}")
        return int(float(value)*100)

    def db_to_value(self, value: str) -> str:
        """
        Convert an integer from the database into a value sutable for
        displaying in a widget.

        :param value: A currency value from the database.
        :type value: int
        :return: A string representation of a currency value.
        :rtype: str
        """
        value = int(value)
        return f"{value/100:.2f}"

    async def _do_insert_query(self, query:str, data:list) -> None:
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            await db.executemany(query, data)
            await db.commit()

    def _find_timezone(self, address: str):
        geolocator = Nominatim(user_agent='nc-bookkeeper')
        location = geolocator.geocode(address)

        if location:
            raw = location.raw
            lat = float(raw['lat'])
            lon = float(raw['lon'])
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lon, lat=lat)
        else:
            address = "Not Known"
            tz = lat = lon = ''
            msg = f"Cannot find the timezone for '{address}'."
            self._mf.statusbar_error = msg

        return tz, lat, lon

    def _get_sunset_datetimes(self, start_year: int, timezone: str) -> list:
        """
        Get the sunset for any timezone.

        :param start_year: The current Gregorian year.
        :type start_year: int
        :param timezone: The timezone for the area in question.
        :type timezone: str
        :return: A list of ISO formatted current and next years.
        :rtype: list
        """
        return [self._get_sunset(self._get_vernal_equinox(year, timezone))
                for year in (start_year, start_year+1)]

    def _get_vernal_equinox(self, year: int, timezone: str) -> dtime.datetime:
        zone = ZoneInfo(timezone)
        # Get the UTC time of the vernal equinox then make it aware.
        # Convert it to local time to get the sun set for the given
        # address then convert it back to UTC time.
        utc_dt = ephem.next_vernal_equinox(str(year)).datetime()
        utc_dt = utc_dt.replace(tzinfo=UTC)
        return utc_dt.astimezone(zone)

    def _get_sunset(self, date: dtime.datetime, utc: bool=True,
                    iso: bool=True) -> dtime.datetime:
        srss = SunriseSunset(date, self.__LAT, self.__LON)
        rise_time, set_time = srss.sun_rise_set
        utc_set_time = set_time.astimezone(UTC) if utc else set_time
        return utc_set_time.isoformat() if iso else utc_set_time

    def _local_to_utc_time(self, dt: dtime.datetime):
        local_tz = ZoneInfo(self.__TIMEZONE)
        local_dt = dt.replace(tzinfo=local_tz)
        return local_dt.astimezone(UTC)

    def _utc_to_local_time(self, dt: dtime.datetime):
        utc_dt = dt.replace(tzinfo=UTC)
        local_tz = ZoneInfo(self.__TIMEZONE)
        return utc_dt.astimezone(local_tz)

    def _convert_bahai_to_gregorian_year(self, year: str) -> int:
        """
        Convert a Baha'i year to a Gregorian year. If a Gregorian year is
        passed in, it will not be changed unless it is below 1000.

        :param year: A Baha'i year.
        :type year: str
        :return: The converted year
        :rtype: int
        """
        start_year = 1843
        year = int(year)
        if year < 1000: year += 1843
        return year

    def _convert_gregorian_to_bahai_year(self, year: str) -> int:
        """
        Convert a Gregorian year to a Baha'i year. If a Baha'i year is
        passed in, it will not be changed unless it is below 1000.

        :param year: A Gregorian year.
        :type year: str
        :return: The converted year
        :rtype: int
        """
        start_year = 1843
        year = int(year)
        if year > 1000: year - 1843
        return year

    def _get_bahai_month_from_gregorian_date(self, today:dtime.date) -> str:
        """
        Get the Baha'i month from the localized gregorian date.

        :param today: A Gergorian date for today.
        :type today: dtime.date
        :return: Baha'i month.
        :rtype: str
        """
        year_gregorian_days = (today-time.date(today.year, 1, 1)).days+1
        b_year = today.year - 1843 if self.LEAP_YEAR(today.year) else 1844
        #days_gregorian_year = 366 if self.LEAP_YEAR(today.year) else 365
        #days_in_bahai_year = 366 if self.LEAP_YEAR(b_year) else 365

        add = 1 if self.LEAP_YEAR(b_year) else 0
        # The magic number 78 is the number of days into the Gregorian year
        # that indicates the start of the Baha'i year. We add 1 if it is a
        # leap year.
        bahai_numerical_month = round((year_gregorian_days - 78 + add) / 19)

        #if bahai_numerical_month > 18:



        return bahai_numerical_month

        #months = self.months

