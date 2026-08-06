# -*- coding: utf-8 -*-
#
# test/test_ledger_transaction.py
#
__docformat__ = "restructuredtext en"

import os
import copy
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
        trans_data = copy.deepcopy(self._LDG_DATA['transaction'])
        trans_data['contribution'] = True
        ref_data0 = copy.deepcopy(self._LDG_DATA['reference'])
        ref_data0['ocs'] = True
        ref_data1 = copy.deepcopy(self._LDG_DATA['reference'])
        ref_data1['receipt'] = True
        ref_data1['number'] = 'B100'
        bank_data = copy.deepcopy(self._LDG_DATA['bank'])
        bank_data['withdrawal'] = True
        bank_data['amount'] = 10000
        coh_data = copy.deepcopy(self._LDG_DATA['coh'])
        coh_data['disbursement'] = True
        coh_data['amount'] = 1000
        incm_data = copy.deepcopy(self._LDG_DATA['income'])
        incm_data['other'] = True
        incm_data['amount'] = 850

        lt = LedgerTransaction(self.db, {})
        data = (
            (trans_data, lt._TRANS_TYPES, {'itype': 1}),
            (ref_data0, lt._REF_TYPES, {'itype': 1, 'number': ''}),
            (ref_data1, lt._REF_TYPES, {'itype': 3, 'number': 'B100'}),
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
        # date and trans_id querys
        date = badidatetime.date(183, 3, 5)
        dt_data = {'panel': {'date': date, 'purge': 0, 'memo': "Something"},
                   'transaction': {'contribution': False, 'distribution': True,
                                   'expense': False, 'other': False},
                   'reference': {'ocs': True, 'check': False, 'receipt': False,
                                 'deposit': False, 'number': ''},
                   'bank': {'deposit': True, 'withdrawal': False,
                            'amount': 5000, 'balance': None}
                   }
        lt = LedgerTransaction(self.db, dt_data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(4, rowcount, msg.format(4, rowcount))
        expect_data0 = (1, 1, 183, date, "Something", 2, 1, '', 0)
        # check_num query
        ck_data = {'panel': {'date': date, 'purge': 0, 'memo': "Description"},
                   'transaction': {'contribution': False,
                                   'distribution': False, 'expense': True,
                                   'other': False},
                   'reference': {'ocs': False, 'check': True, 'receipt': False,
                                 'deposit': False, 'number': '1000'},
                   'bank': {'deposit': False, 'withdrawal': True,
                            'amount': 5000, 'balance': None},
                   'expenses': {'national_baháí_fund': 10000,
                                'regional_baháí_council': 5000},
                   }
        lt = LedgerTransaction(self.db, ck_data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(6, rowcount, msg.format(6, rowcount))
        expect_data1 = (2, 2, 183, date, "Description", 3, 2, '1000', 0)
        # rcpt_num query
        rt_data = {'panel': {'date': date, 'purge': 0,
                             'memo': "Description of the transaction."},
                   'transaction': {'contribution': True,
                                   'distribution': False, 'expense': False,
                                   'other': False},
                   'reference': {'ocs': False, 'check': False, 'receipt': True,
                                 'deposit': False, 'number': 'B1000'},
                   'coh': {'replenishment': True, 'disbursement': False,
                           'amount': 5000, 'balance': None},
                   }
        lt = LedgerTransaction(self.db, rt_data)
        rowcount = await lt.insert_ledger_transaction(183)
        self.assertEqual(4, rowcount, msg.format(4, rowcount))
        expect_data2 = (3, 3, 183, date, "Description of the transaction.", 1,
                        3, 'B1000', 0)

        data = (
            (date, None, None, None, None, False, expect_data0),
            (None, 1, None, None, None, False, expect_data0),
            (None, None, 2, '1000', None, False, expect_data1),
            (None, None, 3, 'B1000', None, False, expect_data2),
            (None, None, None, None, 'Description', True,
             (expect_data1, expect_data2)),
            )

        for date, trans_id, r_type, number, memo, multi, expected in data:
            result = await lt.select_ledger_transaction(
                183, date=date, trans_id=trans_id, r_type=r_type,
                number=number, memo=memo)

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
        expect_data0 = (1, 1, 183, date, 'Description', 2, 1, '', 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Description"},
                'transaction': {'contribution': False, 'distribution': True,
                                'expense': False, 'other': False},
                'reference': {'ocs': True, 'check': False, 'receipt': False,
                              'deposit': False, 'number': ''},
                'bank': {'deposit': True, 'withdrawal': False, 'amount': 5000,
                         'balance': None}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(date.year)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
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
        expect_data0 = (1, 1, 183, date, 'Description', 1, 3, 'B1000', 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Description"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': False},
                'reference': {'ocs': False, 'check': False, 'receipt': True,
                              'deposit': False, 'number': 'B1000'},
                'coh': {'replenishment': True, 'disbursement': False,
                        'amount': 5000, 'balance': None}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(date.year)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
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
        expect_data0 = (1, 1, 183, date, "Description", 1, 1, '', 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Description"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': False},
                'reference': {'ocs': True, 'check': False, 'receipt': False,
                              'deposit': False, 'number': ''},
                'income': {'local_fund': True, 'contributed_expense': False,
                           'other': False, 'amount': 5000, 'balance': None}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(date.year)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
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
        expect_data0 = (1, 1, 183, date, "Description", 3, 1, '', 0)
        expect_data1 = [(1, 'national_baháí_fund', 10000),
                        (1, 'regional_baháí_council', 5000)]
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Description"},
                'transaction': {'contribution': False, 'distribution': False,
                                'expense': True, 'other': False},
                'reference': {'ocs': True, 'check': False, 'receipt': False,
                              'deposit': False, 'number': ''},
                'expenses': {'national_baháí_fund': 10000,
                             'regional_baháí_council': 5000}
                }
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        rowcount = await lt.insert_ledger_transaction(date.year)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
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
        err_msg1 = "Error during ledger insert."
        date = badidatetime.date(183, 3, 5)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Description"},
                'transaction': {'contribution': False, 'distribution': False,
                                'expense': True, 'other': False},
                'reference': {'checkX': '', 'receipt': '', 'deposit': '',
                              'ocs': True},
                }
        lt = LedgerTransaction(self.db, data)

        with self.assertRaises(sqlite3.ProgrammingError) as cm:
            await lt.insert_ledger_transaction(date.year)

        ex = str(cm.exception)
        self.assertIn(err_msg0, ex)
        file_data = self.read_text_file(self.log_path)
        result = self.find_text(file_data, 'ledger_transaction insert_ledger',
                                1, err_msg1)
        self.assertIn(err_msg1, result)

    #@unittest.skip("Temporarily skipped")
    async def test_update_ledger_transaction_bank(self):
        """
        Test that the update_ledger_transaction method updates the bank data.
        """
        trans_id = 1
        expect_rowcount = 4
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, 183, date, 'Updated', 3, 1, '', 0)
        expect_data1 = (1, 1, 2, 5000, None)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Inserted"},
                'transaction': {'contribution': False, 'distribution': True,
                                'expense': False, 'other': False},
                'reference': {'ocs': True, 'check': False, 'receipt': False,
                              'deposit': False, 'number': ''},
                'bank': {'deposit': True, 'withdrawal': False, 'amount': 5000,
                         'balance': None}
                }
        u_data = copy.deepcopy(data)
        u_data['panel']['memo'] = "Updated"
        u_data['transaction']['distribution'] = False
        u_data['transaction']['expense'] = True
        u_data['bank']['deposit'] = False
        u_data['bank']['withdrawal'] = True
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        await lt.insert_ledger_transaction(date.year)
        lt = LedgerTransaction(self.db, u_data)
        rowcount = await lt.update_ledger_transaction(trans_id)
        self.assertEqual(expect_rowcount, rowcount, msg.format(
            expect_rowcount, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_bank(header_pk)
        result = result[0]
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_ledger_transaction_coh(self):
        """
        Test that the update_ledger_transaction method updates the coh data.
        """
        trans_id = 1
        expected_records = 4
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, 183, date, 'Updated', 1, 3, 'R9999', 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Inserted"},
                'transaction': {'contribution': False, 'distribution': False,
                                'expense': True, 'other': False},
                'reference': {'ocs': False, 'check': False, 'receipt': True,
                              'deposit': False, 'number': 'STR9999'},
                'coh': {'replenishment': False, 'disbursement': True,
                        'amount': 5000, 'balance': None}
                }
        u_data = copy.deepcopy(data)
        u_data['panel']['memo'] = "Updated"
        u_data['transaction']['contribution'] = True
        u_data['transaction']['expense'] = False
        u_data['reference']['number'] = 'R9999'
        u_data['coh']['replenishment'] = True
        u_data['coh']['disbursement'] = False
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        await lt.insert_ledger_transaction(date.year)
        lt = LedgerTransaction(self.db, u_data)
        rowcount = await lt.update_ledger_transaction(trans_id)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_coh(header_pk)
        result = result[0]
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_ledger_transaction_income(self):
        """
        Test that the update_ledger_transaction method updates the coh data.
        """
        trans_id = 1
        expected_records = 4
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, 183, date, 'Updated', 1, 1, '', 0)
        expect_data1 = (1, 1, 1, 5000, None)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Inserted"},
                'transaction': {'contribution': False, 'distribution': False,
                                'expense': True, 'other': False},
                'reference': {'ocs': False, 'check': False, 'receipt': True,
                              'deposit': False, 'number': 'STR9999'},
                'income': {'local_fund': False, 'contributed_expense': True,
                           'other': False, 'amount': 5000, 'balance': None}
                }
        u_data = copy.deepcopy(data)
        u_data['panel']['memo'] = "Updated"
        u_data['transaction']['contribution'] = True
        u_data['transaction']['expense'] = False
        u_data['reference']['ocs'] = True
        u_data['reference']['receipt'] = False
        u_data['reference']['number'] = ''
        u_data['income']['local_fund'] = True
        u_data['income']['contributed_expense'] = False
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        await lt.insert_ledger_transaction(date.year)
        lt = LedgerTransaction(self.db, u_data)
        rowcount = await lt.update_ledger_transaction(trans_id)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_income(header_pk)
        result = result[0]
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_ledger_transaction_expenses(self):
        """
        Test that the update_ledger_transaction method updates the coh data.
        """
        trans_id = 1
        expected_records = 6
        date = badidatetime.date(183, 3, 5)
        expect_data0 = (1, 1, 183, date, 'Updated', 3, 2, '1000', 0)
        expect_data1 = [(1, 'deputization_fund', ''),
                        (1, 'national_baháí_fund', 15000),
                        (1, 'regional_baháí_council', 10000)]
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Inserted"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': False},
                'reference': {'ocs': True, 'check': False, 'receipt': False,
                              'deposit': False, 'number': ''},
                'expenses': {'national_baháí_fund': 10000,
                             'regional_baháí_council': 5000,
                             'deputization_fund': 1000}
                }
        u_data = copy.deepcopy(data)
        u_data['panel']['memo'] = "Updated"
        u_data['transaction']['contribution'] = False
        u_data['transaction']['expense'] = True
        u_data['reference']['ocs'] = False
        u_data['reference']['check'] = True
        u_data['reference']['number'] = '1000'
        u_data['expenses']['national_baháí_fund'] = 15000
        u_data['expenses']['regional_baháí_council'] = 10000
        u_data['expenses']['deputization_fund'] = ''
        msg = "Expected {}, found {}."
        lt = LedgerTransaction(self.db, data)
        await lt.insert_ledger_transaction(date.year)
        lt = LedgerTransaction(self.db, u_data)
        rowcount = await lt.update_ledger_transaction(trans_id)
        self.assertEqual(expected_records, rowcount, msg.format(
            expected_records, rowcount))
        result = await lt.select_ledger_transaction(date.year, date=date)
        result = result[0][:-2]
        self.assertEqual(expect_data0, result, msg.format(
            expect_data0, result))
        header_pk = result[0]
        result = await lt.select_expenses(header_pk)
        self.assertEqual(expect_data1, result, msg.format(
            expect_data1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_ledger_transaction_error(self):
        """
        Test that the update_ledger_transaction method reports errors properly.
        """
        trans_id = 1
        err_msg0 = "You did not supply a value for binding parameter :number."
        err_msg1 = "Error during ledger update."
        date = badidatetime.date(183, 3, 5)
        data = {'panel': {'date': date, 'purge': 0, 'memo': "Inserted"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': False},
                'reference': {'ocs': True, 'check': True, 'receipt': False,
                              'deposit': False, 'number': '1000'}
                }
        u_data = copy.deepcopy(data)
        u_data['panel']['memo'] = "Updated"
        u_data['reference'].pop('number')
        lt = LedgerTransaction(self.db, data)
        await lt.insert_ledger_transaction(date.year)
        lt = LedgerTransaction(self.db, u_data)

        with self.assertRaises(sqlite3.ProgrammingError) as cm:
            await lt.update_ledger_transaction(trans_id)

        ex = str(cm.exception)
        self.assertIn(err_msg0, ex)
        file_data = self.read_text_file(self.log_path)
        result = self.find_text(file_data, 'ledger_transaction update_ledger',
                                1, err_msg1)
        self.assertIn(err_msg1, result)
