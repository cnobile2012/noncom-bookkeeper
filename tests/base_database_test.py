# -*- coding: utf-8 -*-
#
# tests/base_database_test.py
#

import re
import unittest
import aiosqlite

from src.bahai_database import Database

from .test_data import TEST_DATA

__all__ = ('BaseAsyncTests',)


class BaseTests:
    _RE_FIRST_LINE = r'^.*{}.*$'

    def read_text_file(self, fullpath: str) -> str:
        with open(fullpath) as f:
            return f.read()

    def _find_text_span(self, data_str: str, start: str, num_lines: int):
        """
        Finds text in a file. i.e. log files, but could be any file.

        :param str data_str: A string of the file contents.
        :param str start: A starting string, usually put in by the test.
        :param int num_lines: The number of line in `data_str` to include in
                              the sample. This includes the start string.
        :returns: A list of lines from the target file.
        :rtype: list
        """
        out = []
        first_line = self._RE_FIRST_LINE.format(re.escape(start))
        sre = re.search(first_line, data_str, re.MULTILINE)

        if sre:
            file_list = [line for line in data_str.split('\n')]
            count = 0

            for line in file_list:
                if count > 0 and count < num_lines:
                    out.append(line)
                    count += 1

                if sre.group() in line:
                    count += 1
                    out.append(line)

        return out

    def find_text(self, data_str: str, start: str, num_lines: int, text: str
                  ) -> str:
        """
        Finds the line in the file that contains the queried text or
        returns an empty string.

        :param str data_str: A string of the file contents.
        :param str start: A starting string, usually put in by the test.
        :param int num_lines: The number of line in `data_str` to include in
                              the sample. This includes the start string.
        :param str text: The text that is being queried.
        :returns: The line in the file that contains the queried text.
        :rtype: str
        """
        for line in self._find_text_span(data_str, start, num_lines):
            if text in line:
                break

        return line if line else ""


class BaseAsyncTests(BaseTests, unittest.IsolatedAsyncioTestCase):
    """
    The base class for all test classes that will be running database access
    code.

    The one caveat is that self.bd = BaseDatabase() must be defined in the
    async def asyncSetUp(self): methods.
    """

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls._db = Database()
        cls._db.testing = True
        cls._db.create_dirs()

    @property
    def db(self):
        return self._db

    async def insert_data(self):
        rowcount = 0

        for table, data in TEST_DATA.items():
            rowcount += await self.insert_all(table, data)

        return rowcount

    async def insert_all(self, table_name: str, data: list) -> None:
        """
        Insert all date in a table.

        :param str table_name: The DB table to insert into.
        :param dict data: The data to insert.
        :returns: The insertion rowcount.
        :rtype: int
        """
        match table_name:
            case self.db._T_FISCAL_YEAR:
                rowcount = await self.db.insert_into_fiscal_year_table(data)
            case self.db._T_FIELD_TYPE:
                rowcount = await self.db.insert_into_field_type_table(data)
            case self.db._T_DATA:
                rowcount = await self.db.insert_all_into_config_data_table(
                    data)
            case self.db._T_MONTH:
                rowcount = await self.db.insert_into_month_table(data)
            case self.db._T_MONTHLY:
                rowcount = await self.db.insert_all_into_monthly_table(data)
            case _:
                rowcount = 0

        assert len(data) == rowcount, (
            f"Invalid inserted {rowcount}, found {len(data)} rows for "
            f"table {table_name}.")

        return rowcount

    async def truncate_all_tables(self):
        """
        Truncate all tables.
        """
        query0 = ("SELECT name FROM sqlite_master "
                  "WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        query1 = ("SELECT name FROM sqlite_master "
                  "WHERE name = 'sqlite_sequence';")

        async with aiosqlite.connect(self._db.user_data_fullpath) as db:
            async with db.execute(query0) as cursor:
                for table in [row[0] for row in await cursor.fetchall()]:
                    await cursor.execute(f"DELETE FROM '{table}';")

                # Reset auto-increment counters if they exist.
                cursor = await db.execute(query1)

                if await cursor.fetchone():
                    await cursor.execute("DELETE FROM sqlite_sequence;")

                await db.commit()
