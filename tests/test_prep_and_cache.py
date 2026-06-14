# -*- coding: utf-8 -*-
#
# test/test_prep_and_cache.py
#
__docformat__ = "restructuredtext en"

import os
import unittest
import badidatetime

from src.config import TomlPanelConfig
from src.prep_and_cache import DataPreperation

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests
from .fixtures import FakeMainFrame, Options


class TestDataPreperation(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._tpc = TomlPanelConfig()
        self.log_path = os.path.join(self._tpc.user_log_fullpath, LOGFILE_NAME)
        FakeMainFrame(options=Options())

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
        sofy = badidatetime.date(183, 3, 5)
        next_sofy = badidatetime.date(184, 3, 5)
        err_msg0 = ("Organization Information data must be entered before "
                    "any other data can be entered.")
        err_msg1 = "The '{}' field(s) must not be empty."
        part_data = {'locale_name': '', 'locality_prefix': '0',
                     'location_city_name': 'New York',
                     'start_of_fiscal_year': sofy,
                     'total_membership': '20', 'treasurer': ''}
        full_data = {'locale_name': 'New York', 'locality_prefix': '0',
                     'location_city_name': 'New York',
                     'start_of_fiscal_year': sofy,
                     'total_membership': '19', 'treasurer': 'Joe Schmo'}
        next_data = {'locale_name': 'New York', 'locality_prefix': '0',
                     'location_city_name': 'New York',
                     'start_of_fiscal_year': next_sofy,
                     'total_membership': '18', 'treasurer': 'Joe Schmo'}
        data = (
            ({}, None, None, False, False, err_msg0),  # No data
            (part_data, 183, 3, False, True, err_msg1.format(
                "locale_name, treasurer")),            # Partial data
            (full_data, None, None, True, False, 1),   # Full data
            #(next_data, 184, 3, True, False, 0),       # Next year
            )
        msg = "Expexted {}, found {}."
        fiscal_years = {'data': [(183, 3, 5, 1, 1, 0), (184, 3, 5, 0, 0, 0)]}
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, fiscal_years)
        self.assertEqual(2, rowcount)

        for items, year, month, valid, partial, expected in data:
            rowcount = await self.tdp.organization(items, year, month)

            if valid:
                if partial:
                    file_data = self.read_text_file(self.log_path)
                    result = self.find_text(
                        file_data, 'config prep_and_cache organization',
                        2, expected)
                    self.assertIn(expected, result, msg.format(
                        expected, result))
                else:  # Full data
                    fy0 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=183)
                    self.assertEqual(expected, len(fy0))
                    fy1 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=184)
                    self.assertEqual(expected, len(fy0))
                    months =  self.db.cache.get(self.db._T_MONTH)
                    self.assertEqual(20, len(months))
                    fields = self.db.cache.get(self.db._T_FIELD_TYPE)
                    self.assertEqual(45, len(fields))
            else:
                file_data = self.read_text_file(self.log_path)
                result = self.find_text(file_data,
                                        'config prep_and_cache organization',
                                        2, expected)
                self.assertIn(expected, result, msg.format(expected, result))

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

    #@unittest.skip("Temporarily skipped")
    async def test__first_run_initialization(self):
        """
        Test that the _first_run_initialization method initializes the database
        with all current panel data.
        """
        # First day of fiscal year.
        year = 183
        month = 3
        day = 5

        data = (
            (False, None, None, None, None),
            (True, 1, 1, 20, 45),
            )

        for after, current, audit, num_mon, num_flds in data:
            if after:
                await self.tdp._first_run_initialization(year, month, day)
                fy0 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=year)
                self.assertEqual(current, fy0[0][4])
                fy1 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=year+1)
                self.assertEqual(audit, fy0[0][5])
                months =  self.db.cache.get(self.db._T_MONTH)
                self.assertEqual(num_mon, len(months))
                fields = self.db.cache.get(self.db._T_FIELD_TYPE)
                self.assertEqual(num_flds, len(fields))
            else:
                self.assertFalse(self.db.cache.has_cache)

    #@unittest.skip("Temporarily skipped")
    async def test__enter_next_year(self):
        """
        Test that the _enter_next_year method updates the previous fiscal
        year, updates this fiscal year, and inserts the next fiscal year.
        """
        items = {'data': [(182, 3, 5, 1, 1, 0), (183, 3, 5, 0, 0, 0)]}
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, items)
        self.assertEqual(2, rowcount)
        rowcount = await self.tdp._enter_next_year(183, 3, 5)
        self.assertEqual(3, rowcount)

        data = (
            (182, (182, 3, 5, 0, 0, 0)),
            (183, (183, 3, 5, 1, 1, 0)),
            (184, (184, 3, 5, 0, 0, 0)),
            )
        msg = "Expected {}, found {}."

        for year, expected in data:
            result = self.tdp.db.cache.get(self.db._T_FISCAL_YEAR, year=year)
            record = result[0][1:-2]
            self.assertEqual(expected, record, msg.format(
                expected, record))

    #@unittest.skip("Temporarily skipped")
    async def test__enter_previous_year(self):
        """
        Test that the _enter_previous_year method inserts the next
        fiscal year.
        """
        expected = (183, 3, 5, 0, 0, 0)
        rowcount = await self.tdp._enter_previous_year(183, 3, 5)
        self.assertEqual(1, rowcount)
        result = self.tdp.db.cache.get(self.db._T_FISCAL_YEAR, year=183)
        record = result[0][1:-2]
        msg = f"Expected {expected}, found {record}."
        self.assertEqual(expected, record, msg)

    #@unittest.skip("Temporarily skipped")
    def test__add_location_data(self):
        """
        Test that the _add_location_data method correctly adds the IANA key,
        latitude and longitude to the organization record.
        """
        err_msg0 = "Cannot find the timezone for '{}'."
        err_msg1 = ("The 'location_city_name' field was not found, this "
                    "will cause some dates to be set to the wrong timezone, "
                    "most likely to UTC:00:00.")
        new_org = {'locale_name': 'New York', 'locality_prefix': '0',
                   'location_city_name': 'New York',
                   'start_of_fiscal_year': '0183-03-05',
                   'total_membership': '20', 'treasurer': '<your treasurer>'}
        bad_loc = {'locale_name': 'New York', 'locality_prefix': '0',
                   'location_city_name': "Someplace That Doesn't Exist",
                   'start_of_fiscal_year': '0183-03-05',
                   'total_membership': '20', 'treasurer': '<your treasurer>'}
        no_loc = {'locale_name': 'New York', 'locality_prefix': '0',
                  'location_city_name': "",
                  'start_of_fiscal_year': '0183-03-05',
                  'total_membership': '20', 'treasurer': '<your treasurer>'}
        data = (
            (new_org, True, ('America/New_York', 40.7127281, -74.0060152)),
            (bad_loc, False, err_msg0.format(bad_loc['location_city_name'])),
            (no_loc, False, err_msg1)
            )
        msg = "Expected {}, found {}."

        for data, valid, expected in data:
            result, error = self.tdp._add_location_data(data)

            if valid:
                expect_iana = expected[0]
                iana_name = result.get('iana_name')
                expect_latitude = expected[1]
                latitude = result.get('latitude')
                expect_longitude = expected[2]
                longitude = result.get('longitude')
                self.assertEqual(expect_iana, iana_name, msg.format(
                    expect_iana, iana_name))
                self.assertEqual(expect_latitude, latitude, msg.format(
                    expect_latitude, latitude))
                self.assertEqual(expect_longitude, longitude, msg.format(
                    expect_longitude, longitude))
            else:
                self.assertEqual(expected, error, msg.format(expected, error))

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
        self.assertEqual(len(data), rowcount)
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
        err_msg0 = "Invalid `r_type`, found {}."
        data = (
            (183, self.db._T_FIELD_TYPE, None, True, 'longitude'),
            (183, self.db._T_DATA, 'organization', True, 'iana_name'),
            (183, self.db._T_DATA, 'budget', True, 'cash_in_bank'),
            (183, self.db._T_DATA, None, True, []),
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

                if expected:
                    self.assertIn(expected, test_fields, msg.format(
                        expected, test_fields))
                else:
                    self.assertEqual(expected, test_fields, msg.format(
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
        t_data = {'year': 183, 'month': 3, 'data': [
            ('iana_name', 'America/New_York'), ('latitude', 40.7127281),
            ('locale_name', 'New York'), ('locality_prefix', '0'),
            ('location_city_name', 'New York'), ('longitude', -74.0060152),
            ('start_of_fiscal_year', '183-03-05'), ('total_membership', '20'),
            ('treasurer', '<your treasurer>')]}
        t_fs = {'data': [(183, 3, 5, 1, 1, 0), (184, 3, 5, 0, 0, 0)]}
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
