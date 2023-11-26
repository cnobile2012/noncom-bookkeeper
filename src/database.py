# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

from .config import Settings


class Database(Settings):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # [{pk: <value>, field: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._field_types = []
        # [{pk: <value>, report: <value>, rid: <value>, desc: <value>,
        #   c_time: <value>, m_time: <value>}, ...]
        self._report_types = []

    @property
    def has_org_info(self) -> bool:
        """
        Check that the db has the Organization Information.
        """
        ret = False
        # For now return false.
        return ret

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


    def read_from_data_table(self, val0, t1=None, t2=None):
        """
        Reads a row or rows from the Data table.

        :param val0: This can be a pk, value, fft_fk, or a c_time or
                     m_time string.
        :type val0: str or int
        :param t1: Start datetime range.
        :type t1: datetime
        :param t2: End datetime range.
        :type 21: datetime
        :return: A list of rows from the Data table.
        :rtype: list
        """


