# -*- coding: utf-8 -*-
#
# src/base_database.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import aiosqlite

from .utilities import StoreObjects

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


class BaseDatabase:
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
        self._mf = StoreObjects().get_object('MainFrame')
        self._org_data = None

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

    @property
    def has_org_info_data(self) -> bool:
        """
        Check that the db has the Organization Information.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('organization')

    @property
    def has_budget_data(self) -> bool:
        """
        Check that the db has the Yearly Budget data.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('budget')

    @property
    def has_month_data(self) -> bool:
        """
        Check that the db has the Organization Information.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('month')

    def _check_panels_for_entries(self, name: str) -> bool:
        """
        Check that the given panel name has entries.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        panel = self._mf.panels[name]
        data = self._collect_panel_values(panel)
        return all([item not in self._EMPTY_FIELDS for item in data.values()])

    def _collect_panel_values(self, panel: wx.Panel,
                              convert_to_utc: bool=False) -> dict:
        """
        Collects the data from the panel's widgets.

        :param wx.Panel panel: The panel to collect data from.
        :param convert_to_utc: True if wx.DateTime field's should be
                               converted to UTC and False if they are not
                               to be converted (default is False).
        :returns: A dictonary of db field names and values.
        :rtype: dict
        """
        data = {}

        for c_set in self._find_children(panel):
            name0 = c_set[0].__class__.__name__
            name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
            field_name = self._make_field_name(c_set[0].GetLabelText())

            if name0 == 'RadioBox':
                data[field_name] = self._scrub_value(c_set[0].GetSelection())
            elif name0 == 'ComboBox':
                data[field_name] = c_set[0].GetSelection()
            elif name0 == 'StaticText':
                value = c_set[1].GetValue()

                if name1 == 'TextCtrl':
                    financial = True if c_set[1].financial else False
                    data[field_name] = self._scrub_value(value,
                                                         financial=financial)
                elif name1 == 'DatePickerCtrl':
                    data[field_name] = self._scrub_value(value, convert_to_utc)

        return data

    def populate_panel_values(self, name: str, panel: wx.Panel,
                              values: list) -> None:
        """
        Poplulate the named panel with the database values.

        :param str name: The name of the panel.
        :param list values: The database values to be used to poplulate the
                            panel.
        """
        if (data := {item[1]: item[2:] for item in values}):
            for c_set in self._find_children(panel):
                name0 = c_set[0].__class__.__name__
                name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
                field_name = self._make_field_name(c_set[0].GetLabelText())
                value = data[field_name][0]

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
                                and field_name == 'total_membership_month'):
                                value = self._org_data['total_membership']
                            elif not value and field_name == 'treasurer_month':
                                value = self._org_data['treasurer']
                        c_set[1].SetValue(value)
                    elif name1 == 'DatePickerCtrl':
                        year, month, day = self._convert_date_to_yymmdd(value)
                        dt = wx.DateTime(year=year, month=month, day=day)
                        c_set[1].SetValue(dt)

    def _find_children(self, panel: wx.Panel) -> list:
        """
        Find the children in the panel that hold data.

        :param wx.Panel panel: The panel to collect data from.
        :returns: A list of child sets.
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
        Insert data into the `month` table.
        """
        items = await self.select_from_month_table()
        months = self._ordered_month()

        if not items:  # Insert all months and their order.
            await self.insert_into_month_table(months)
        else:  # Insert only months and their order if not in the database.
            # We only need month and order.
            data = [item[1:3] for item in items]

            for idx, item in enumerate(data):
                if item not in months:
                    await self.insert_into_month_table(item)

    async def _insert_update_fiscal_year_table(self, field_data: tuple
                                               ) -> None:
        """
        Insert or update `fiscal_year` table.

        :param tuple field_data: This is the year, month, day, and current
                                 values (year, month, day, current).
        """
        year = field_data[0]
        values = await self.select_from_fiscal_year_table(year=year)

        if values:
            await self.update_fiscal_year_table(year, field_data[3])  # current
        else:
            await self.insert_into_fiscal_year_table(field_data)

    async def _insert_update_data_table(self, year: int, month: int,
                                        data: dict) -> None:
        """
        Insert or update `data` table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>,...}.
        """
        values = await self.select_from_data_table(data, year, month)
        print('POOP0: data\n', data)
        print('POOP1: values\n', values)

        if not values:  # Do insert
            await self.insert_into_data_table(year, month, data)
        else:
            items = dict([(pk, (field, value))
                          for pk, field, value, y1, y2, c, m in values])
            insert_data = {}
            update_data = {}

            for pk, (field, value) in items.items():
                if field in data:  # Field value already exists.
                    update_data[field] = (pk, data[field])
                else:  # Field value does not exist.
                    insert_data[field] = data[field]

            if insert_data:  # Do insert
                await self.insert_into_data_table(year, month, insert_data)

            if update_data:  # Do update
                await self.update_data_table(year, month, update_data)

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
            await db.executemany(query, data)
            await db.commit()

    async def _do_update_query(self, query: str, data: list) -> None:
        """
        Do the update query.

        :param str query: The SQL query to do.
        :param list data: Data to update into the Data table.
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            await db.executemany(query, data)
            await db.commit()

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

    def _make_field_name(self, name: str):
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

    def value_to_db(self, value: str) -> int:
        """
        Convert the text currency value to an integer.

        .. note::

           We store currency values as integers.
           Example $1952.14 in the db is 195214.

        :param str value: A currency value from a field.
        :returns: An integer value suttable for putting in the database.
        :rtype: int
        """
        assert isinstance(value, str), ("The argument 'value' can only be a "
                                        f"string found {type(value)}")
        return int(float(value)*100)

    def db_to_value(self, value: str) -> str:
        """
        Convert an integer from the database into a value sutable for
        displaying in a widget.

        :param int value: A currency value from the database.
        :returns: A string representation of a currency value.
        :rtype: str
        """
        value = int(value)
        return f"{value/100:.2f}"

    def _find_timezone(self, address: str):
        """
        Find the IANA timezone name, latitude, and longitude.

        :param str address: The address, City, town used to find the required
                            information.
        :returns: The IANA timezone name, latitude, and longitude.
        :rtype: tuple
        """
        geolocator = Nominatim(user_agent='nc-bookkeeper')
        location = geolocator.geocode(address)

        if location:
            raw = location.raw
            lat = float(raw['lat'])
            lon = float(raw['lon'])
            tf = TimezoneFinder()
            iana = tf.timezone_at(lng=lon, lat=lat)
        else:
            address = "Not Known"
            iana = lat = lon = ''
            msg = f"Cannot find the timezone for '{address}'."
            self._mf.statusbar_error = msg

        return iana, lat, lon

    def _update_organization_constants(self, values: list) -> None:
        """
        This method sets the organization constants that are used throughout
        the application without having to do a select on the DB everytime.

        .. note::

           It is used in both the `populate_panels` and `save_to_database`
           methods.
        """
        self._org_data = {value[0]: value[2] for value in values}
