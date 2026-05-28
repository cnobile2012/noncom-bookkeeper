# -*- coding: utf-8 -*-
#
# test/test_prep_and_cache.py
#
__docformat__ = "restructuredtext en"

import unittest

from src.bahai_database import Database
from src.prep_and_cache import DataPreperation, Cache

from .base_database_test import BaseAsyncTests


class TestDataPreperation(BaseAsyncTests):

    def __init__(self, name):
        super().__init__(name)


class TestCache(BaseAsyncTests):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        self.setup_db()
        self._cache = Cache(self._db)

    @unittest.skip("Temporarily skipped")
    def test_load(self):
        """
        Test that the load method loads the `organization`, `fiscal`,
        and `monthly` data.
        """
        pass
