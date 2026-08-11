# -*- coding: utf-8 -*-
#
# tests/base_database_test.py
#
__docformat__ = "restructuredtext en"

import re
import unittest
import aiosqlite
import wx
import badidatetime

from src.bahai_database import Database
from src.utilities import StoreObjects

from .sample_data import TEST_DATA
from .fixtures import FakeMainFrame, Options

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
        line = ""

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
    # Below are test data needed by some tests.
    _ORG_DATA = {'locality_prefix': 0, 'locale_name': 'New York',
                 'total_membership': '20', 'treasurer': 'Joe Schmo',
                 'start_of_fiscal_year': badidatetime.date(183, 3, 5),
                 'location_city_name': 'New York', 'iana_name': None,
                 'latitude': None, 'longitude': None}
    _ORG_EMPTY = {'locality_prefix': 0, 'locale_name': '',
                  'total_membership': '', 'treasurer': '',
                  'start_of_fiscal_year': badidatetime.date(183, 3, 5),
                  'location_city_name': '', 'iana_name': None,
                  'latitude': None, 'longitude': None}
    _BGT_DATA = {'cash_in_bank': '200000', 'ocs_holdings': '10000',
                 'total_outstanding_bills_previous_year': '000',
                 'total_membership_beginning_of_year': '20',
                 'monetary_contributions': '200000'}
    _BGT_EMPTY = {'cash_in_bank': '', 'ocs_holdings': '',
                  'total_outstanding_bills_previous_year': '',
                  'total_membership_beginning_of_year': '',
                  'monetary_contributions': ''}
    _MTH_DATA = {'month_index': '183-03 Jamál', 'participation': '2',
                 'outstanding_bills': '1000',
                 'end_of_month_cash_on_hand': '000',
                 'total_membership_this_month': '20',
                 'treasurer_this_month': 'Joe Schmo',
                 'locality_prefix_month': 0}
    _MTH_EMPTY = {'month_index': '183-03 Jamál', 'participation': '',
                  'outstanding_bills': '',
                  'end_of_month_cash_on_hand': '',
                  'total_membership_this_month': '',
                  'treasurer_this_month': '',
                  'locality_prefix_month': 0}
    _FY_DATA = {'fiscal_year_choice': 0, 'current_fiscal_year': False,
                'work_on_this_fiscal_year': False, 'audit_complete': False}
    _LDG_DATA = {
        'panel': {'transaction_id': '', 'date': None, 'memo': '',
                  'total_expenses': ''},
        'transaction': {'contribution': False, 'distribution': False,
                        'expense': False, 'other': False},
        'reference': {'ocs': False, 'check': False, 'receipt': False,
                      'deposit': False, 'number': ''},
        'bank': {'deposit': False, 'withdrawal': False, 'amount': '',
                 'balance': ''},
        'coh': {'replenishment': False, 'disbursement': False,
                'amount': '', 'balance': ''},
        'income': {'local_fund': False, 'contributed_expense': False,
                   'other': False, 'amount': '', 'balance': ''},
        'expenses': {'administration': '', 'education': '', 'proclamation': '',
                     'scolarships': '', 'teaching': '',
                     'national_baháí_fund': '',
                     'baháí_chair_for_world_peace_reserved_fund': '',
                     'persian_baháí_media_service_fund_payam_e_doost': '',
                     'house_of_worship_campus_reserves_fund': '',
                     'wilmette_institute_unrestricted_contribution': '',
                     'humanitarian_relief_fund_in_usa': '',
                     'us_baháí_archives_renovation_fund': '',
                     'baháí_election_convention_contributions': '',
                     'bosch_facilities_recovery_fund': '',
                     'institute_properties_resurve_fund': '',
                     'legal_defense_for_the_refugees_in_turkey': '',
                     'international_baháí_fund': '',
                     'baháí_development_fund': '',
                     'international_endowment_fund': '',
                     'continental_baháí_fund': '',
                     'national_house_of_worship_canada': '',
                     'shrine_of_abdul_bahá': '',
                     'humanitarian_relief_fund_world_center': '',
                     'persian_relief_fund_world_center': '',
                     'international_temples_fund': '',
                     'asian_continental_board': '',
                     'us_deputization_fund_international_pioneering': '',
                     'regional_baháí_council': '', 'deputization_fund': '',
                     'regional_facilities_fund': '',
                     'area_teaching_committee': ''}
        }

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls._db = Database()
        StoreObjects().set_object(cls._db.__class__.__name__, cls._db)
        cls._db.testing = True
        cls._db.create_dirs()
        cls.app = wx.GetApp()

        if cls.app is None:
            cls.app = wx.App(False)

        cls.frame = FakeMainFrame(options=Options())

    @classmethod
    def tearDownClass(cls):
        if wx.GetApp():
            wx.GetApp().Destroy()

    @property
    def db(self):
        return self._db

    async def insert_data(self):
        rowcount = 0

        for table, data in TEST_DATA.items():
            rowcount += await self.insert_table(table, data)

        return rowcount

    async def insert_table(self, table_name: str, data: list) -> None:
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
            case self.db._T_MONTH:
                rowcount = await self.db.insert_into_month_table(data)
            case self.db._T_FIELD_TYPE:
                rowcount = await self.db.insert_into_field_type_table(data)
            case self.db._T_DATA:
                rowcount = await self.db.insert_all_into_config_data_table(
                    data)
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

    async def insert_fiscal_year(self) -> int:
        """
        Insert fiscal year data in the DB.
        """
        rowcount = 0

        if not self.db.cache.has_fiscal_cache_data:
            fy_data = {'data': TEST_DATA[self.db._T_FISCAL_YEAR]}
            rowcount = await self.db.cache.insert(self.db._T_FISCAL_YEAR,
                                                  fy_data)
            self.assertEqual(len(fy_data['data']), rowcount)

        return rowcount

    async def insert_field_data(self, data: dict) -> int:
        """
        Insert field data in the DB.
        """
        return await self.db.cache.insert(self.db._T_FIELD_TYPE,
                                          {'data': list(data)})

    async def insert_months(self) -> int:
        """
        Insert months data in the DB.
        """
        data = {'data': TEST_DATA[self.db._T_MONTH]}
        rowcount = await self.db.cache.insert(self.db._T_MONTH, data)
        self.assertEqual(len(data['data']), rowcount)
        return rowcount
