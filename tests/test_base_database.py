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

from src.bases import BaseGenerated
from src.config import TomlPanelConfig
from src.utilities import StoreObjects
from src.bahai_database import Database

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestBaseDatabase(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._tpc = TomlPanelConfig()
        self.log_path = os.path.join(self._tpc.user_log_fullpath, LOGFILE_NAME)

    async def asyncSetUp(self):
        with patch.object(self.db, '_mf',
                          StoreObjects().get_object('MainFrame')):
            await self.db.create_db()

        self.db.cache._flush_cache()
        await self.insert_data()
        await self.db.cache.load()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

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

    @unittest.skip("Temporarily skipped")
    async def test_populate_panels(self):
        """
        Test that the populate_panels method populates the panels if data
        is available.
        """
        fy = self.db.cache.get(self.db._T_FISCAL_YEAR)
        data = (
            (True, (fy[0][1], fy[0][2])),
            (False, (None, None)),
            )
        msg = "Expected {}, found {}."

        for load, expected in data:
            if not load:
                await self.asyncTearDown()

            with patch.object(self.db, '_mf',
                              StoreObjects().get_object('MainFrame')):
                result = await self.db.populate_panels()

            self.assertEqual(expected, result, msg.format(expected, result))

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

        with patch.object(self.db, '_mf',
                          StoreObjects().get_object('MainFrame')):
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

    @unittest.skip("Temporarily skipped")
    async def test__populate_month(self):
        """
        Test that the _populate_month method populates the currently
        chosen month with that months data.
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test_save_to_database(self):
        """
        Test that the save_to_database method inserts or updates panel
        data in the database.
        """
        err_msg0 = ("The 'locale_name, total_membership, treasurer, "
                    "location_city_name' field(s) must not be empty.")
        sofy = badidatetime.date(183, 3, 5)
        full_data = {'locale_name': 'New York', 'locality_prefix': '0',
                     'location_city_name': 'New York',
                     'start_of_fiscal_year': sofy,
                     'total_membership': '19', 'treasurer': 'Joe Schmo'}

        data = (
            ('organization', False, err_msg0),
            ('organization', True, None),
            )
        msg = "Expexted {}, found {}."
        await self.asyncTearDown()
        #await self.insert_fiscal_year()

        for panel_name, valid, expected in data:
            panel = self.get_panel(panel_name)

            with patch.object(self.db, '_mf',
                              StoreObjects().get_object('MainFrame')):
                error = await self.db.save_to_database(panel_name, panel)

            if valid:
                panels = {panel_name: panel}
                #await self.insert_field_data(panel_name)
                await self.db._populate_config_data_panels(sofy.year, panels)
                result = self.db.cache.get(self.db._T_DATA, year=sofy.year,
                                           r_type=panel_name)
                #print('POOP', self.db.cache._store)
            else:
                self.assertEqual(expected, error, msg.format(expected, error))

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
        Test that the _do_select_query method 
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
        err_msg0 = "The query {} does not end with a ';'."
        insert_query = "INSERT INTO config VALUES (?, ?);"
        multiple_query = (
            "UPDATE accounts SET user = :user, password = :password "
            "WHERE barcode = :barcode;"
            "UPDATE members SET displayName = :displayName, "
            "firstName = :firstName, lastName = :lastName, "
            "email = :email WHERE barcode = :barcode;"
            )
        items = {'user': 'fstone', 'password': 'Unencrypted',
                 'displayName': 'Fred S', 'firstName': 'Fred',
                 'lastName': 'Stone', 'email': 'fake@email.com',
                 'barcode': '100032'}
        data = (
            (insert_query, ('things', '5'), True, 1),
            (multiple_query, items, True, 2),
            (insert_query[:-1], ('things', '5'), False,
             err_msg0.format(insert_query[:-1])),
            )

        for query, params, valid, expected in data:
            if valid:
                rowcount = await self.bd._do_query(query, params)
                self.assertEqual(expected, rowcount)
            else:
                with self.assertRaises(AssertionError) as cm:
                    await self.bd._do_query(query, params)

                self.assertIn(expected, str(cm.exception))
