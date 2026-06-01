# -*- coding: utf-8 -*-
#
# tests/base_database_test.py
#

import os
import re
import random
import string
import unittest
import aiosqlite

from unittest.mock import patch

from src.bahai_database import Database
from src.prep_and_cache import Cache

from .test_data import ORG_FIELDS, BDG_FIELDS, TEST_DATA

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
        cls.cache = Cache(cls._db)

    @property
    def db(self):
        return self._db

    async def insert_data(self):
        self.cache._flush_cache()

        for table, data in TEST_DATA.items():
            await self.cache.insert_all(table, data)



    # async def does_table_exist(self, table: str) -> bool:
    #     """
    #     Do an SQL query to see if a table exists.

    #     :param str table: The name of the table.
    #     :returns: Returns 'True' if a table exists and 'False' if it does
    #                       not exist.
    #     :rtype: bool
    #     """
    #     query = ("SELECT name FROM sqlite_master WHERE type = 'table' "
    #              "AND name = ?;")

    #     async with aiosqlite.connect(self.bd.db_fullpath) as db:
    #         cursor = await db.execute(query, (table,))
    #         return await cursor.fetchone() != ()

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
