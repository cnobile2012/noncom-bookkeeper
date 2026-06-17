# -*- coding: utf-8 -*-
#
# test/test_cache.py
#
__docformat__ = "restructuredtext en"
import unittest

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestCache(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)

    async def asyncSetUp(self):
        await self.db.create_db()
        self.db.cache._flush_cache()
        await self.insert_data()
        await self.db.cache.load()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    async def test_has_cache(self):
        """
        Test that the has_cache property returns True if there is cashed
        items and False if not.
        """
        self.db.cache._flush_cache()
        await self.truncate_all_tables()
        msg = "Expected {} found {}."

        for has_data in (False, True):
            if has_data:
                await self.insert_data()
                await self.db.cache.load()
                result = self.db.cache.has_cache
            else:
                result = self.db.cache.has_cache

            self.assertEqual(has_data, result, msg.format(has_data, result))

    #@unittest.skip("Temporarily skipped")
    def test_key_set_get(self):
        """
        Test that the key set and get properties work correctly.
        """
        self.db.cache.key = 'JUNK'
        result = self.db.cache.key
        self.assertEqual('JUNK', result)

    #@unittest.skip("Temporarily skipped")
    async def test_load_no_data(self):
        """
        Test that the load method loads no `organization`, `fiscal`,
        and `monthly` data with an empty DB.
        """
        # Since asyncSetUp() creates all the data and this test doesn't
        # want them, we delete everything.
        self.db.cache._flush_cache()
        await self.truncate_all_tables()
        expected = False
        msg = "Expected {}, found {}"
        has_flds = self.db.cache.has_fields_data
        has_orgz = self.db.cache.has_organization_cache_data
        has_bdgt = self.db.cache.has_budget_cache_data
        has_fscl = self.db.cache.has_fiscal_cache_data
        has_mnth = self.db.cache.has_month_cache_data
        has_mnly = self.db.cache.has_monthly_cache_data
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
        has_flds = self.db.cache.has_fields_data
        has_orgz = self.db.cache.has_organization_cache_data
        has_bdgt = self.db.cache.has_budget_cache_data
        has_fscl = self.db.cache.has_fiscal_cache_data
        has_mnth = self.db.cache.has_month_cache_data
        has_mnly = self.db.cache.has_monthly_cache_data
        self.assertTrue(has_flds, msg.format(expected, has_flds))
        self.assertTrue(has_orgz, msg.format(expected, has_orgz))
        self.assertTrue(has_bdgt, msg.format(expected, has_bdgt))
        self.assertTrue(has_fscl, msg.format(expected, has_fscl))
        self.assertTrue(has_mnth, msg.format(expected, has_mnth))
        #self.assertTrue(has_mnly, msg.format(expected, has_mnly))

    #@unittest.skip("Temporarily skipped")
    async def test__load_field_type(self):
        """
        Test that the _load_field_type method selects from the database
        all field_type data and populates storage with it.
        """
        err_msg0 = f"'{self.db._T_FIELD_TYPE}'"
        self.db.cache._flush_cache()

        with self.assertRaises(KeyError) as cm:
            self.db.cache._store[self.db._T_FIELD_TYPE]

        expected = str(cm.exception)
        self.assertEqual(expected, err_msg0)
        await self.db.cache._load_field_type()
        result = self.db.cache._store[self.db._T_FIELD_TYPE]
        self.assertIsInstance(result, list)

    #@unittest.skip("Temporarily skipped")
    async def test__load_month(self):
        """
        Test that the _load_month method selects from the database
        all field_type data and populates storage with it.
        """
        err_msg0 = f"'{self.db._T_MONTH}'"
        self.db.cache._flush_cache()

        with self.assertRaises(KeyError) as cm:
            self.db.cache._store[self.db._T_MONTH]

        expected = str(cm.exception)
        self.assertEqual(expected, err_msg0)
        await self.db.cache._load_month()
        result = self.db.cache._store[self.db._T_MONTH]
        self.assertIsInstance(result, list)

    #@unittest.skip("Temporarily skipped")
    async def test__load_fiscal_year(self):
        """
        Test that the _load_fiscal_year method selects from the database
        all fiscal_year data and populates storage with it.
        """
        err_msg0 = "183"
        self.db.cache._flush_cache()

        with self.assertRaises(KeyError) as cm:
            self.db.cache._store[183][self.db._T_FISCAL_YEAR]

        expected = str(cm.exception)
        self.assertEqual(expected, err_msg0)
        await self.db.cache._load_fiscal_year()
        result = self.db.cache._store[183][self.db._T_FISCAL_YEAR]
        self.assertIsInstance(result, list)

    #@unittest.skip("Temporarily skipped")
    async def test__load_config_data(self):
        """
        Test that the _load_config_data method selects from the database
        all config_data data and populates storage with it.
        """
        err_msg0 = "None"
        self.db.cache._flush_cache()

        with self.assertRaises(KeyError) as cm:
            self.db.cache._store[None][self.db._T_DATA]

        expected = str(cm.exception)
        self.assertEqual(expected, err_msg0)
        self.db.cache.year = 183
        self.db.cache._store[self.db.cache.year] = {}
        await self.db.cache._load_config_data()
        result = self.db.cache._store[183][self.db._T_DATA]
        self.assertIsInstance(result, list)

    #@unittest.skip("Temporarily skipped")
    async def test__load_monthly(self):
        """
        Test that the _load_monthly method selects from the database
        all config_data data and populates storage with it.
        """
        err_msg0 = "None"
        self.db.cache._flush_cache()

        with self.assertRaises(KeyError) as cm:
            self.db.cache._store[None][self.db._T_MONTHLY]

        expected = str(cm.exception)
        self.assertEqual(expected, err_msg0)
        self.db.cache.year = 183
        self.db.cache._store[self.db.cache.year] = {}
        await self.db.cache._load_monthly()
        result = self.db.cache._store[183][self.db._T_MONTHLY]
        self.assertIsInstance(result, list)

    #@unittest.skip("Temporarily skipped")
    def test_fields(self):
        """
        Test that the fields property returns just the field names.
        """
        msg = "Field {} not in {}"
        result = self.db.cache.fields

        for field in self.db.cache.ORG_FIELDS:
            self.assertIn(field, result, msg.format(field, result))

    #@unittest.skip("Temporarily skipped")
    def test_get_bgt_fields(self):
        """
        Test that the get_bgt_fields property teturns just the budget fields.
        """
        msg = "Field {} found in {}"
        result = self.db.cache.get_bgt_fields

        for field in self.db.cache.ORG_FIELDS:
            self.assertNotIn(field, result, msg.format(field, result))

    #@unittest.skip("Temporarily skipped")
    def test_available_years(self):
        """
        Test that the available_years property a list of years in the cache.
        """
        expected = [183, 184]
        result = self.db.cache.available_years
        self.assertEqual(expected, result)

    #@unittest.skip("Temporarily skipped")
    def test_get(self):
        """
        Test that the get method returns the correct data depending on the
        DB table.
        """
        err_msg0 = "Invalid `r_type`, found '{}'."
        data = (
            (183, self.db._T_FIELD_TYPE, None, True, 'longitude'),
            (183, self.db._T_DATA, 'organization', True, 'iana_name'),
            (183, self.db._T_DATA, 'budget', True, 'cash_in_bank'),
            (183, self.db._T_DATA, None, True, ('iana_name', 'cash_in_bank')),
            (184, self.db._T_FISCAL_YEAR, None, True, 184),
            (183, self.db._T_MONTH, None, True, 'Ayyám-i-Há'),
            #(183, self.db._T_MONTHLY, None, True, 'Joe Shmo'),
            (183, self.db._T_DATA, 'invalid', False,
             err_msg0.format('invalid')),
            )
        msg = "Expected {}, found {}"

        for year, table_name, record_type, valid, expected in data:
            if valid:
                result = self.db.cache.get(table_name, year=year,
                                           r_type=record_type)

                match table_name:
                    case self.db._T_FIELD_TYPE:
                        test_fields = [item[1] for item in result]  # field
                    case self.db._T_DATA:
                        test_fields = [item[1] for item in result]  # value
                    case self.db._T_FISCAL_YEAR:
                        test_fields = [item[1] for item in result]  # year
                    case self.db._T_MONTH:
                        test_fields = [item[1] for item in result]  # month
                    case self.db._T_MONTHLY:
                        test_fields = [item[5] for item in result]  # treasurer

                if isinstance(expected, tuple):
                    self.assertIn(expected[0], test_fields, msg.format(
                        expected[0], test_fields))
                    self.assertIn(expected[1], test_fields, msg.format(
                        expected[1], test_fields))
                else:
                    self.assertIn(expected, test_fields, msg.format(
                        expected, test_fields))
            else:
                with self.assertRaises(AssertionError) as cm:
                    self.db.cache.get(table_name, year=year,
                                      r_type=record_type)

                result = str(cm.exception)
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert(self):
        """
        Test that the insert method properly inserts data in the database
        and cache.
        """
        self.db.cache._flush_cache()
        await self.truncate_all_tables()
        t_month = {'data': self.db.ordered_month()}
        t_fs = {'data': [(183, 3, 5, 1, 1, 0), (184, 3, 5, 0, 0, 0)]}
        t_data = {'year': 183, 'month': 3, 'data': {
            'iana_name': 'America/New_York', 'latitude': 40.7127281,
            'locale_name': 'New York', 'locality_prefix': '0',
            'location_city_name': 'New York', 'longitude': -74.0060152,
            'start_of_fiscal_year': '183-03-05', 'total_membership': '20',
            'treasurer': '<your treasurer>'}}
        data = (
            (self.db._T_FIELD_TYPE, {'data': self.db.cache.ORG_FIELDS}, 9),
            (self.db._T_MONTH, t_month, 20),
            (self.db._T_FISCAL_YEAR, t_fs, 2),
            (self.db._T_DATA, t_data, 9),
            #(self.db._T_MONTHLY, None, 20),
            ('InvalidTable', {}, 0)
            )
        msg = "Expected {}, found {}"

        for table_name, inserts, expected in data:
            rowcount = await self.db.cache.insert(table_name, inserts)
            self.assertEqual(expected, rowcount, msg.format(
                expected, rowcount))

    #@unittest.skip("Temporarily skipped")
    async def test_update(self):
        """
        Test that the update method updates data in the database
        and cache.
        """
        t_fs = {'data': [(183, 3, 5, 1, 1, 0), (184, 3, 5, 0, 0, 0)]}
        data = self.db.cache.get(self.db._T_DATA, year=183,
                                 r_type='organization')
        t_data = {'data': []}

        for item in data:
            if item[1] == 'total_membership':
                t_data['data'].append((item[0], '25'))
            elif item[1] == 'treasurer':
                t_data['data'].append((item[0], '<a different treasurer>'))

        data = (
            (self.db._T_FISCAL_YEAR, t_fs, 2),
            (self.db._T_DATA, t_data, 2),
            #(self.db._T_MONTHLY, None, 20),
            ('InvalidTable', {}, 0)
            )
        msg = "Expected {}, found {}"

        for table_name, updates, expected in data:
            rowcount = await self.db.cache.update(table_name, updates)
            self.assertEqual(expected, rowcount, msg.format(
                expected, rowcount))
