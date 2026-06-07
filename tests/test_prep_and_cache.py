# -*- coding: utf-8 -*-
#
# test/test_prep_and_cache.py
#
__docformat__ = "restructuredtext en"

import unittest
from src.prep_and_cache import DataPreperation
from src.utilities import StoreObjects

from . import log, check_flag, patchers
from .base_database_test import BaseAsyncTests


class FakeMainFrame:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mf = StoreObjects().get_object('MainFrame')

    @property
    def panel(self):
        return {}


class TestDataPreperation(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)

    async def asyncSetUp(self):
        await self.db.create_db()
        self.tdp = DataPreperation(self.db)

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    async def test_organization(self):
        """
        Test that the organization method inserts or updates the config_date,
        fiscal_year, and field_type tables.
        """
        pass

    #@unittest.skip("Temporarily skipped")
    async def test_fiscal(self):
        """
        Test that the fiscal method updates the cache and DB.
        """
        data = {'data': [(183, 3, 5, 1, 1, 0)]}
        year = data['data'][0][0]
        month = data['data'][0][1]
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, data)
        self.assertEqual(1, rowcount)
        updated_data = {'current_fiscal_year': 0,
                        'work_on_this_fiscal_year': 0, 'audit_complete': 1}
        result = await self.tdp.fiscal(updated_data, year, month)
        cfy = result[0][3]
        wotfy = result[0][4]
        ac = result[0][5]
        self.assertEqual(updated_data['current_fiscal_year'], cfy)
        self.assertEqual(updated_data['work_on_this_fiscal_year'], wotfy)
        self.assertEqual(updated_data['audit_complete'], ac)

    @unittest.skip("Temporarily skipped")
    async def test__first_run_initialization(self):
        """
        Test that the _first_run_initialization method initializes the database
        with all current panel data.
        """
        # First day of fiscal year.
        year = 183
        month = 3
        day = 5
        mf = FakeMainFrame()
        StoreObjects().set_object('MainFrame', self)
        await self.tdp._first_run_initialization(year, month, day)
        result = self.db.cache.get(self.db._T_FISCAL_YEAR)
        print(result)
        # *** TODO *** Make a fake MainFrame fixture.

    #@unittest.skip("Temporarily skipped")
    async def test__entered_next_year(self):
        """
        Test that the _entered_next_year method updates the previous fiscal
        year, updates this fiscal year, and inserts the next fiscal year.
        """
        items = {'data': [(182, 3, 5, 1, 1, 0), (183, 3, 5, 0, 0, 0)]}
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, items)
        self.assertEqual(2, rowcount)
        rowcount = await self.tdp._entered_next_year(183, 3, 5)
        self.assertEqual(3, rowcount)

        data = (
            (182, [(182, 3, 5, 0, 0, 0)]),
            (183, [(183, 3, 5, 1, 1, 0)]),
            (184, [(184, 3, 5, 0, 0, 0)]),
            )
        msg = "Expected {}, found{}."

        for year, expected in data:
            result = self.tdp.db.cache.get(self.db._T_FISCAL_YEAR, year=year)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test__entered_previous_year(self):
        """
        Test that the _entered_previous_year method inserts the next
        fiscal year.
        """
        expected = [(183, 3, 5, 0, 0, 0)]
        rowcount = await self.tdp._entered_previous_year(183, 3, 5)
        self.assertEqual(1, rowcount)
        result = self.tdp.db.cache.get(self.db._T_FISCAL_YEAR, year=183)
        msg = f"Expected {expected}, found{result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    def test__add_location_data(self):
        """
        Test that the _add_location_data method correctly adds the IANA key,
        latitude and longitude to the organization record.
        """
        msg = "Expected {}, found {}."
        data = {'locale_name': 'New York', 'locality_prefix': '0',
                'location_city_name': 'New York',
                'start_of_fiscal_year': '0183-03-05', 'total_membership': '20',
                'treasurer': '<your treasurer>'}
        data, error = self.tdp._add_location_data(data)
        expect_iana = 'America/New_York'
        iana_name = data.get('iana_name')
        expect_latitude = 40.7127281
        latitude = data.get('latitude')
        expect_longitude = -74.0060152
        longitude = data.get('longitude')
        self.assertEqual(expect_iana, iana_name, msg.format(
            expect_iana, iana_name))
        self.assertEqual(expect_latitude, latitude, msg.format(
            expect_latitude, latitude))
        self.assertEqual(expect_longitude, longitude, msg.format(
            expect_longitude, longitude))

    #@unittest.skip("Temporarily skipped")
    def test__find_timezone(self):
        """
        Test that the _find_timezone method correctly finds the IANA key,
        latitude and longitude.
        """
        msg = "Expected {}, found {}."
        address = 'New York'
        iana, lat, lon, error = self.tdp._find_timezone(address)
        expect_iana = 'America/New_York'
        expect_latitude = 40.7127281
        expect_longitude = -74.0060152
        self.assertEqual(expect_iana, iana, msg.format(expect_iana, iana))
        self.assertEqual(expect_latitude, lat, msg.format(
            expect_latitude, lat))
        self.assertEqual(expect_longitude, lon, msg.format(
            expect_longitude, lon))

    #@unittest.skip("Temporarily skipped")
    async def test__earliest_fiscal_year(self):
        """
        Test that the _earliest_fiscal_year property returns the 1st fiscal
        year in the DB.
        """
        data = [(182, 3, 5, 0, 0, 0), (183, 3, 5, 1, 1, 0),
                (184, 3, 5, 0, 0, 0)]
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, {'data': data})
        result = self.tdp._earliest_fiscal_year
        self.assertEqual(data[0][0], result)

    #@unittest.skip("Temporarily skipped")
    async def test_organization_data(self):
        """
        Test that the organization_data property returns the current year's
        organization data.
        """
        await self.insert_data()
        await self.tdp.db.cache.load()
        result = self.tdp.organization_data
        fields = result.keys()

        for field in self.tdp.db.cache.ORG_FIELDS:
            self.assertIn(field, fields)


class TestCache(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)

    async def asyncSetUp(self):
        await self.db.create_db()
        self.db.cache._flush_cache()
        await self.insert_data()
        await self.db.cache.load()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

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
        #log.debug("%s", self.db.cache._store[183])
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
    def test_get(self):
        """
        Test that the get method returns the correct data depending on the
        DB table.
        """
        err_msg0 = "Invalid `r_type`, found {}."
        data = (
            (183, self.db._T_DATA, 'organization', True, 'iana_name'),
            (183, self.db._T_DATA, 'budget', True, 'cash_in_bank'),
            (184, self.db._T_FISCAL_YEAR, None, True, 184),
            (183, self.db._T_MONTH, None, True, 'Ayyám-i-Há'),
            #(183, self.db._T_MONTHLY, None, True, 'Joe Shmo'),
            (183, self.db._T_DATA, 'invalid', False,
             err_msg0.format('invalid')),
            )
        msg = "Expected {}, found {}"

        for year, table_name, record_type, valid, data_to_find in data:
            if valid:
                result = self.db.cache.get(table_name, year=year,
                                           r_type=record_type)

                match table_name:
                    case self.db._T_DATA:
                        test_fields = result.keys()
                    case self.db._T_FISCAL_YEAR:
                        test_fields = [item[1] for item in result]  # year
                    case self.db._T_MONTH:
                        test_fields = [item[1] for item in result]  # month
                    case self.db._T_MONTHLY:
                        test_fields = [item[5] for item in result]  # treasurer

                self.assertIn(data_to_find, test_fields, msg.format(
                    data_to_find, test_fields))
            else:
                with self.assertRaises(AssertionError) as cm:
                    self.db.cache.get(table_name, year=year,
                                      r_type=record_type)

                expect = str(cm.exception)
                self.assertEqual(expect, data_to_find)
