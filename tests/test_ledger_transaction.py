# -*- coding: utf-8 -*-
#
# test/test_ledger_transaction.py
#
__docformat__ = "restructuredtext en"

import os
import unittest
import sqlite3
import aiosqlite
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

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        # Must be here to get logging capture to work.
        self._set = Settings()
        self.log_path = os.path.join(self._set.user_log_fullpath, LOGFILE_NAME)

    async def asyncSetUp(self):
        await self.db.create_db()
        self.db.cache._flush_cache()
        await self.insert_data()
        await self.db.cache.load()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    def test__make_types(self):
        """
        Test that the _make_types method converts linear values into a
        sequence of numbers.
        """
        trans_data = dict(self._LDG_DATA['transaction'])
        trans_data['contribution'] = True
        ref_data0 = dict(self._LDG_DATA['reference'])
        ref_data0['ocs'] = True
        ref_data1 = dict(self._LDG_DATA['reference'])
        ref_data1['receipt_number'] = 'B100'
        ref_data1['ocs'] = False
        bank_data = dict(self._LDG_DATA['bank'])
        bank_data['withdrawal'] = True
        bank_data['amount'] = 10000
        coh_data = dict(self._LDG_DATA['coh'])
        coh_data['disbursement'] = True
        coh_data['amount'] = 1000
        incm_data = dict(self._LDG_DATA['income'])
        incm_data['misc'] = True
        incm_data['amount'] = 850

        lt = LedgerTransaction(self.db, {})
        data = (
            (trans_data, lt._TRANS_TYPES, {'itype': 1, 'other': ''}),
            (ref_data0, lt._REF_TYPES, {'check_number': '',
                                        'receipt_number': '', 'itype': 1}),
            (ref_data1, lt._REF_TYPES, {'check_number': '',
                                        'receipt_number': 'B100', 'itype': 0}),
            (bank_data, lt._BANK_TYPES, {'itype': 2, 'amount': 10000,
                                         'balance': ''}),
            (coh_data, lt._COH_TYPES, {'itype': 2, 'amount': 1000,
                                       'balance': ''}),
            (incm_data, lt._INCM_TYPES, {'itype': 3, 'amount': 850,
                                         'balance': ''}),
            ({}, {}, {}),
            )
        msg = "Expected {}, found {}."

        for items, types, expected in data:
            result = lt._make_types(items, types)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_select_ledger_transaction(self):
        """
        Test that the select_ledger_transaction method selects
        ledger_transaction data properly.
        """
        msg = "Expected {}, found {}."
        # date and trans_num querys
        date = badidatetime.date(183, 3, 5)
        dt_data = {'panel': {'date': date, 'purged': 0, 'memo': "Something"},
                   'transaction': {'contribution': False, 'distribution': True,
                                   'expense': False, 'other': ''},
                   'reference': {'check_number': '', 'receipt_number': '',
                                 'ocs': True},
                   'bank': {'deposit': True, 'withdrawal': False,
                            'amount': 5000, 'balance': None}
                   }
        lt = LedgerTransaction(self.db, dt_data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(4, rowcount, msg.format(4, rowcount))
        expect_data0 = (1, 1, date, "Something", 183, 3, 5, 184, 3, 5, 2,
                        '', '', '', 1, 0)
        # ck_num query
        ck_data = {'panel': {'date': date, 'purged': 0, 'memo': "Description"},
                   'transaction': {'contribution': False,
                                   'distribution': False, 'expense': True,
                                   'other': ''},
                   'reference': {'check_number': '1000', 'receipt_number': '',
                                 'ocs': False},
                   'bank': {'deposit': False, 'withdrawal': True,
                            'amount': 5000, 'balance': None},
                   'expenses': {'national_baháí_fund': 10000,
                                'regional_baháí_council': 5000},
                   }
        lt = LedgerTransaction(self.db, ck_data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(6, rowcount, msg.format(6, rowcount))
        expect_data1 = (2, 2, date, "Description", 183, 3, 5, 184, 3, 5, 3,
                        '', '1000', '', 0, 0)
        # rcpt_num query
        rt_data = {'panel': {'date': date, 'purged': 0,
                             'memo': "Description of the transaction."},
                   'transaction': {'contribution': True,
                                   'distribution': False, 'expense': False,
                                   'other': ''},
                   'reference': {'check_number': '', 'receipt_number': 'B1000',
                                 'ocs': False},
                   'coh': {'replenishment': True, 'disbursement': False,
                           'amount': 5000, 'balance': None},
                   }
        lt = LedgerTransaction(self.db, rt_data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(4, rowcount, msg.format(4, rowcount))
        expect_data2 = (3, 3, date, "Description of the transaction.",
                        183, 3, 5, 184, 3, 5, 1, '', '', 'B1000', 0, 0)

        data = (
            (date, None, None, None, None, False, expect_data0),
            (None, 1, None, None, None, False, expect_data0),
            (None, None, '1000', None, None, False, expect_data1),
            (None, None, None, 'B1000', None, False, expect_data2),
            (None, None, None, None, 'Description', True,
             (expect_data1, expect_data2)),
            )

        for date, trans_num, ck_num, rcpt_num, memo, multi, expected in data:
            result = await lt.select_ledger_transaction(
                183, date=date, trans_num=trans_num, ck_num=ck_num,
                rcpt_num=rcpt_num, memo=memo)

            if multi:
                for idx, row in enumerate(result):
                    row = row[:-2]
                    self.assertEqual(expected[idx], row, msg.format(
                        expected[idx], row))
            else:
                result = result[0][:-2]
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_ledger_transaction_bank(self):
        """
        Test that the insert_ledger_transaction method inserts
        bank data properly.
        """
        expected_records = 4
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, date, 'Description', 183, 3, 5, 184, 3, 5, 2,
                        '', '', '', 1, 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purged': 0,
                          'memo': "Description"},
                'transaction': {'contribution': False, 'distribution': True,
                                'expense': False, 'other': ''},
                'reference': {'check_number': '', 'receipt_number': '',
                              'ocs': True},
                'bank': {'deposit': True, 'withdrawal': False, 'amount': 5000,
                         'balance': None}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(183, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_bank(header_pk)
        result = result[0]
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_ledger_transaction_coh(self):
        """
        Test that the insert_ledger_transaction method inserts
        coh data properly.
        """
        expected_records = 4
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, date, 'Description', 183, 3, 5, 184, 3, 5, 1,
                        '', '', 'B1000', 0, 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purged': 0,
                          'memo': "Description"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': ''},
                'reference': {'check_number': '', 'receipt_number': 'B1000',
                              'ocs': False},
                'coh': {'replenishment': True, 'disbursement': False,
                        'amount': 5000, 'balance': None}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(183, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_coh(header_pk)
        result = result[0]
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_ledger_transaction_income(self):
        """
        Test that the insert_ledger_transaction method inserts
        income data properly.
        """
        expected_records = 4
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, date, "Description", 183, 3, 5, 184, 3, 5, 1,
                        '', '', '', 1, 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purged': 0,
                          'memo': "Description"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': ''},
                'reference': {'check_number': '', 'receipt_number': '',
                              'ocs': True},
                'income': {'local_fund': True, 'contributed_expense': False,
                           'misc': False, 'amount': 5000, 'balance': None}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(183, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_income(header_pk)
        result = result[0]
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_ledger_transaction_expenses(self):
        """
        Test that the insert_ledger_transaction method inserts
        income data properly.
        """
        expected_records = 5
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, date, "Description", 183, 3, 5, 184, 3, 5, 3,
                        '', '', '', 1, 0)
        expect_data1 = [(1, 'national_baháí_fund', 10000),
                        (1, 'regional_baháí_council', 5000)]
        data = {'panel': {'date': date, 'purged': 0,
                          'memo': "Description"},
                'transaction': {'contribution': False, 'distribution': False,
                                'expense': True, 'other': ''},
                'reference': {'check_number': '', 'receipt_number': '',
                              'ocs': True},
                'expenses': {'national_baháí_fund': 10000,
                             'regional_baháí_council': 5000}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(183, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_expenses(header_pk)
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_insert_ledger_transaction_error(self):
        """
        Test that the insert_ledger_transaction method reports errors properly.
        """
        err_msg0 = "You did not supply a value"
        err_msg1 = "Error during ledger insert"
        date = badidatetime.date(183, 3, 5)
        data = {'panel': {'date': date, 'purged': 0,
                          'memo': "Description"},
                'transaction': {'contribution': False, 'distribution': False,
                                'expense': True, 'other': ''},
                'reference': {'check_numberX': '', 'receipt_number': '',
                              'ocs': True},
                }
        lt = LedgerTransaction(self.db, data)

        with self.assertRaises(sqlite3.ProgrammingError) as cm:
            await lt.insert_ledger_transaction(183)

        ex = str(cm.exception)
        self.assertIn(err_msg0, ex)
        file_data = self.read_text_file(self.log_path)
        result = self.find_text(file_data, 'ERROR testing ledger_transaction',
                                1, err_msg1)
        self.assertIn(err_msg1, result)
