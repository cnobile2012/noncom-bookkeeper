# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

import aiosqlite
from datetime import datetime
import wx

from .config import BaseSystemData
from .utilities import StoreObjects


class Database(BaseSystemData):
    _SCHEMA = (
        ('FieldType', 'pk', 'field', 'rids', 'desc' , 'c_time', 'm_time'),
        ('ReportType', 'pk', 'report', 'rid', 'desc' , 'c_time', 'm_time'),
        ('Data', 'pk', 'value', 'fk', 'c_time' , 'm_time')
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
                    query = f"CREATE TABLE {table}({fields})"
                    await db.execute(query)
                    await db.commit()

            #cur.executemany("INSERT INTO lang VALUES(:name, :year)", data)

    @property
    async def has_schema(self) -> bool:
        """
        Checks that the schema has been created.

        :return: True if the schema has been created and False if it has not
                 been created.
        :rtype: bool
        """
        query = "SELECT name FROM sqlite_master"

        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute(query) as cursor:
                table_names = [table[0] for table in await cursor.fetchall()]
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
    async def has_org_info(self) -> bool:
        """
        Check that the db has the Organization Information.

        The db stores data for the 'selection' in the RadioBox, 'value'
        for the 4th, 6th, and 8th TextCtrl, 'value' of the DatePickerCtrl.

        :return: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        ret = False
        panel = self._mf.panels['organization']
        data = self.collect_panel_values(panel)
        #print(f"POOP--data {data}")

        # Check that the field names are in the FieldType table.
        #rows = "', '".join(self.panel_field_names('organization'))
        rows = "', '".join(list(data.keys()))
        query = f"SELECT field FROM FieldType WHERE field IN ('{rows}');"

        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute(query) as cursor:
                values = await cursor.fetchall()
                print(values)



        # Check that we have data for the fields in Data table.
        #    query = f"SELECT "

        for field in data:
            pass

        # For now return false.
        return ret

    def save_to_database(self, panel:wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param panel: Any of the panels that has collected data.
        :type panel: wx.Panel
        """
        data = self.collect_panel_values(panel)
        print(data)



    def collect_panel_values(self, panel:wx.Panel,
                             convert_to_utc:bool=False) -> dict:
        """
        Collects the data from the panel's widgets.

        *** TODO *** This method will not work for the Budget and Monthly panel.

        :param panel: The panel to collect data from.
        :type panel: wx.Panel
        :param convert_to_utc: True if wx.DateTime field's should be
                               converted to UTC and False if they are not
                               to be converted (default is False).
        :return: A dictonary of field names and values.
        :rtype: dict
        """
        data = {}
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

        print(children)
        child_sets = [children[i:i+2] for i in range(0, len(children), 2)]

        for c_set in child_sets:
            name0 = c_set[0].__class__.__name__
            name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]

            if name0 == 'RadioBox':
                db_name = self._make_db_name(c_set[0].GetLabelText())
                # Returns an integer.
                data[db_name] = self._scrub_value(c_set[0].GetSelection())
            elif name0 == 'ComboBox':
                db_name = self._make_db_name(c_set[0].GetLabelText())
                data[db_name] = c_set[0].GetSelection()
            elif name0 == 'StaticText':
                db_name = self._make_db_name(c_set[0].GetLabelText())

                if name1 == 'TextCtrl':
                    data[db_name] = self._scrub_value(c_set[1].GetValue())
                elif name1 == 'DatePickerCtrl':
                    data[db_name] = self._scrub_value(c_set[1].GetValue(),
                                                      convert_to_utc)

        return data

    def add_to_field_type_table(self, fields:list) -> None:
        """
        Add given fields to the FieldType table.

        :param fields: The field names to add.
        :type fields: list
        """


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

    def read_field_type_table(self):
        """
        Reads the FieldType table and loads it into memory.
        """


    def read_report_type_table(self):
        """
        Reads the ReportType table and loads it into memory.
        """


    def read_from_data_table(self, val0, v1=None, v2=None):
        """
        Reads a row or rows from the Data table.

        :param val0: This can be a pk, value, or a 'fk' or 'c_time' or
                     'm_time' string.
        :type val0: str or int
        :param v1: Start datetime range or fk (from the FieldType table).
        :type v1: datetime
        :param v2: End datetime range.
        :type v2: datetime
        :return: A list of rows from the Data table.
        :rtype: list
        """
        query = {}

        if val0 == 'fk': # Foreign Key
            assert v1, f"Invalid 'v1: {v1} value."
            query['fk'] = v1


        elif val0 == 'c_time': # c_time
            assert v1 and v2, f"Invalid 'v1: {v1}' or 'v2: {v2}' values."


        elif val0 == 'm_time': # m_time
            assert v1 and v2, f"Invalid 'v1: {v1}' or 'v2: {v2}' values."


        elif isinstance(val0, int): # value
            pass


        else: # Primary Key
            pass

    def _make_db_name(self, name):
        return name.replace(' ', '_').replace(':', '').lower()

    def _scrub_value(self, value, convert_to_utc=False):
        if isinstance(value, str):
            value = value.strip()
        #elif isinstance(value, int):
        #    pass
        elif isinstance(value, wx.DateTime):
            # We convert into an ISO format for the db.
            if convert_to_utc: value = value.ToUTC()
            value = value.FormatISOCombined()

        return value
