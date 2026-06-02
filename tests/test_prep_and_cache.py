# -*- coding: utf-8 -*-
#
# test/test_prep_and_cache.py
#
__docformat__ = "restructuredtext en"

import unittest

from src.bahai_database import Database
from src.prep_and_cache import DataPreperation

from . import check_flag, log
from .base_database_test import BaseAsyncTests


class TestDataPreperation(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)


class TestCache(BaseAsyncTests):
    _YEAR = 183

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)

    async def asyncSetUp(self):
        await self.db.create_db()
        self.cache.year = self._YEAR
        await self.insert_data()
        await self.cache.load()

    async def asyncTearDown(self):
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    async def test_load_no_data(self):
        """
        Test that the load method loads no `organization`, `fiscal`,
        and `monthly` data with an empty DB.
        """
        await self.truncate_all_tables()
        expected = False
        msg = "Expected {}, found {}"
        has_flds = self.cache.has_fields_data
        has_orgz = self.cache.has_organization_cache_data
        has_bdgt = self.cache.has_budget_cache_data
        has_fscl = self.cache.has_fiscal_cache_data
        has_mnth = self.cache.has_month_cache_data
        has_mnly = self.cache.has_monthly_cache_data
        self.assertFalse(has_flds, msg.format(expected, has_flds))
        self.assertFalse(has_orgz, msg.format(expected, has_orgz))
        self.assertFalse(has_bdgt, msg.format(expected, has_bdgt))
        self.assertFalse(has_fscl, msg.format(expected, has_fscl))
        self.assertFalse(has_mnth, msg.format(expected, has_mnth))
        self.assertFalse(has_mnly, msg.format(expected, has_mnly))

    #@unittest.skip("Temporarily skipped")
    def test_load_with_data(self):
        """
        Test that the load method loads all the `organization`, `fiscal`,
        and `monthly` data.
        """
        msg = "Expected {}, found {}"
        expected = True
        has_flds = self.cache.has_fields_data
        has_orgz = self.cache.has_organization_cache_data
        has_bdgt = self.cache.has_budget_cache_data
        has_fscl = self.cache.has_fiscal_cache_data
        has_mnth = self.cache.has_month_cache_data
        has_mnly = self.cache.has_monthly_cache_data
        self.assertTrue(has_flds, msg.format(expected, has_flds))
        self.assertTrue(has_orgz, msg.format(expected, has_orgz))
        self.assertTrue(has_bdgt, msg.format(expected, has_bdgt))
        self.assertTrue(has_fscl, msg.format(expected, has_fscl))
        self.assertTrue(has_mnth, msg.format(expected, has_mnth))
        #self.assertTrue(has_mnly, msg.format(expected, has_mnly))

    #@unittest.skip("Temporarily skipped")
    def test_fields(self):
        """
        Test that the fields property returns just the field names.
        """
        msg = "Field {} not in {}"
        result = self.cache.fields

        for field in self.cache.ORG_FIELDS:
            self.assertIn(field, result, msg.format(field, result))

    #@unittest.skip("Temporarily skipped")
    def test_get_bgt_fields(self):
        """
        Test that the get_bgt_fields property teturns just the budget fields.
        """
        msg = "Field {} found in {}"
        result = self.cache.get_bgt_fields

        for field in self.cache.ORG_FIELDS:
            self.assertNotIn(field, result, msg.format(field, result))

    #@unittest.skip("Temporarily skipped")
    def test_get(self):
        """
        Test that the get method returns the correct data depending on the
        DB table.
        """
        err_msg0 = "Invalid `r_type`, found {}."
        data = (
            (183, self.db._T_DATA, 'organization', True, 'iana_name'),
            (183, self.db._T_DATA, 'budget', True, 'cash_in_bank'),
            (183, self.db._T_FISCAL_YEAR, None, True, 184),
            (183, self.db._T_MONTH, None, True, 'Ayyám-i-Há'),
            #(183, self.db._T_MONTHLY, None, True, 'Joe Shmo'),
            (183, self.db._T_DATA, 'invalid', False,
             err_msg0.format('invalid')),
            )
        msg = "Expected {}, found {}"

        for year, table_name, record_type, valid, data_to_find in data:
            self.cache.year = year

            if valid:
                result = self.cache.get(table_name, record_type)

                match table_name:
                    case self.db._T_DATA:
                        index = 1
                    case self.db._T_FISCAL_YEAR:
                        index = 1  # year
                    case self.db._T_MONTH:
                        index = 1  # month
                    case self.db._T_MONTHLY:
                        index = 5

                test_fields = [item[index] for item in result]
                self.assertIn(data_to_find, test_fields, msg.format(
                    data_to_find, test_fields))
            else:
                with self.assertRaises(AssertionError) as cm:
                    self.cache.get(table_name, record_type)

                expect = str(cm.exception)
                self.assertEqual(expect, data_to_find)
