# -*- coding: utf-8 -*-
#
# test/test_preperation.py
#
__docformat__ = "restructuredtext en"

import os
import unittest
import badidatetime

from src.config import TomlPanelConfig
from src.preperation import DataPreperation

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestDataPreperation(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._tpc = TomlPanelConfig()
        self.log_path = os.path.join(self._tpc.user_log_fullpath, LOGFILE_NAME)

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
        data = (
            ({}, None, None, False, False, err_msg0),    # No data
            (part_data, 183, 3, False, True, err_msg1.format(
                "locale_name, treasurer")),              # Partial data
            (full_data, None, None, True, False, None),  # Full data
            )
        msg = "Expexted {}, found {}."
        fiscal_years = {'data': [(183, 3, 5, 1, 1, 0), (184, 3, 5, 0, 0, 0)]}
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, fiscal_years)
        self.assertEqual(2, rowcount)

        for items, year, month, valid, partial, expected in data:
            error = await self.tdp.organization(items, year, month)

            if valid:
                if partial:
                    self.assertEqual(expected, error)
                    file_data = self.read_text_file(self.log_path)
                    result = self.find_text(
                        file_data, 'testing preperation organization',
                        2, expected)
                    self.assertIn(expected, result, msg.format(
                        expected, result))
                else:  # Current Year (full_data)
                    self.assertEqual(expected, error)
                    fy0 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=183)
                    self.assertEqual(1, len(fy0), msg.format(
                        expected, len(fy0)))
                    fy1 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=184)
                    self.assertEqual(1, len(fy0), msg.format(
                        expected, len(fy0)))
                    months = self.db.cache.get(self.db._T_MONTH)
                    self.assertEqual(20, len(months), msg.format(
                        20, len(months)))
                    fields = self.db.cache.get(self.db._T_FIELD_TYPE)
                    self.assertEqual(45, len(fields), msg.format(
                        45, len(fields)))
            else:
                self.assertEqual(expected, error)
                file_data = self.read_text_file(self.log_path)
                result = self.find_text(file_data,
                                        'testing preperation organization',
                                        2, expected)
                self.assertIn(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_organization_prev_next_year(self):
        """
        Test that the organization method inserts or updates the fiscal_year
        table for the previous and next years.
        """
        err_msg0 = ("Cannot enter a year that is not immediately before or "
                    "after the earliest or latest year. Found {} with "
                    "earliest: {}, and latest: {}.")
        prev_2_sofy = badidatetime.date(181, 3, 5)
        next_2_sofy = badidatetime.date(185, 3, 5)
        prev_sofy = badidatetime.date(182, 3, 5)
        next_sofy = badidatetime.date(184, 3, 5)
        org_data = {'locale_name': 'New York', 'locality_prefix': '0',
                    'location_city_name': 'New York',
                    'start_of_fiscal_year': None,
                    'total_membership': '18', 'treasurer': 'Joe Schmo'}
        data = (
            (prev_2_sofy, 183, 3, (), err_msg0.format(181, 183, 184)),
            (next_2_sofy, 183, 3, (), err_msg0.format(185, 183, 184)),
            (prev_sofy, 183, 3, (182, 183, 184), None),  # Previous year
            (next_sofy, 183, 3, (183, 184, 185), None),  # Next year
            )
        msg = "Expexted {}, found {}."
        fys = [(183, 3, 5, 1, 1, 0), (184, 3, 5, 0, 0, 0)]
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, {'data': fys})

        for date, year, month, years, expected in data:
            org_data['start_of_fiscal_year'] = date
            error = await self.tdp.organization(org_data, year, month)

            if expected is None:
                self.assertEqual(expected, error)
                # Current field previous year
                fy0 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=years[0])
                self.assertEqual(0, fy0[0][4], msg.format(0, fy0[0][4]))
                # Current field current year
                fy1 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=years[1])
                self.assertEqual(1, fy1[0][4], msg.format(1, fy1[0][4]))
                # Current field next year
                fy2 = self.db.cache.get(self.db._T_FISCAL_YEAR, year=years[2])
                self.assertEqual(0, fy2[0][4], msg.format(0, fy2[0][4]))
            else:
                self.assertEqual(expected, error, msg.format(expected, error))

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
    async def test_budget(self):
        """
        Test that the budget method inserts or updates budget data properly.
        """
        data = (
            ({'administration': 100}, 183, 3, True),
            )
        msg = "Expected {}, found {}."

        for bgt_data, year, month, insert in data:
            if insert:
                items = self.db.cache.get(self.db._T_DATA, year=year,
                                          r_type='budget')
                # Should not have data
                self.assertEqual([], items, msg.format([], items))
                await self.insert_fiscal_year()
                await self.insert_field_data('budget')
                error = await self.tdp.budget(bgt_data, year, month)
                items = self.db.cache.get(self.db._T_DATA, year=year,
                                          r_type='budget')
                value = bgt_data['administration']
                #print('POOP1', bgt_data, items)
                #self.assertEqual(value, items[0][1], msg.format(
                #    value, items[0][1]))
            else:
                await self.insert_data()
                await self.tdp.db.cache.load()
                result = self.db.cache.get(self.db._T_DATA, year=183,
                                           r_type='budget')
                #print('POOP', result)

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
                months = self.db.cache.get(self.db._T_MONTH)
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

    @unittest.skip("Temporarily skipped")
    async def test__insert_update_config_data_table(self):
        """
        Test that the _insert_update_config_data_table method inserts or
        updates the config_date table.
        """
        err_msg0 = "Could not find field {} in {}."
        await self.asyncTearDown()
        data = {field: 0 for field in self.db.cache.ORG_FIELDS}
        rowcount = await self.db._add_fields_to_field_type_table(data)
        data = (
            (183, 3, 'organization', org_data),
            #('budget', ),
            )
        msg = "Expected {}, found {}."

        for r_type in data:
            pass

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
    async def test__latest_fiscal_year(self):
        """
        Test that the _latest_fiscal_year property returns the 1st fiscal
        year in the DB.
        """
        data = [(182, 3, 5, 0, 0, 0), (183, 3, 5, 1, 1, 0),
                (184, 3, 5, 0, 0, 0)]
        rowcount = await self.tdp.db.cache.insert(
            self.tdp.db._T_FISCAL_YEAR, {'data': data})
        self.assertEqual(len(data), rowcount)
        result = self.tdp._latest_fiscal_year
        self.assertEqual(data[2][0], result)

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
