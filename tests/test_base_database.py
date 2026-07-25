# -*- coding: utf-8 -*-
#
# tests/base_database_test.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import unittest
import badidatetime

from unittest.mock import patch

from src.config import Settings
from src.utilities import StoreObjects
from src.base_database import BaseDatabase, adapt_tuple, convert_tuple

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestBaseDatabase(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._set = Settings()
        self.log_path = os.path.join(self._set.user_log_fullpath, LOGFILE_NAME)
        self.fmf = StoreObjects().get_object('MainFrame')

    async def asyncSetUp(self):
        with patch.object(self.db, '_mf', self.fmf):
            await self.db.create_db()

        await self.insert_data()
        await self.db.cache.load()
        self.frame.create_panels()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    def test_adapt_tuple(self):
        """
        Test that the adapt_tuple function correctly converts a tuple
        to a string.
        """
        year_month = (183, 3)
        result = adapt_tuple(year_month)
        self.assertIsInstance(result, str)

    #@unittest.skip("Temporarily skipped")
    def test_convert_tuple(self):
        """
        Test that the convert_tuple function correctly converts bytes to
        a tuple.
        """
        err_msg0 = "Expected tuple, got {}."
        year_month = b'(183, 3)'
        result = convert_tuple(year_month)
        self.assertIsInstance(result, tuple)
        bad_year_month = b'[183, 3]'

        with self.assertRaises(ValueError) as cm:
            convert_tuple(bad_year_month)

        ex = str(cm.exception)
        self.assertEqual(ex, err_msg0.format('list'))

    #@unittest.skip("Temporarily skipped")
    def test_set_local_coordinates(self):
        """
        Test that the set_local_coordinates method raises an exception
        if not overridden.
        """
        err_msg0 = "The 'set_local_coordinates' must be implemented."

        with self.assertRaises(NotImplementedError) as cm:
            bd = BaseDatabase()
            bd.set_local_coordinates()

        ex = str(cm.exception)
        self.assertEqual(ex, err_msg0)

    #@unittest.skip("Temporarily skipped")
    def test_get_db_columns(self):
        """
        Test that the get_db_columns method returns the column names
        for the specified table.
        """
        expected = ['pk', 'year', 'month', 'day', 'current', 'work_on',
                    'audit', 'ctime', 'mtime']
        result = self.db.get_db_columns(self.db._T_FISCAL_YEAR)
        self.assertEqual(expected, result)

    #@unittest.skip("Temporarily skipped")
    async def test_has_schema(self):
        """
        Test that the has_schema method returns True or False depending on
        if the schema found is what is expected.
        """
        err_msg0 = "Database table count is wrong it should be "
        err_msg1 = "Database index count is wrong it should be "
        data = (
            (False, True),
            (True, False),
            )
        msg = "Expected {}, with delete {}, found {}."

        for delete, expected in data:
            if delete:
                # Remove one item from both tables and indexes so a failure
                # situation can be tested.
                all_tables = dict(self.db._SCHEMA_TABLES)
                mis_tables = all_tables
                mis_tables.pop(self.db._T_LEDGER_EXPENSE)
                all_indices = list(self.db._SCHEMA_INDICES)
                mis_indices = all_indices
                mis_indices.pop()

                with patch.multiple(
                    self.db, _SCHEMA_TABLES=mis_tables,
                    _SCHEMA_INDICES=mis_indices,
                    _mf=StoreObjects().get_object('MainFrame')):

                    os.remove(self.db.user_data_fullpath)
                    await self.db.create_db()
                    result = await self.db.has_schema
                    self.assertEqual(expected, result)
                    file_data = self.read_text_file(self.log_path)
                    result = self.find_text(file_data, err_msg0, 1, err_msg0)
                    self.assertIn(err_msg0, result)
                    result = self.find_text(file_data, err_msg1, 1, err_msg1)
                    self.assertIn(err_msg1, result)
            else:
                result = await self.db.has_schema
                self.assertEqual(expected, result, msg.format(
                    expected, delete, result))

    #@unittest.skip("Temporarily skipped")
    async def test_populate_panels(self):
        """
        Test that the populate_panels method populates the panels if data
        is available.
        """
        log_msg0 = "Populating all panels in {:04d}-{:02d}."
        fy = self.db.cache.get(self.db._T_FISCAL_YEAR)[0]
        data = (
            (True, log_msg0.format(fy[1], fy[2])),
            (False, None),
            )
        msg = "Expected {}, found {}."

        for load, expected in data:
            if not load:
                await self.asyncTearDown()

            with patch.object(self.db, '_mf', self.fmf):
                result = await self.db.populate_panels()

            if load:
                file_data = self.read_text_file(self.log_path)
                result = self.find_text(file_data, "Populating all", 1,
                                        expected)
                self.assertIn(expected, result)
            else:
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test__populate_config_data_panels(self):
        """
        Test that the _populate_config_data_panels method populates all
        panals that use the config_data table.
        """
        msg = "Expected {}, found {}."
        self.db.cache._flush_cache()
        # Test that the cache and DB are empty.
        self.assertFalse(self.db.cache.fields)
        widgets = ('TextCtrl', 'BadiDatePickerCtrl')
        data = {4: 'New York', 6: '20', 8: 'Joe Schmo',
                10: badidatetime.date(183, 3, 5), 14: 'New York'}

        with patch.object(self.db, '_mf', self.fmf):
            await self.db._populate_config_data_panels(183, self.db._mf.panels)
            # Test that fields have be repopulated.
            self.assertTrue(self.db.cache.fields)
            # Now reload the data and test that the data is in the panels.
            await self.db.cache.load()
            await self.db._populate_config_data_panels(183, self.db._mf.panels)
            org_panel = self.db._mf.panels['organization']

            for idx, child in enumerate(org_panel.GetChildren()):
                if child.__class__.__name__ in widgets:
                    result = child.GetValue()
                    expected = data.get(idx)

                    if expected:
                        self.assertEqual(expected, result, msg.format(
                            expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test__populate_month(self):
        """
        Test that the _populate_month method populates the currently
        chosen month with that months data.
        """
        data = (
            (False, False, ''),  # This must be 1st
            (True, False, 'Joe Schmo'),
            #(True, True, ),
            )
        msg = "Expexted {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = self.db._mf.panels.get('monthly')

            for valid, insert, expected in data:
                if insert:
                    # Insert a row of monthly data
                    pass

                if valid:
                    await self.asyncTearDown()
                    await self.insert_data()
                    await self.db.cache.load()
                else:
                    await self.asyncTearDown()
                    data = {'data': [(183, 3, 5, 1, 1, 0)]}
                    await self.db.cache.insert(self.db._T_FISCAL_YEAR, data)
                    await self.db.cache._load_fiscal_year()

                fy = self.db.cache.get(self.db._T_FISCAL_YEAR)[0]
                await self.db._populate_month(fy)
                result = panel.GetChildren()[15].GetValue()
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test__populate_fiscal(self):
        """
        Test that the _populate_fiscal method sets the choices in the
        ComboBox widget in the fical panel.
        """
        with patch.object(self.db, '_mf', self.fmf):
            self.db._populate_fiscal()
            panel = self.db._mf.panels.get('fiscal')
            self.assertEqual('183-184', panel.GetChildren()[3].GetString(1))

    #@unittest.skip("Temporarily skipped")
    async def test_save_to_database_config_data(self):
        """
        Test that the save_to_database method inserts or updates organization
         and budget panel data in the database.
        """
        await self.asyncTearDown()
        await self.insert_months()
        await self.insert_fiscal_year()
        fy = self.db.cache.get(self.db._T_FISCAL_YEAR)[0]
        year, month = fy[1:3]
        err_msg0 = "The '{}' field(s) must not be empty."
        org_data = dict(self._ORG_DATA)
        org_data['locality_prefix'] = str(org_data['locality_prefix'])
        org_data['start_of_fiscal_year'] = str(
            org_data['start_of_fiscal_year'])
        org_data['iana_name'] = 'America/New_York'
        org_data['latitude'] = '40.7127281'
        org_data['longitude'] = '-74.0060152'
        data = (
            ('organization', self._ORG_EMPTY, {}, False,
             err_msg0.format("locale_name, total_membership, treasurer, "
                             "location_city_name")),
            ('organization', {}, org_data, True, len(org_data)),
            ('budget', self._BGT_EMPTY, {}, False,
             err_msg0.format("cash_in_bank, ocs_holdings, "
                             "total_outstanding_bills_previous_year, "
                             "total_membership_beginning_of_year, "
                             "monetary_contributions")),
            ('budget', {}, self._BGT_DATA, True, len(self._BGT_DATA)),
            )
        msg = "Expexted '{}', found '{}'."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, pre_poplt, values, valid, expected in data:
                panel = self.db._mf.panels.get(panel_name)

                if valid:
                    self.db.populate_panel_values(panel_name, panel, values)
                    items = self.db.collect_panel_values(panel)
                    error = await self.db.save_to_database(panel_name, panel)
                    self.assertIsNone(error, f"Expected 'none', found {error}")
                    result = self.db.cache.get(self.db._T_DATA, year=year,
                                               r_type=panel_name)

                    for field, value in values.items():
                        for record in result:
                            if field == record[1]:
                                self.assertEqual(value, record[2], msg.format(
                                    value, field, record[2]))
                else:
                    self.db.populate_panel_values(panel_name, panel, pre_poplt)
                    error = await self.db.save_to_database(panel_name, panel)
                    self.assertEqual(expected, error, msg.format(
                        expected, error))

    #@unittest.skip("Temporarily skipped")
    async def test_save_to_database_monthly(self):
        """
        Test that the save_to_database method inserts or updates the monthly
        panel data in the database.
        """
        await self.asyncTearDown()
        await self.insert_months()
        await self.insert_fiscal_year()
        fy = self.db.cache.get(self.db._T_FISCAL_YEAR)[0]
        year, month = fy[1:3]
        err_msg0 = "The '{}' field(s) must not be empty."
        mth_data = dict(self._MTH_DATA)
        mth_data['month_index'] = 1
        data = (
            ('monthly', self._MTH_EMPTY, {}, False, err_msg0.format(
                "total_membership_this_month, treasurer_this_month")),
            ('monthly', {}, mth_data, True, 1),
            )
        msg = "Expexted '{}', found '{}'."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, pre_poplt, values, valid, expected in data:
                panel = self.db._mf.panels.get(panel_name)

                if valid:
                    self.db.populate_panel_values(panel_name, panel, values)
                    items = self.db.collect_panel_values(panel)
                    error = await self.db.save_to_database(panel_name, panel)
                    self.assertIsNone(error, f"Expected 'none', found {error}")
                    result = self.db.cache.get(self.db._T_MONTHLY, year=year)
                    self.assertEqual(expected, len(result), msg.format(
                        expected, len(result)))
                else:
                    self.db.populate_panel_values(panel_name, panel, pre_poplt)
                    error = await self.db.save_to_database(panel_name, panel)
                    self.assertEqual(expected, error, msg.format(
                        expected, error))

    #@unittest.skip("Temporarily skipped")
    async def test_save_to_database_fiscal(self):
        """
        Test that the save_to_database method inserts or updates panel
        data in the database.
        """
        await self.asyncTearDown()
        await self.insert_months()
        err_msg0 = "Failed to update any fiscal year data."
        fy_data = dict(self._FY_DATA)
        fy_data['work_on_this_fiscal_year'] = True
        fy_data['audit_complete'] = True
        field_names = [name for name in fy_data if not name.startswith('fisc')]
        field_name_idx = zip(field_names, [4, 5, 6])
        data = (
            ('fiscal', fy_data, False, err_msg0),
            ('fiscal', fy_data, True, 1),
            )
        msg = "Expexted '{}', field_name '{}', found '{}'."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, values, valid, expected in data:
                panel = self.db._mf.panels.get(panel_name)

                if valid:
                    await self.insert_fiscal_year()
                    fy = self.db.cache.get(self.db._T_FISCAL_YEAR)[0]
                    year, month = fy[1:3]
                    self.db.populate_panel_values(panel_name, panel, values)
                    items = self.db.collect_panel_values(panel)
                    error = await self.db.save_to_database(panel_name, panel)
                    self.assertIsNone(error, f"Expected 'none', found {error}")
                    result = self.db.cache.get(self.db._T_FISCAL_YEAR,
                                               year=year)
                    size = len(result)
                    self.assertEqual(expected, size,
                                     f"Expected {expected}, found {size}.")

                    for fn, idx in field_name_idx:
                        value0 = values[fn]
                        value1 = result[0][idx]
                        self.assertEqual(value0, value1, msg.format(
                            value0, fn, value1))
                else:
                    error = await self.db.save_to_database(panel_name, panel)
                    self.assertEqual(expected, error,
                                     f"Expected '{expected}, found '{error}'.")

    #@unittest.skip("Temporarily skipped")
    async def test__add_fields_to_field_type_table(self):
        """
        Test that the _add_fields_to_field_type_table method correctly adds
        fields to the field_type table and the cache.
        """
        msg = "Expected {}, found {}."
        await self.asyncTearDown()
        long_field = "abc12" * 11
        fields = self.db.cache.ORG_FIELDS + [long_field]
        data = {field: 0 for field in fields}
        rowcount = await self.db._add_fields_to_field_type_table(data)
        fld_len = len(fields)
        err_msg0 = ("Found field(s) that are longer than "
                    f"{self.db._MAX_FIELD_LEN}, ['{long_field}'].")
        self.assertEqual(fld_len, rowcount, msg.format(fld_len, rowcount))
        file_data = self.read_text_file(self.log_path)
        result = self.find_text(file_data, err_msg0, 1, err_msg0)
        self.assertIn(err_msg0, result)

    @unittest.skip("Temporarily skipped")
    async def test__do_select_query(self):
        """
        Test that the _do_select_query method returns the correct data
        from the query.
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__do_insert_query(self):
        """
        Test that the _do_insert_query method returns the correct row
        count that was inserted.
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__do_update_query(self):
        """
        Test that the _do_update_query method returns returns the correct row
        count that was updated.
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__do_delete_query(self):
        """
        Test that the _do_delete_query method returns returns the correct row
        count that was deleted.
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__do_query(self):
        """
        Test that the _do_query method can insert, update, or delete records.
        """
        pass
