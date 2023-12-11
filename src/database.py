# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

import aiosqlite
import time
from datetime import datetime
import wx

from .config import BaseSystemData
from .utilities import StoreObjects


class Database(BaseSystemData):
    __FIELD_TYPE = 'field_type'
    __REPORT_TYPE = 'report_type'
    __DATA = 'data'
    _SCHEMA = (
        (__FIELD_TYPE, 'pk INTEGER NOT NULL PRIMARY KEY',
         'field TEXT UNIQUE NOT NULL',
         'rids INTEGER DEFAULT 0 NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__REPORT_TYPE, 'pk INTEGER NOT NULL PRIMARY KEY',
         'report TEXT UNIQUE NOT NULL',
         'rid INTEGER UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__DATA, 'pk INTEGER NOT NULL PRIMARY KEY',
         'value NOT NULL',
         'fk INTEGER NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL',
         f'FOREIGN KEY (fk) REFERENCES {__FIELD_TYPE} (pk)')
        )
    _TABLES = [table[0] for table in  _SCHEMA]
    _TABLES.sort()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # [{pk: <value>, field: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._field_types = []
        # [{pk: <value>, report: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._report_types = []
        self._mf = StoreObjects().get_object('MainFrame')

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
            values = await self.select_from_data_table(data)
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
            #self.parent.statusbar_error = msg
            # *** TODO *** This needs to be shown on the screen if
            #              detected.

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

    def _check_panels_for_entries(self, name:str) -> bool:
        """
        Check that the given panel name has entries.

        :return: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        panel = self._mf.panels[name]
        data = self._collect_panel_values(panel)
        return all([item != '' for item in data.values()])

    async def save_to_database(self, panel:wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param panel: Any of the panels that has collected data.
        :type panel: wx.Panel
        """
        data = self._collect_panel_values(panel)
        await self._insert_values_in_data_table(data)
        panel.dirty = False

    def _collect_panel_values(self, panel:wx.Panel,
                             convert_to_utc:bool=False) -> dict:
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
                if name1 == 'TextCtrl':
                    data[db_name] = self._scrub_value(c_set[1].GetValue())
                elif name1 == 'DatePickerCtrl':
                    data[db_name] = self._scrub_value(c_set[1].GetValue(),
                                                      convert_to_utc)

        return data

    def populate_panel_values(self, name:str, panel:wx.Panel,
                              values:list) -> None:
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
                        c_set[1].SetValue(value)
                    elif name1 == 'DatePickerCtrl':
                        c_set[1].SetValue(
                            self._convert_date_to_local_time(value))

    def _find_children(self, panel:wx.Panel) -> list:
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

            if name == 'StaticLine': continue
            elif name == 'StaticText':
                font = child.GetFont()
                ps = font.GetPointSize()
                w = font.GetWeight()
                if ps == 12 and w == wx.FONTWEIGHT_BOLD: continue
            elif name == 'ComboBox':
                add = True

            children.append(child)
            if add: children.append(None)

        return [children[i:i+2] for i in range(0, len(children), 2)]

    async def _add_fields_to_field_type_table(self, data:dict) -> None:
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

    async def _select_from_field_type_table(self, data:dict) -> list:
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

    async def _insert_field_type_data(self, fields:set) -> None:
        """
        Insert fields into the FieldType table.

        :param fields: The fields from any panel in the form of:
                       [<field name>,...].
        :type fields: set
        """
        now = datetime.utcnow().isoformat()
        data = [(field, now, now) for field in fields]
        query = (f"INSERT INTO {self.__FIELD_TYPE} (field, c_time, m_time) "
                 "VALUES (?, ?, ?)")
        await self._do_insert_query(query, data)

    async def select_from_data_table(self, data:dict) -> list:
        """
        Reads a row or rows from the Data table.

        :param data: The data from the any panel  in the form of:
                     {<field name>: <value>,...}.
        :type data: dict
        :return: A list of rows from the Data table.
        :rtype: list
        """
        fields = '", "'.join(data)
        query = (f'SELECT ft.field, ft.pk, d.value, d.c_time, d.m_time '
                 f'FROM {self.__DATA} d JOIN ('
                 f'SELECT pk, field FROM {self.__FIELD_TYPE}) ft '
                 f'ON ft.pk = d.fk AND field IN ("{fields}");')
        return await self._do_select_query(query)

    async def _insert_values_in_data_table(self, data:dict) -> None:
        """
        Insert values into the Data table.

        :param data: The data from the any panel  in the form of:
                     {<field name>: <value>,...}.
        :type data: dict
        """
        values = await self.select_from_data_table(data)

        if not values: # Do insert
            items = await self._select_from_field_type_table(data)
            now = datetime.utcnow().isoformat()
            query = (f"INSERT INTO {self.__DATA} (value, fk, c_time, m_time) "
                     "VALUES (:value, :fk, :c_time, :m_time);")
            fields = []

            for item in items:
                pk, field, rids, c_time, m_time = item
                fields.append({'value': data[field], 'fk': pk,
                               'c_time': now, 'm_time': now})

            await self._do_insert_query(query, fields)
        else: # Do update
            now = datetime.utcnow().isoformat()
            query = (f"UPDATE {self.__DATA} SET value = :value, "
                     "m_time = :m_time WHERE fk = :pk")
            fields = []

            for item in values:
                field, pk = item[:2]
                fields.append({'pk': pk,'value': data[field], 'm_time': now})

            await self._do_update_query(query, fields)

    async def _do_select_query(self, query:str) -> list:
        """
        Do the actual query and return the results.

        :param query: The SQL query to do.
        :type query: str
        :return: A list of the data.
        :rtype: list
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute(query) as cursor:
                values = await cursor.fetchall()

        return values

    async def _do_insert_query(self, query:str, data:list) -> None:
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

    async def _do_update_query(self, query:str, data:list) -> None:
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

    def _find_fields(self, new:list, old:list) -> set:
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

    def _make_db_name(self, name):
        name = name.replace('(', '').replace(')', '')
        return name.replace(' ', '_').replace(':', '').lower()

    def _scrub_value(self, value, convert_to_utc=False):
        if isinstance(value, str):
            value = value.strip()
        elif isinstance(value, wx.DateTime):
            # We convert into an ISO 8601 format for the db.
            if convert_to_utc: value = value.ToUTC()
            value = value.FormatISOCombined()

        return value

    def _convert_date_to_local_time(self, value:str,
                                    convert_from_utc=False) -> wx.DateTime:
        """
        """
        dt = wx.DateTime()
        dt.ParseISOCombined(value)

        if convert_from_utc:
            tz = time.localtime().tm_zone
            dt = dt.ToTimezone(dt.TimeZone(tz))

        return dt

    def value_to_db(self, value:str) -> int:
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

    def db_to_value(self, value:int) -> str:
        """
        Convert an integer from the database into a value sutable for
        displaying in a widget.

        :param value: A currency value from the database.
        :type value: int
        :return: A string representation of a currency value.
        :rtype: str
        """
        assert isinstance(value, int), ("The argument 'value' can only be an "
                                        f"integer found {type(value)}")
        return f"{value/100:.2f}"
