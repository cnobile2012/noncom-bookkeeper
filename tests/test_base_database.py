# -*- coding: utf-8 -*-
#
# tests/base_database_test.py
#
__docformat__ = "restructuredtext en"

import os
import unittest

from unittest.mock import patch

from src.config import TomlPanelConfig
from src.utilities import StoreObjects
from src.bahai_database import Database

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests
from .fixtures import FakeMainFrame, Options


class TestBaseDatabase(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._tpc = TomlPanelConfig()
        self.log_path = os.path.join(self._tpc.user_log_fullpath, LOGFILE_NAME)
        FakeMainFrame(options=Options())

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
                # Remove one iten from both tables and indexes to force
                # a failure.
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
        fy = self.db.cache.get(self.db._T_FISCAL_YEAR)
        data = (
            (False, (None, None)),
            (True, (fy[0][1], fy[0][2])),
            )
        msg = "Expected {}, found {}."

        for load, expected in data:
            if load:
                await self.insert_data()
            else:
                self.db.cache._flush_cache()
                await self.truncate_all_tables()

            with patch.object(self.db, '_mf',
                              StoreObjects().get_object('MainFrame')):
                result = await self.db.populate_panels()

            self.assertEqual(expected, result, msg.format(expected, result))

    @unittest.skip("Temporarily skipped")
    async def test__populate_config_data_panels(self):
        """
        Test that the _populate_config_data_panels method 
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__populate_monthly_panel(self):
        """
        Test that the _populate_monthly_panel method 
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test_save_to_database(self):
        """
        Test that the save_to_database method 
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__add_fields_to_field_type_table(self):
        """
        Test that the _add_fields_to_field_type_table method 
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__insert_update_config_data_table(self):
        """
        Test that the _insert_update_config_data_table method 
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__insert_update_monthly_table(self):
        """
        Test that the _insert_update_monthly_table method 
        """
        pass

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
