# -*- coding: utf-8 -*-
#
# test/test_ledger_transaction.py
#
__docformat__ = "restructuredtext en"

import os
import unittest
import badidatetime
from unittest.mock import patch

from src.config import Settings
from src.ledger_transaction import LedgerTransaction
from src.utilities import StoreObjects

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestLedgerTransaction(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self._set = Settings()
        self.log_path = os.path.join(self._set.user_log_fullpath, LOGFILE_NAME)
        self.fmf = StoreObjects().get_object('MainFrame')

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)

    @unittest.skip("Temporarily skipped")
    async def test_insert_full_ledger_transaction(self):
        """
        """
        lt = LedgerTransaction()


    #@unittest.skip("Temporarily skipped")
    async def test__insert_transaction(self):
        """
        """
        query = f"SELECT * FROM {self.db._T_LEDGER_TRANSACTION};"

        data = ('')


        lt = LedgerTransaction(self.db)


    @unittest.skip("Temporarily skipped")
    async def test__insert_reference(self):
        """
        """
        lt = LedgerTransaction()


    @unittest.skip("Temporarily skipped")
    async def test__insert_header(self):
        """
        """
        lt = LedgerTransaction()


    @unittest.skip("Temporarily skipped")
    async def test__insert_bank(self):
        """
        """
        lt = LedgerTransaction()


    @unittest.skip("Temporarily skipped")
    async def test__insert_coh(self):
        """
        """
        lt = LedgerTransaction()


    @unittest.skip("Temporarily skipped")
    async def test__insert_income(self):
        """
        """
        lt = LedgerTransaction()


    @unittest.skip("Temporarily skipped")
    async def test__insert_expense(self):
        """
        """
        lt = LedgerTransaction()

