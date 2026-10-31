# -*- coding: utf-8 -*-
#
# tests/test_bahai_database.py
#
__docformat__ = "restructuredtext en"

import os
import copy
import unittest
import badidatetime

from unittest.mock import patch

from src.config import Settings
from src.utilities import StoreObjects
from src.custom_widgits import ordered_month

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestDatabase(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._set = Settings()
        self.log_path = os.path.join(self._set.user_log_fullpath, LOGFILE_NAME)

    async def asyncSetUp(self):
        await self.db.create_db()
        await self.insert_data()
        await self.db.cache.load()
        self.frame.create_panels()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    def test_set_local_coordinates(self):
        """
        Test that the set_local_coordinates method correctly sets the
        latitude and longitude in the badidatetime package.
        """
        data = (
            (None, None, (40.7127281, -74.0060152)),
            (35.5894, -78.7792, (35.5894, -78.7792)),
            )
        msg = "Expected '{}' found '{}'"

        for lat, lon, expected in data:
            self.db.set_local_coordinates(lat, lon)
            result = badidatetime.LOCAL_COORD[:2]
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_has_local_coords(self):
        """
        Test that the has_local_coords property returns True if the
        badidatetime package has the locale set.
        """
        data = (
            (None, None, False),
            (35.5894, -78.7792, True),
            )
        msg = "Expected '{}' found '{}'"

        for lat, lon, expected in data:
            if lat and lon:
                self.db.set_local_coordinates(lat, lon)

            result = self.db.has_local_coords
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_select_from_fiscal_year_table(self):
        """
        Test that the select_from_fiscal_year_table method returns the
        correct data based on the incoming arguments.
        """
        expect0 = (1, 183, 3, 5, 1, 1, 0)
        expect1 = [(1, 183, 3, 5, 1, 1, 0), (2, 184, 3, 5, 0, 0, 0)]
        expect2 = []
        data = (
            (183, None, None, None, None, None, None, expect0),
            (None, 3, None, None, None, None, None, expect1),
            (None, None, 5, None, None, None, None, expect1),
            (None, None, None, 1, None, None, None, expect0),
            (None, None, None, None, 1, None, None, expect0),
            (None, None, None, None, None, 1, None, expect2),
            (None, None, None, None, None, None, True, expect1),
            (None, None, None, None, None, None, None, expect1),
            )
        msg = "Expected '{}' found '{}'"

        for year, month, day, current, work, audit, fiscal, expected in data:
            items = await self.db.select_from_fiscal_year_table(
                year=year, month=month, day=day, current=current, work_on=work,
                audit=audit, fiscal=fiscal)

            if isinstance(items, list):
                result = [item[:-2] for item in items]
            else:
                result = items[:-2]

            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_into_fiscal_year_table(self):
        """
        Test that the insert_into_fiscal_year_table method inserts the
        normal case and for bulk data loads.
        """
        now = badidatetime.datetime.now()
        insert0 = [(185, 3, 5, 0, 0, 0)]
        insert1 = [(4, 186, 3, 5, 0, 0, 0, now, now)]
        data = (
            (insert0, 1),
            (insert1, 1),
            )
        msg = "Expected '{}' found '{}'"

        for insert, expected in data:
            result = await self.db.insert_into_fiscal_year_table(insert)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_fiscal_year_table(self):
        """
        Test that the update_fiscal_year_table method correctly updates
        a fiscal year.
        """
        msg = "Expected '{}' found '{}'"
        # First insert a fiscal year so we can then change it.
        insert = [(185, 3, 5, 0, 0, 0)]
        result = await self.db.insert_into_fiscal_year_table(insert)
        self.assertEqual(1, result, msg.format(1, result))
        update = [(185, 3, 5, 1, 1, 0)]
        result = await self.db.update_fiscal_year_table(update)
        self.assertEqual(1, result, msg.format(1, result))
        result = await self.db.select_from_fiscal_year_table(year=185)
        expected = (3, 185, 3, 5, 1, 1, 0)
        self.assertEqual(expected, result[:-2], msg.format(
            expected, result[:-2]))

    # @unittest.skip("Temporarily skipped")
    # def test_select_fiscal_year_balances(self):
    #     """
    #     Test that the select_fiscal_year_balances method 
    #     """

    # @unittest.skip("Temporarily skipped")
    # def test_insert_fiscal_year_balances(self):
    #     """
    #     Test that the insert_fiscal_year_balances method 
    #     """

    #@unittest.skip("Temporarily skipped")
    async def test_select_from_month_table(self):
        """
        Test that the select_from_month_table method returns one or many
        rows depending on the query type.
        """
        expect0 = (1, 'Bahá', 1)
        expect1 = (19, 'Ayyám-i-Há', 0)
        expect2 = (3, 'Jamál', 3)
        expect3 = [(1, 'Bahá', 1), (2, 'Jalál', 2), (3, 'Jamál', 3),
                   (4, "'Aẓamat", 4), (5, 'Núr', 5), (6, 'Raḥmat', 6),
                   (7, 'Kalimát', 7), (8, 'Kamál', 8), (9, "Asmá'", 9),
                   (10, "'Izzat", 10), (11, 'Mashíyyat', 11), (12, "'Ilm", 12),
                   (13, 'Qudrat', 13), (14, 'Qawl', 14), (15, 'Masá’il', 15),
                   (16, 'Sharaf', 16), (17, 'Sulṭán', 17), (18, 'Mulk', 18),
                   (19, 'Ayyám-i-Há', 0), (20, "'Alá'", 19)]
        data = (
            ('Bahá', None, None, expect0),
            (None, 0, None, expect1),
            (None, None, 3, expect2),
            (None, None, None, expect3),
            )
        msg = "Expected '{}' found '{}'"

        for name, order, pk, expected in data:
            items = await self.db.select_from_month_table(
                name=name, order=order, pk=pk)

            if isinstance(items, list):
                result = [item[:-1] for item in items]
            else:
                result = items[:-1]

            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_into_month_table(self):
        """
        Test that the insert_into_month_table method returns the row count
        of months inserted for either bulk or normal mode.
        """
        now = badidatetime.datetime.now()
        insert0 = self.db.ordered_month()
        insert1 = [(i, month, ord, now) for i, (ord, month) in enumerate(
            ordered_month().items(), start=1)]
        data = (
            (insert0, 20),
            (insert1, 20),
            )
        msg = "Expected '{}' found '{}'"

        for insert, expected in data:
            await self.asyncTearDown()
            result = await self.db.insert_into_month_table(insert)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_select_from_field_type_table(self):
        """
        Test that the select_from_field_type_table method correctly
        selects field records based on the mode.
        """
        expect0 = [(1, 'iana_name'), (2, 'latitude'), (3, 'locale_name'),
                   (4, 'locality_prefix'), (5, 'location_city_name'),
                   (6, 'longitude'), (7, 'start_of_fiscal_year'),
                   (8, 'total_membership'), (9, 'treasurer'),
                   (10, 'administration'), (11, 'area_teaching_committee'),
                   (12, 'asian_continental_board'),
                   (13, 'baháí_chair_for_world_peace_reserved_fund'),
                   (14, 'baháí_development_fund'),
                   (15, 'baháí_election_convention_contributions'),
                   (16, 'bosch_facilities_recovery_fund'),
                   (17, 'cash_in_bank'), (18, 'continental_baháí_fund'),
                   (19, 'deputization_fund'), (20, 'education'),
                   (21, 'house_of_worship_campus_reserves_fund'),
                   (22, 'humanitarian_relief_fund_in_usa'),
                   (23, 'humanitarian_relief_fund_world_center'),
                   (24, 'institute_properties_resurve_fund'),
                   (25, 'international_baháí_fund'),
                   (26, 'international_endowment_fund'),
                   (27, 'international_temples_fund'),
                   (28, 'legal_defense_for_the_refugees_in_turkey'),
                   (29, 'monetary_contributions'), (30, 'national_baháí_fund'),
                   (31, 'national_house_of_worship_canada'),
                   (32, 'online_contribution_service_holdings'),
                   (33, 'persian_baháí_media_service_fund_payam_e_doost'),
                   (34, 'persian_relief_fund_world_center'),
                   (35, 'proclamation'), (36, 'regional_baháí_council'),
                   (37, 'regional_facilities_fund'), (38, 'scolarships'),
                   (39, 'shrine_of_abdul_bahá'), (40, 'teaching'),
                   (41, 'total_membership_beginning_of_year'),
                   (42, 'total_outstanding_bills_previous_year'),
                   (43, 'us_baháí_archives_renovation_fund'),
                   (44, 'us_deputization_fund_international_pioneering'),
                   (45, 'wilmette_institute_unrestricted_contribution')]
        expect1 = [(2, 'latitude'), (6, 'longitude')]
        data = (
            (None, expect0),
            (['latitude', 'longitude'], expect1),
            )
        msg = "Expected '{}' found '{}'"

        for fields, expected in data:
            items = await self.db.select_from_field_type_table(fields)

            if isinstance(items, list):
                result = [item[:-2] for item in items]
            else:
                result = items[:-2]

            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_into_field_type_table(self):
        """
        Test that the insert_into_field_type_table method for both the
        normal and bulk modes.
        """
        now = badidatetime.datetime.now()
        insert0 = [(1, 'iana_name', now, now), (2, 'latitude', now, now)]
        data = (
            (['new_field_0', 'new_field_1'], 2),
            (insert0, 2),
            )
        msg = "Expected '{}' found '{}'"

        for fields, expected in data:
            await self.asyncTearDown()
            result = await self.db.insert_into_field_type_table(fields)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_field_type_table(self):
        """
        Test that the update_field_type_table method updates field
        types correctly.
        """
        msg = "Expected '{}' found '{}'"
        expected = 2
        data = [{'old_field': 'latitude', 'new_field': 'lat'},
                {'old_field': 'longitude', 'new_field': 'lon'}]
        result = await self.db.update_field_type_table(data)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_select_from_config_data_table(self):
        """
        Test that the select_from_config_data_table method returns
        the config data.
        """
        msg = "Expected '{}' found '{}'"
        data = ['iana_name', 'latitude', 'locale_name', 'locality_prefix',
                'location_city_name', 'longitude']
        year = 183
        expected = [
            (1, 'iana_name', 'America/New_York', 183, 3, 5, 184, 3, 5),
            (2, 'latitude', '40.7127281', 183, 3, 5, 184, 3, 5),
            (3, 'locale_name', 'New York', 183, 3, 5, 184, 3, 5),
            (4, 'locality_prefix', '0', 183, 3, 5, 184, 3, 5),
            (5, 'location_city_name', 'New York', 183, 3, 5, 184, 3, 5),
            (6, 'longitude', '-74.0060152', 183, 3, 5, 184, 3, 5)
            ]
        items = await self.db.select_from_config_data_table(data, year)
        result = [item[:-2] for item in items]
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_all_into_config_data_table(self):
        """
        Test that the insert_all_into_config_data_table method bulk
        loads config data.
        """
        msg = "Expected '{}' found '{}'"
        now = badidatetime.datetime.now()
        # pk, value, fy1fk, fy2fk, mfk, ffk, ctime, mtime
        # The mfk and ffk values are arbitrary, but must be in the db.
        data = [(1000, 'Text_0', 1, 2, 3, 10, now, now),
                (1001, 'Text_1', 1, 2, 3, 11, now, now)]
        expected = 2
        result = await self.db.insert_all_into_config_data_table(data)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_into_config_data_table(self):
        """
        Test that the insert_into_config_data_table method inserts
        configuration data.
        """
        await self.asyncTearDown()
        err_msg0 = "No current fiscal_year data in the database."
        err_msg1 = "Programming error, no field data."
        err_msg2 = "Programming error, no month data."
        err_msg3 = "Programming error, no 2nd year fiscal year data."
        insert = copy.deepcopy(self._ORG_DATA)
        insert['iana_name'] = 'America/New_York'
        insert['latitude'] = 40.7127281
        insert['longitude'] = -74.0060152
        data = (
            (183, 10, insert, True, err_msg0),
            (183, 10, insert, False, err_msg1),
            (183, 10, insert, False, err_msg2),
            (183, 10, insert, False, err_msg3),
            (183, 10, insert, True, 9),
            )
        msg = "Expected '{}' found '{}'"

        for year, month, items, valid, expected in data:
            if valid:
                result = await self.db.insert_into_config_data_table(
                    year, month, items)

                if result == 0:
                    file_data = self.read_text_file(self.log_path)
                    result = self.find_text(file_data, err_msg0, 1, expected)

                    self.assertIn(expected, result, msg.format(
                        expected, result))
                else:
                    self.assertEqual(expected, result, msg.format(
                        expected, result))
            else:
                with self.assertRaises(AssertionError) as cm:
                    await self.db.insert_into_config_data_table(
                        year, month, items)

                result = str(cm.exception)
                self.assertEqual(expected, result, msg.format(
                    expected, result))

            # One at a time fix the error conditions.
            if expected == err_msg0:
                fs_data = [(183, 3, 5, 1, 1, 0)]
                rowcount = await self.db.insert_into_fiscal_year_table(fs_data)
                self.assertEqual(1, rowcount)
            elif expected == err_msg1:
                fields = list(insert)
                rowcount = await self.db.insert_into_field_type_table(fields)
                self.assertEqual(9, rowcount)
            elif expected == err_msg2:
                rowcount = await self.db.insert_into_month_table(
                    self.db.ordered_month())
                self.assertEqual(20, rowcount)
            elif expected == err_msg3:
                fs_data = [(184, 3, 5, 0, 0, 0)]
                rowcount = await self.db.insert_into_fiscal_year_table(fs_data)
                self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_update_config_data_table(self):
        """
        Test that the update_config_data_table method updates the
        config_data table.
        """
        err_msg0 = "The pk '{}' is not an integer."
        err_msg1 = "The value '{}' is not a string."
        data = (
            ([('A', '')], False, err_msg0.format('A')),
            ([(1000, 1234)], False, err_msg1.format(1234)),
            ([(1, 'NOT_REAL')], True, 1)
            )
        msg = "Expected '{}' found '{}'"

        for update, valid, expected in data:
            if valid:
                result = await self.db.update_config_data_table(update)
                self.assertEqual(expected, result, msg.format(
                    expected, result))
            else:
                with self.assertRaises(AssertionError) as cm:
                    await self.db.update_config_data_table(update)

                result = str(cm.exception)
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_select_from_monthly_table(self):
        """
        Test that the select_from_monthly_table method selects the correct
        monthly data depending on the mode.
        """
        expect0 = [(1, 1, (183, 3), 1, 10000, 1000, 20, 'Joe Schmo', 0)]
        expect1 = [(8, 1, (183, 10), 20, 0, 0, 20, 'Joe Schmo', 0),
                   (9, 1, (183, 11), 25, 0, 0, 20, 'Joe Schmo', 0),
                   (10, 1, (183, 12), 30, 0, 0, 20, 'Joe Schmo', 0),
                   (1, 1, (183, 3), 1, 10000, 1000, 20, 'Joe Schmo', 0),
                   (2, 1, (183, 4), 2, 0, 0, 20, 'Joe Schmo', 0),
                   (3, 1, (183, 5), 5, 0, 0, 20, 'Joe Schmo', 0),
                   (4, 1, (183, 6), 10, 0, 0, 20, 'Joe Schmo', 0),
                   (5, 1, (183, 7), 15, 0, 0, 20, 'Joe Schmo', 0),
                   (6, 1, (183, 8), 20, 0, 0, 20, 'Joe Schmo', 0),
                   (7, 1, (183, 9), 20, 0, 0, 20, 'Joe Schmo', 0)]
        data = (
            (183, (183, 3), expect0),
            (183, None, expect1),
            )
        msg = "Expected '{}' found '{}'"

        for year, ym, expected in data:
            items = await self.db.select_from_monthly_table(year, ym)
            result = [item[:-2] for item in items]
            self.assertEqual(expected, result, msg.format(
                expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_all_into_monthly_table(self):
        """
        Test that the insert_all_into_monthly_table method inserts bulk
        data correctly.
        """
        msg = "Expected '{}' found '{}'"
        now = badidatetime.datetime.now()
        fs_data = [(186, 3, 5, 0, 0, 0)]
        rowcount = await self.db.insert_into_fiscal_year_table(fs_data)
        self.assertEqual(1, rowcount)
        data = [(1000, 1, (186, 3), 1, 10000, 1000, 20, 'Joe Schmo', 0,
                 now, now),
                (1001, 1, (186, 4), 2, 0, 0, 20, 'Joe Schmo', 0, now, now)]
        expected = 2
        result = await self.db.insert_all_into_monthly_table(data)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_into_monthly_table(self):
        """
        Test that the insert_into_monthly_table method inserts monthly
        data correctly.
        """
        msg = "Expected '{}' found '{}'"
        year = 184
        data = {'cal_year_month': (184, 3), 'participation': 20,
                'outstanding': 100.00, 'coh': 0.0, 'membership': 20,
                'treasurer': 'Joe Schmo', 'locality': 'NoWhere'}
        expected = 1
        result = await self.db.insert_into_monthly_table(year, data)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_monthly_table(self):
        """
        Test that the update_monthly_table method updates a monthly
        record correctly.
        """
        msg = "Expected '{}' found '{}'"
        year = 183
        values = ((183, 10), 30, 10.0, 100.0, 50, 'Joe Schmo', 'London')
        data = {field: values[i]
                for i, field in enumerate(self.db.MONTHLY_FIELD_MAP.values())}
        expected = 1
        result = await self.db.update_monthly_table(year, data)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_convert_date_to_yymmdd(self):
        """
        Test that the convert_date_to_yymmdd method converts an ISO date
        to a date object. If already a date object it is just passed through.
        """
        data = (
            ('0183-03-05', badidatetime.date(183, 3, 5)),
            (badidatetime.date(184, 3, 5), badidatetime.date(184, 3, 5))
            )
        msg = "Expected '{}' found '{}'"

        for value, expected in data:
            result = self.db.convert_date_to_yymmdd(value)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__ymd_from_iso(self):
        """
        Test that the _ymd_from_iso method converts an ISO string to a
        year, month, and day tuple.
        """
        msg = "Expected '{}' found '{}'"
        iso = '0183-03-05'
        expected = (183, 3, 5)
        result = self.db._ymd_from_iso(iso)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_today(self):
        """
        Test that the today method returns todays date.
        """
        msg = "Expected '{}' found '{}'"
        expected = badidatetime.date.today()
        result = self.db.today()
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_utc_tzinfo(self):
        """
        Test that the utc_tzinfo property returns the UTC coordinates
        in a time zone object.
        """
        msg = "Expected '{}' found '{}'"
        expected = '51.477928, -0.001545, 0, UTC'
        result = str(self.db.utc_tzinfo)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_tzinfo(self):
        """
        Test that the tzinfo property returns the local coordinates
        in a time zone object.
        """
        msg = "Expected '{}' found '{}'"
        expected = '40.7127281, -74.0060152, -5.0'
        result = str(self.db.tzinfo)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__get_standard_offset(self):
        """
        Test that the _get_standard_offset method returns the standard
        time offset in seconds for the current IANA name.
        """
        err_msg0 = "The IANA key has not been set."
        data = (
            ('America/New_York', True, -18000.0),
            ('America/Phoenix', True, -25200.0),
            ('', False, err_msg0),
            )
        msg = "Expected '{}' found '{}'"

        for name, valid, expected in data:
            if valid:
                result = self.db._get_standard_offset(name)
            else:
                with self.assertRaises(AssertionError) as cm:
                    self.db._get_standard_offset(name)

                result = str(cm.exception)

            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_index_of_calendar_year(self):
        """
        Test that the index_of_calendar_year method returns the index
        of the month in the fiscal year.
        """
        data = (
            ((183, 3), None, 0),
            ((183, 10), 183, 7),
            )
        msg = "Expected '{}' found '{}'"

        for date, year, expected in data:
            result = self.db.index_of_calendar_year(date, year)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_year_month_by_index(self):
        """
        Test that the year_month_by_index method returns the text used
        in the monthly panel dropdown widget.
        """
        err_msg0 = ("The index value is out of range, found '{}', it must "
                    "be between 0 and {}.")
        data = (
            (0, 183, True, '0183-03 Jamál'),
            (16, 183, True, '0183-00 Ayyám-i-Há'),
            (20, 183, True, '0184-03 Jamál'),
            (-1, 183, False, err_msg0.format(-1, 20)),
            (21, 183, False, err_msg0.format(21, 20)),
            )
        msg = "Expected '{}' found '{}'"

        for idx, year, valid, expected in data:
            if valid:
                result = self.db.year_month_by_index(idx, year)
            else:
                with self.assertRaises(AssertionError) as cm:
                    self.db.year_month_by_index(idx, year)

                result = str(cm.exception)

            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_full_fiscal_year_data(self):
        """
        Test that the full_fiscal_year_data method returns for all fiscal
        year months the order of the month in the fiscal year, the actual
        year of the month, the ordinal of the month in the actual year and
        the month name.
        """
        msg = "Expected '{}' found '{}'"
        year = 183
        expected = [(0, 183, 3, 'Jamál'), (1, 183, 4, "'Aẓamat"),
                    (2, 183, 5, 'Núr'), (3, 183, 6, 'Raḥmat'),
                    (4, 183, 7, 'Kalimát'), (5, 183, 8, 'Kamál'),
                    (6, 183, 9, "Asmá'"), (7, 183, 10, "'Izzat"),
                    (8, 183, 11, 'Mashíyyat'), (9, 183, 12, "'Ilm"),
                    (10, 183, 13, 'Qudrat'), (11, 183, 14, 'Qawl'),
                    (12, 183, 15, 'Masá’il'), (13, 183, 16, 'Sharaf'),
                    (14, 183, 17, 'Sulṭán'), (15, 183, 18, 'Mulk'),
                    (16, 183, 0, 'Ayyám-i-Há'), (17, 183, 19, "'Alá'"),
                    (18, 184, 1, 'Bahá'), (19, 184, 2, 'Jalál'),
                    (20, 184, 3, 'Jamál')]
        result = self.db.full_fiscal_year_data(year)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_populate_monthly_data(self):
        """
        Test that the populate_monthly_data method create a data structure
        that can be used to populate a monthly panel.
        """
        values0 = (10, 1, (183, 12), 30, 0, 0, 20, 'Joe Schmo', 0)
        items0 = {'month_index': '183-03 Jamál', 'participation': '',
                  'outstanding_bills': '', 'end_of_month_cash_on_hand': '',
                  'total_membership_this_month': '',
                  'treasurer_this_month': '', 'locality_prefix_month': 0}
        expect0 = {'month_index': 9, 'participation': 30,
                   'outstanding_bills': 0, 'end_of_month_cash_on_hand': 0,
                   'total_membership_this_month': 20,
                   'treasurer_this_month': 'Joe Schmo',
                   'locality_prefix_month': 0}
        expect1 = {'month_index': 0, 'participation': '',
                   'outstanding_bills': '', 'end_of_month_cash_on_hand': '',
                   'total_membership_this_month': 20,
                   'treasurer_this_month': 'Joe Schmo',
                   'locality_prefix_month': 0}
        values1 = list(values0)
        values1[7] = ''
        expect2 = {'month_index': 16, 'participation': 30,
                   'outstanding_bills': 0, 'end_of_month_cash_on_hand': 0,
                   'total_membership_this_month': 20,
                   'treasurer_this_month': 'Joe Schmo',
                   'locality_prefix_month': 0}
        data = (
            (9, values0, items0, expect0),
            (0, (), items0, expect1),
            (16, values1, items0, expect2),
            )
        msg = "Expected '{}' found '{}'"

        for month_idx, values, items, expected in data:
            result = self.db.populate_monthly_data(month_idx, values, items)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_convert_str_date(self):
        """
        Test that the convert_str_date method converts the drop down
        date string into a tuple of year and month.
        """
        msg = "Expected '{}' found '{}'"
        date_str = '183-03 Jamál'
        expected = (183, 3)
        result = self.db.convert_str_date(date_str)
        self.assertEqual(expected, result, msg.format(expected, result))
