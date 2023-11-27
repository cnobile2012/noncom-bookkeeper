# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

import sqlite3

from .config import BaseSystemData


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
        self._con = None
        self._cur = None

    def connect_db(self):
        """
        Connect to the db and create a cursor.
        """
        self._con = sqlite3.connect(self.user_data_fullpath)
        self._cur = self._con.cursor()

    @property
    def has_org_info(self) -> bool:
        """
        Check that the db has the Organization Information.
        """
        ret = False

        row_names = self.field_names('organization')
        #print(row_names)

        # For now return false.
        return ret

    @property
    def has_schema(self):
        assert self._cur, "Error, the curser needs to be created first."
        result = self._cur.execute("SELECT name FROM sqlite_master")
        table_names = [
            table[0] for table in result.fetchmany(size=len(self._SCHEMA) + 4)]
        check = len(table_names) == len(self._SCHEMA)

        if not check:
            names = [table[0] for table in self._SCHEMA]
            msg = ("Database table count is wrong it should be "
                   f"'{names}' found '{table_names}'")
            self._log.error(msg)
            #self.parent.statusbar_error = msg
            # *** TODO *** This needs to be shown on the screen if detected.

        #print(table_names)
        return check

    def create_db(self):
        """
        Create the database based on the fields currently defined.
        """
        assert self._cur, "Error, the curser needs to be created first."

        if not self.has_schema:

            for params in self._SCHEMA:
                table = params[0]
                fields = ', '.join([field for field in params[1:]])
                query = f"CREATE TABLE {table}({fields})"
                self._cur.execute(query)

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

