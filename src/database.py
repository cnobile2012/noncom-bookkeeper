# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

import aiosqlite

from .config import BaseSystemData
from .utilities import StoreObjects


class Database(BaseSystemData):
    _SCHEMA = (
        ('FieldType', 'pk', 'field', 'rids', 'desc' , 'c_time', 'm_time'),
        ('ReportType', 'pk', 'report', 'rid', 'desc' , 'c_time', 'm_time'),
        ('Data', 'pk', 'value', 'fk', 'c_time' , 'm_time')
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # [{pk: <value>, field: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._field_types = []
        # [{pk: <value>, report: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._report_types = []
        self._mf = StoreObjects().get_object('MainFrame')

    async def start(self):
        await self.create_db()

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
        row_names = "', '".join(self.field_names('organization'))
        query = f"SELECT field FROM FieldType WHERE field IN ('{row_names}');"

        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute("SELECT name FROM sqlite_master") as cursor:
                values = await cursor.fetchall()

        print(values)

        oi_panel = self._mf.panels['organization']
        children = list(oi_panel.GetChildren())
        child_sets = [children[i:i+2] for i in range(0, len(children), 2)]

        for c_set in child_sets:
            name0 = c_set[0].__class__.__name__
            name1 = c_set[1].__class__.__name__

            if name0 == 'RadioBox':
                print(c_set[0].GetSelection()) # Returns an integer.
            elif name0 == 'StaticText':
                if name1 in ('TextCtrl', 'DatePickerCtrl'):
                    print(c_set[1].GetValue())

        #    query = f"SELECT "

        # For now return false.
        return ret

    @property
    async def has_schema(self):
        query = "SELECT name FROM sqlite_master"

        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute(query) as cursor:
                table_names = [table[0] for table in await cursor.fetchall()]
                check = len(table_names) == len(self._SCHEMA)

                if not check:
                    names = [table[0] for table in self._SCHEMA]
                    msg = ("Database table count is wrong it should be "
                           f"'{names}' found '{table_names}'")
                    self._log.error(msg)
                    #self.parent.statusbar_error = msg
                    # *** TODO *** This needs to be shown on the screen if
                    #              detected.

        return check

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

