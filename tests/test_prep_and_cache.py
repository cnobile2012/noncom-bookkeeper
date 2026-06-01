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
        self._cache = None
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    async def test_load_no_data(self):
        """
        Test that the load method loads no `organization`, `fiscal`,
        and `monthly` data with an empty DB.
        """
        await self.truncate_all_tables()
        year = 183
        expected = False
        msg = "Expected {}, found {}"
        await self.cache.load()
        has_orgz = self.cache.has_organization_cache_data
        has_fscl = self.cache.has_fiscal_cache_data
        has_mnly = self.cache.has_monthly_cache_data
        self.assertFalse(has_orgz, msg.format(expected, has_orgz))
        self.assertFalse(has_fscl, msg.format(expected, has_fscl))
        self.assertFalse(has_mnly, msg.format(expected, has_mnly))

    #@unittest.skip("Temporarily skipped")
    async def test_load_with_data(self):
        """
        Test that the load method loads all the `organization`, `fiscal`,
        and `monthly` data.
        """
        pass
