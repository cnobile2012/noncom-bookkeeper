# -*- coding: utf-8 -*-
#
# tests/test_populate_collect_panel.py
#
__docformat__ = "restructuredtext en"

import copy
import os
import wx
import unittest
import datetime
import badidatetime

from unittest.mock import patch

from src.bases import BaseGenerated
from src.config import Settings
from src.utilities import StoreObjects
from src.ledger_entry import SearchDialog
from src.ledger_transaction import LedgerTransaction

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestPopulateCollect(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._set = Settings()
        self.log_path = os.path.join(self._set.user_log_fullpath, LOGFILE_NAME)
        self.fmf = StoreObjects().get_object('MainFrame')

    async def asyncSetUp(self):
        await self.db.create_db()
        self.db.cache._flush_cache()
        await self.insert_data()
        await self.db.cache.load()
        self.frame.create_panels()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    async def _insert_transactions(self):
        """
        Insert a few transactions.
        """
        await self.asyncTearDown()
        await self.insert_fiscal_year()
        await self.insert_field_data(self._LDG_DATA['expenses'])
        # [((1, 183, badidatetime.date(183, 9, 6), 'Test OCS Contribution', 1,
        #    1, '', None, None, None, None, 1, 5000, 0), [])]
        date = badidatetime.date(183, 9, 6)
        data0 = {'panel': {'date': date, 'purge': 0,
                           'memo': "Test OCS Contribution"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': False},
                'reference': {'ocs': True, 'check': False, 'receipt': False,
                              'deposit': False, 'number': ''},
                'income': {'local_fund': True, 'contributed_expense': False,
                           'other': False, 'amount': 5000}
                 }
        lt = LedgerTransaction(self.db, data0)
        rowcount = await lt.insert_ledger_transaction(date.year)
        self.assertEqual(6, rowcount)
        # [((2, 183, badidatetime.date(183, 8, 5), 'Test OCS Contribution', 1,
        #    1, '', None, None, None, None, 1, 2000, 0), [])]
        date = badidatetime.date(183, 8, 5)
        data1 = {'panel': {'date': date, 'purge': 0,
                           'memo': "Test OCS Contribution"},
                'transaction': {'contribution': True, 'distribution': False,
                                'expense': False, 'other': False},
                'reference': {'ocs': True, 'check': False, 'receipt': False,
                              'deposit': False, 'number': ''},
                'income': {'local_fund': True, 'contributed_expense': False,
                           'other': False, 'amount': 2000}
                 }
        lt = LedgerTransaction(self.db, data1)
        rowcount = await lt.insert_ledger_transaction(date.year)
        self.assertEqual(6, rowcount)
        # [((3, 183, badidatetime.date(183, 8, 10), 'Test expenses', 3, 1, '',
        #    2, 30000, None, None, None, None, 0),
        #   [(3, 'national_baháí_fund', 20000),
        #    (3, 'regional_baháí_council', 10000)])]
        date = badidatetime.date(183, 8, 10)
        data2 = {'panel': {'date': date, 'purge': 0, 'memo': "Test expenses"},
                 'transaction': {'contribution': False, 'distribution': False,
                                 'expense': True, 'other': False},
                 'reference': {'ocs': True, 'check': False, 'receipt': False,
                               'deposit': False, 'number': ''},
                 'bank': {'deposit': False, 'withdrawal': True,
                          'amount': 30000},
                 'expenses': {'national_baháí_fund': 20000,
                              'regional_baháí_council': 10000}
                 }
        lt = LedgerTransaction(self.db, data2)
        rowcount = await lt.insert_ledger_transaction(date.year)
        self.assertEqual(9, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_has_org_info_data(self):
        """
        Test that the has_org_info_data property returns True or False
        depending on the existance of manditory data in the panel.
        """
        data = (
            ({}, False),
            (self._ORG_DATA, True),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = self.fmf.panels['organization']
            self.db.clear_panel('organization', panel)

            for values, expected in data:
                self.db.populate_panel_values('organization', panel, values)
                result = self.db.has_org_info_data
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_has_budget_data(self):
        """
        Test that the has_budget_data property returns True or False
        depending on the existance of manditory data in the panel.
        """
        data = (
            ({}, False),
            (self._BGT_DATA, True),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = self.fmf.panels['budget']
            self.db.clear_panel('budget', panel)

            for values, expected in data:
                self.db.populate_panel_values('budget', panel, values)
                result = self.db.has_budget_data
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_has_ledger_data(self):
        """
        Test that the has_ledger_data property returns True or False
        depending on the existance of manditory data in the panel.
        """
        ldg_data0 = copy.deepcopy(self._LDG_DATA)
        ldg_data0['panel']['transaction_id'] = 1
        ldg_data0['transaction']['contribution'] = True
        ldg_data0['reference']['ocs'] = True
        ldg_data0['income']['local_fund'] = True
        ldg_data0['income']['amount'] = '100.00'
        ldg_data0['income']['balance'] = '100.00'

        data = (
            ({}, False),
            (ldg_data0, True),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = self.fmf.panels['ledger']
            self.db.clear_panel('ledger', panel)

            for ldg_data, expected in data:
                self.db.populate_panel_values('ledger', panel, ldg_data)
                result = self.db.has_ledger_data
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test__check_panels_for_entries(self):
        """
        Test that the _check_panels_for_entries method correctly check
        if a given panel has entries.
        """
        ldg_data0 = copy.deepcopy(self._LDG_DATA)
        ldg_data0['panel']['transaction_id'] = 1
        ldg_data0['transaction']['contribution'] = True
        ldg_data0['reference']['ocs'] = True
        ldg_data0['income']['local_fund'] = True
        ldg_data0['income']['amount'] = '100.00'
        ldg_data0['income']['balance'] = '100.00'

        data = (
            ('organization', {}, False),
            ('budget', {}, False),
            ('ledger',  {}, False),
            ('organization', self._ORG_DATA, True),
            ('budget', self._BGT_DATA, True),
            ('ledger', ldg_data0, True),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, values, expected in data:
                panel = self.fmf.panels[panel_name]
                self.db.clear_panel(panel_name, panel)
                self.db.populate_panel_values(panel_name, panel, values)
                result = self.db._check_panels_for_entries(panel_name)
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test__lde_push(self):
        """
        Test that the lde_push method correctly pushes data onto a
        dictionary object.
        """
        ldg_values0 = {'panel': {'date': '0183-03-05', 'memo': 'Some text.'}}
        expect00 = {'panel': {'date': '0183-03-05'}}
        expect01 = {'panel': {'memo': 'Some text.'}}

        ldg_values1 = {'transaction': {'contribution': True},
                       'reference': {'ocs': True},
                       'income': {'local_fund': True, 'amount': '50.00'}}
        expect10 = {'transaction': {'contribution': True}}
        expect11 = {'reference': {'ocs': True}}
        expect12 = {'income': {'local_fund': True}}
        expect13 = {'income': {'amount': '50.00'}}

        ldg_values2 = {'transaction': {'distribution': True},
                       'reference': {'ocs': True},
                       'bank': {'amount': '150.00'}}
        expect20 = {'transaction': {'distribution': True}}
        expect21 = {'reference': {'ocs': True}}
        expect22 = {'bank': {'amount': '150.00'}}

        ldg_values3 = {'transaction': {'expense': True},
                       'reference': {'ocs': True},
                       'expenses': {'national_baháí_fund': '150.00'}}
        expect30 = {'transaction': {'expense': True}}
        expect31 = {'reference': {'ocs': True}}
        expect32 = {'expenses': {'national_baháí_fund': '150.00'}}
        data = (
            ('panel.date', '0183-03-05', ldg_values0, expect00),
            ('panel.memo', 'Some text.', ldg_values0, expect01),
            ('transaction.contribution', True, ldg_values1, expect10),
            ('reference.ocs', True, ldg_values1, expect11),
            ('income.local_fund', True, ldg_values1, expect12),
            ('income.amount', '50.00', ldg_values1, expect13),
            ('transaction.distribution', True, ldg_values2, expect20),
            ('reference.ocs', True, ldg_values2, expect21),
            ('bank.amount', '150.00', ldg_values2, expect22),
            ('transaction.expense', True, ldg_values3, expect30),
            ('reference.ocs', True, ldg_values3, expect31),
            ('expenses.national_baháí_fund', '150.00', ldg_values3, expect32),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = self.fmf.panels['ledger']

            for key, value, items, expected in data:
                values = {}
                self.db._lde_push(key, value, panel, values)
                self.assertEqual(expected, values, msg.format(
                    expected, values))

    #@unittest.skip("Temporarily skipped")
    async def test__lde_pop(self):
        """
        Test that the lde_pop method correctly pops values off a
        dictionary object.
        """
        ldg_values0 = {'panel': {'date': '0183-03-05', 'memo': 'Some text.'}}
        ldg_values1 = {'transaction': {'contribution': True},
                       'reference': {'ocs': True},
                       'income': {'local_fund': True, 'amount': '50.00'}}
        ldg_values2 = {'transaction': {'distribution': True},
                       'reference': {'ocs': True},
                       'bank': {'amount': '150.00'}}
        ldg_values3 = {'transaction': {'expense': True},
                       'reference': {'ocs': True},
                       'expenses': {'national_baháí_fund': '150.00'}}
        data = (
            ('panel.date', ldg_values0, '0183-03-05'),
            ('panel.memo', ldg_values0, 'Some text.'),
            ('transaction.contribution', ldg_values1, True),
            ('reference.ocs', ldg_values1, True),
            ('income.local_fund', ldg_values1, True),
            ('income.amount', ldg_values1, '50.00'),
            ('transaction.distribution', ldg_values2, True),
            ('reference.ocs', ldg_values2, True),
            ('bank.amount', ldg_values2, '150.00'),
            ('transaction.expense', ldg_values3, True),
            ('reference.ocs', ldg_values3, True),
            ('expenses.national_baháí_fund', ldg_values3, '150.00'),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = self.fmf.panels['ledger']

            for key, items, expected in data:
                result = self.db._lde_pop(key, panel, items)
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_collect_panel_values(self):
        """
        Test that the collect_panel_values method collects data from
        panels and converts it to appropreate values for the database.
        """
        mth_values = copy.deepcopy(self._MTH_DATA)
        mth_values['month_index'] = 0
        date = badidatetime.date(183, 3, 5)
        ldg_values0 = copy.deepcopy(self._LDG_DATA)
        ldg_values0['panel']['date'] = str(date)
        ldg_values0['panel']['transaction_id'] = '1'
        ldg_values0['transaction']['expense'] = True
        ldg_values0['reference']['ocs'] = True
        ldg_values0['expenses']['national_baháí_fund'] = '150.00'
        expect0 = copy.deepcopy(ldg_values0)
        expect0['panel']['date'] = date
        expect0['expenses']['national_baháí_fund'] = 15000

        data = (
            ('organization', 9, self._ORG_DATA, self._ORG_DATA),
            ('budget', 36, self._BGT_DATA, self._BGT_DATA),
            ('monthly', 7, mth_values, self._MTH_DATA),
            ('fiscal', 4, self._FY_DATA, self._FY_DATA),
            ('ledger', 7, ldg_values0, expect0),
            )
        msg = "Expected '{}', panel_name '{}', found '{}'."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, count, values, expected in data:
                panel = self.fmf.panels[panel_name]
                self.db.populate_panel_values(panel_name, panel, values)
                result = self.db.collect_panel_values(panel)
                self.assertEqual(count, len(result), msg.format(
                    count, panel_name, len(result)))
                #print(result, '\n', expected)

                for field_name, value in expected.items():
                    self.assertEqual(value, result[field_name], msg.format(
                        value, panel_name, result[field_name]))

    #@unittest.skip("Temporarily skipped")
    async def test_populate_panel_values(self):
        """
        Test that the populate_panel_values method populates the panel
        with the database values.
        """
        org_data = copy.deepcopy(self._ORG_DATA)
        org_data['start_of_fiscal_year'] = org_data[
            'start_of_fiscal_year'].isoformat()
        date = badidatetime.date(183, 3, 5)
        ldg_values0 = copy.deepcopy(self._LDG_DATA)
        ldg_values0['panel']['date'] = str(date)
        ldg_values0['panel']['transaction_id'] = '1'
        ldg_values0['transaction']['contribution'] = True
        ldg_values0['reference']['ocs'] = True
        ldg_values0['income']['local_fund'] = True
        ldg_values0['income']['amount'] = '50.00'
        expect0 = copy.deepcopy(ldg_values0)
        expect0['panel']['date'] = date
        expect0['income']['amount'] = 5000

        data = (
            ('organization', org_data, False, org_data),
            ('budget', self._BGT_DATA, False, self._BGT_DATA),
            ('fiscal', self._FY_DATA, False, self._FY_DATA),
            ('fiscal', {}, True, {}),
            ('ledger', ldg_values0, False, expect0),
            )
        msg = "Expected {}, field_name '{}', found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, values, first_run, expected in data:
                panel = self.fmf.panels[panel_name]
                self.db.populate_panel_values(panel_name, panel, values)
                result = self.db.collect_panel_values(panel)

                if first_run:
                    combobox = panel.GetChildren()[3]
                    self.assertEqual(2, combobox.Count)
                else:
                    for field_name, value in expected.items():
                        if field_name == 'start_of_fiscal_year':
                            field = str(result[field_name])
                        else:
                            field = result[field_name]

                        self.assertEqual(value, field, msg.format(
                            value, field_name, field))

    #@unittest.skip("Temporarily skipped")
    async def test__set_statusbar(self):
        """
        Test that the _set_statusbar method sends the error message
        to the log file and the status bar.
        """
        exp0 = ("Invalid widget type, found 'InvalidWidget' with value 10.",
                "Invalid widget type, found 'InvalidWidget' with value 10.")
        exp1 = ("Invalid widget type, found 'InvalidWidget'.",
                "Invalid widget type, found 'InvalidWidget', panel 'budget' "
                "widgets: () and ().")
        data = (
            ('InvalidWidget', " with value 10.", exp0),
            ('InvalidWidget', ", panel 'budget' widgets: () and ().", exp1),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for widget, add_msg, expected in data:
                self.fmf.statusbar_error = None
                self.db._set_statusbar(widget, add_msg)
                error = self.fmf.statusbar_error
                self.assertEqual(expected[0], error, msg.format(
                    expected[0], error))
                file_data = self.read_text_file(self.log_path)
                result = self.find_text(file_data, '_set_statusbar', 2,
                                        expected[1])
                self.assertIn(expected[1], result)

    #@unittest.skip("Temporarily skipped")
    def test__process_box_value(self):
        """
        Test that the _process_box_value method processes the values
        from both RadioBox and ComboBox widgets.
        """
        err_msg0 = "Expected a numeric value in field '{}' found {}."
        cb_choices = ['183-03 Jamál', "183-04 'Aẓamat", '183-05 Núr',
                      '183-06 Raḥmat', '183-07 Kalimát', '183-08 Kamál',
                      "183-09 Asmá'", "183-10 'Izzat", '183-11 Mashíyyat',
                      "183-12 'Ilm", '183-13 Qudrat', '183-14 Qawl',
                      '183-15 Masá’il', '183-16 Sharaf', '183-17 Sulṭán',
                      '183-18 Mulk', '183-00 Ayyám-i-Há', "183-19 'Alá'",
                      '184-01 Bahá', '184-02 Jalál', '184-03 Jamál']
        data = (
            ('RadioBox', '', ['LSA', 'Group'], '1', True, int),
            ('ComboBox', '', cb_choices, '10', True, int),
            ('RadioBox', 'test_name', ['LSA', 'Group'], 'qwerty', False,
             err_msg0.format('test_name', 'qwerty')),
            )
        msg = "Expected {}, found {}."

        for wgt_name, field_name, choices, value, valid, expected in data:
            obj = getattr(wx, wgt_name)(
                self.fmf, wx.ID_ANY, 'Locality Prefix (Month)',
                style=wx.RA_SPECIFY_ROWS, choices=choices)

            if valid:
                result = self.db._process_box_value(obj, field_name, value)
                self.assertIsInstance(result, expected, msg.format(
                    expected, result))
            else:
                with patch.object(self.db, '_mf', self.fmf):
                    result = self.db._process_box_value(obj, field_name, value)
                    self.assertIsNone(result, msg.format(None, result))
                    result = self.fmf.statusbar_warning
                    self.assertEqual(expected, result, msg.format(
                        expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_find_child_sets(self):
        """
        Test that the find_child_sets method correctly finds the children
        in the panel that have data.
        """
        data = (
            ('organization', 0, 6),
            ('budget', 0, 36),
            ('fiscal', 1, 4),
            ('monthly', 1, 7),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, none_sets, expected in data:
                panel = self.fmf.panels[panel_name]
                widget_sets = 0
                none_count = 0

                for w0, w1 in self.db.find_child_sets(panel):
                    self.assertIsNotNone(w0)
                    widget_sets += 1

                    if w1 is None:
                        none_count += 1

                self.assertEqual(expected, widget_sets, msg.format(
                    expected, widget_sets))
                self.assertEqual(none_sets, none_count, msg.format(
                    none_sets, none_count))

    #@unittest.skip("Temporarily skipped")
    def test__add_fiscal_year_choices(self):
        """
        Test that the _add_fiscal_year_choices method correctly adds the
        fiscal years to the ComboBox choices.
        """
        err_msg0 = "Can only pass the 'panel' or the 'w0' arguments."

        with patch.object(self.db, '_mf', self.fmf):
            fiscal_panel = self.fmf.panels['fiscal']
            combobox = fiscal_panel.GetChildren()[3]
            w0 = ('ComboBox', 'choose_fiscal_year', combobox)
            data = (
                (fiscal_panel, None, True, 2),
                (None, w0, True, 2),
                (fiscal_panel, w0, False, err_msg0),
                )
            msg = "Expected {}, found {}."

            for panel, w0, valid, expected in data:
                if valid:
                    self.db._add_fiscal_year_choices(panel=panel, w0=w0)
                    count = combobox.Count
                    self.assertEqual(expected, count, msg.format(
                        expected, count))
                else:
                    with self.assertRaises(AssertionError) as cm:
                        self.db._add_fiscal_year_choices(panel=panel, w0=w0)

                    result = str(cm.exception)
                    self.assertEqual(expected, result, msg.format(
                        expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__value_to_db(self):
        """
        Test that the _value_to_db method correctly converts a currency
        value to an integer.
        """
        data = (
            (1952.14, True, True, 195214),
            (195214, True, False, '195214'),
            ('1952.14', True, False, '195214'),
            ('-1952.14', True, False, '-195214'),
            ('+1952.14', True, False, '195214'),
            ('$1952.14', True, False, '195214'),
            ('=1952.14', True, False, '195214'),
            ('1952.14', True, True, 195214),
            (badidatetime.datetime(183, 3, 5), False, False,
             '0183-03-05T00:00:00'),
            (datetime.datetime(2026, 5, 1), False, False,
             '2026-05-01 00:00:00'),
            (wx.DateTime(1, 5, 2026), False, False,
             'Mon 01 Jun 2026 12:00:00 AM EDT'),
            (' 123456 ', False, False, '123456'),
            )
        msg = "Expected {} with financial {}, to_int {}, found {}."

        for value, financial, to_int, expected in data:
            result = self.db._value_to_db(value, financial=financial,
                                          to_int=to_int)
            self.assertEqual(expected, result, msg.format(
                expected, financial, to_int, result))

    #@unittest.skip("Temporarily skipped")
    def test__panel_to_financial_panel(self):
        """
        Test that the _panel_to_financial_panel method correctly converts
        an unformatted financial panel value to a formatted value.
        """
        data = (
            (195214, '1952.14'),
            (1952.14, '1952.14'),
            ('195214', '1952.14'),
            ('1952.14', '1952.14'),
            ('qwerty', ''),
            )
        msg = "Expected {}, found {}."

        for value, expected in data:
            result = self.db._panel_to_financial_panel(value)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__str_to_int(self):
        """
        Test that the _str_to_int method correctly converts a numeric string
        to an integer.
        """
        err_msg0 = "Expected a numeric value in field '{{}}' found {}."
        data = (
            (195215, (195215, None)),
            ('195215', (195215, None)),
            ('1952.15', (195215, None)),
            ('qwerty', (None, err_msg0.format('qwerty'))),
            )
        msg = "Expected {}, found {}."

        for value, expected in data:
            result = self.db._str_to_int(value)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_isfloat(self):
        """
        Test that the isfloat method correctly determines if a text value
        is a floating point number.
        """
        data = (
            ('1952.14', True),
            ('195214', False),
            ('qwerty', False),
            )
        msg = "Expected {}, found {}."

        for value, expected in data:
            result = self.db.isfloat(value)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_convert_db_to_panel(self):
        """
        Test that the convert_db_to_panel method correctly converts DB
        row data into panel data.
        """
        row0 = ((1, 183, badidatetime.date(183, 7, 19),
                 'Test OCS Contribution', 1, 1, '', None, None, None, None,
                 1, 5000), [])
        expect0 = copy.deepcopy(self._LDG_DATA)
        expect0['panel']['transaction_id'] = str(row0[0][0])
        expect0['panel']['date'] = row0[0][2]
        expect0['panel']['memo'] = row0[0][3]
        expect0['transaction']['contribution'] = True
        expect0['reference']['ocs'] = True
        expect0['income']['local_fund'] = True
        expect0['income']['amount'] = row0[0][12]
        row1 = ((3, 183, badidatetime.date(183, 8, 7), 'Test OCS Distribution',
                 2, 1, '', 1, 5000, None, None, None, None), [])
        expect1 = copy.deepcopy(self._LDG_DATA)
        expect1['panel']['transaction_id'] = str(row1[0][0])
        expect1['panel']['date'] = row1[0][2]
        expect1['panel']['memo'] = row1[0][3]
        expect1['transaction']['distribution'] = True
        expect1['reference']['ocs'] = True
        expect1['bank']['deposit'] = True
        expect1['bank']['amount'] = row1[0][8]
        row2 = ((4, 183, badidatetime.date(183, 8, 7), 'Test CoH Distribution',
                 2, 4, '2026-08-06', 1, 5000, 2, 5000, None, None), [])
        expect2 = copy.deepcopy(self._LDG_DATA)
        expect2['panel']['transaction_id'] = str(row2[0][0])
        expect2['panel']['date'] = row2[0][2]
        expect2['panel']['memo'] = row2[0][3]
        expect2['transaction']['distribution'] = True
        expect2['reference']['deposit'] = True
        expect2['reference']['number'] = row2[0][6]
        expect2['bank']['deposit'] = True
        expect2['bank']['amount'] = row2[0][8]
        expect2['coh']['disbursement'] = True
        expect2['coh']['amount'] = row2[0][10]
        row3 = ((5, 183, badidatetime.date(183, 8, 10), 'Test expenses',
                 3, 1, '', 2, 30000, None, None, None, None),
                [(5, 'national_baháí_fund', 20000),
                 (5, 'regional_baháí_council', 10000)])
        expect3 = copy.deepcopy(self._LDG_DATA)
        expect3['panel']['transaction_id'] = str(row3[0][0])
        expect3['panel']['date'] = row3[0][2]
        expect3['panel']['memo'] = row3[0][3]
        expect3['transaction']['expense'] = True
        expect3['reference']['ocs'] = True
        expect3['bank']['withdrawal'] = True
        expect3['bank']['amount'] = row3[0][8]
        expect3['expenses']['national_baháí_fund'] = row3[1][0][2]
        expect3['expenses']['regional_baháí_council'] = row3[1][1][2]
        expect3['panel']['total_expenses'] = row3[1][0][2] + row3[1][1][2]

        data = (
            (row0, expect0),
            (row1, expect1),
            (row2, expect2),
            (row3, expect3),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = self.fmf.panels['ledger']

            for row, expected in data:
                # Set the panel empty
                self.db.clear_panel('ledger', panel)
                items = self.db.convert_db_to_panel(row)
                self.db.populate_panel_values('ledger', panel, items)
                result = self.db.collect_panel_values(panel)
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    @unittest.skip("Temporarily skipped")
    def test_get_prev_and_next(self):
        """
        Test that the get_prev_and_next method
        """
        pass

    #@unittest.skip("Temporarily skipped")
    def test_populate_fiscal_panel(self):
        """
        Test that the populate_fiscal_panel method sets the correct
        ColorCheckBox with the current, work_on, or audit values.
        """
        data = (
            (183, (True, True, False)),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for year, expected in data:
                self.db.populate_fiscal_panel(year)
                fiscal = self.fmf.panels['fiscal']
                index = -1

                for w0, w1 in self.db.find_child_sets(fiscal):
                    if w1 is not None and w1[0] == 'ColorCheckBox':
                        index += 1
                        result = w1[2].GetValue()
                        self.assertEqual(expected[index], result, msg.format(
                            expected[index], result))

    #@unittest.skip("Temporarily skipped")
    def test_set_fiscal_panel(self):
        """
        Test that the set_fiscal_panel method sets the correct ColorCheckBox
        with the current, work_on, or audit values.
        """
        data = (
            (True, False, False, ('current_fiscal_year', True)),
            (False, True, False, ('work_on_this_fiscal_year', True)),
            (False, False, True, ('audit_complete', True)),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for current, work_on, audit, expected in data:
                self.db.set_fiscal_panel(current, work_on, audit)
                fiscal = self.fmf.panels['fiscal']

                for w0, w1 in self.db.find_child_sets(fiscal):
                    if w0[1] == expected[0]:
                        result = w1[2].GetValue()
                        self.assertEqual(expected[1], result, msg.format(
                            expected[1], result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_monthly_panel(self):
        """
        Test that the update_monthly_panel method updates the monthly panel.
        """
        insert_data = {'treasurer': 'Joe Schmo', 'month_index': 0,
                       'cal_year_month': (183, 3), 'participation': 5,
                       'outstanding': '1000', 'coh': '000', 'locality': 0,
                       'membership': 20}
        await self.db.cache.update(self.db._T_MONTHLY,
                                   {'year': 183, 'data': insert_data})
        widget_data = {'treasurer_this_month': 'Joe Schmo', 'month_index': 0,
                       'participation': '5', 'outstanding_bills': '10.00',
                       'end_of_month_cash_on_hand': '0.00',
                       'locality_prefix_month': 0,
                       'total_membership_this_month': '20'}
        data = (
            ('183-03 Jamál', widget_data),
            )
        msg = "Expected '{}', field_name '{}', found '{}'."

        with patch.object(self.db, '_mf', self.fmf):
            for date_str, expected in data:
                self.db.update_monthly_panel(date_str)
                monthly = self.fmf.panels['monthly']

                for w0, w1 in self.db.find_child_sets(monthly):
                    if w1 is not None:
                        for field_name, value in expected.items():
                            if w0[1] == field_name:
                                if field_name == 'locality_prefix_month':
                                    result = w0[2].GetSelection()
                                else:
                                    result = w1[2].GetValue()

                                self.assertEqual(value, result, msg.format(
                                    value, field_name, result))

    #@unittest.skip("Temporarily skipped")
    async def test_ledger_search_panel(self):
        """
        Test that the ledger_search_panel method returns data for either the
        LedgerDataEntry or SearchResult panels.

        *** TODO *** Insert test records, don't rely on the DB records.
        """
        # Insert test data
        await self._insert_transactions()


        # Test 1
        test_data0 = {'panel.transaction_id': '', 'panel.date': '',
                      'panel.memo': '', 'transaction.contribution': False,
                      'transaction.distribution': False,
                      'transaction.expense': False, 'transaction.other': False,
                      'reference.ocs': False, 'reference.check': False,
                      'reference.receipt': False, 'reference.deposit': False,
                      'reference.number': '', 'bank.deposit': False,
                      'bank.withdrawal': False, 'coh.replenishment': False,
                      'coh.disbursement': False, 'income.local_fund': False,
                      'income.contributed_expense': False,
                      'income.other': False}
        # Test 2
        test_data1 = copy.deepcopy(test_data0)
        test_data1['panel.transaction_id'] = 1
        expect1 = [((1, 183, badidatetime.date(183, 9, 6),
                     'Test OCS Contribution', 1, 1, '', None, None, None, None,
                     1, 5000, 0,), [])]
        # Test 3
        test_data2 = copy.deepcopy(test_data0)
        test_data2['transaction.contribution'] = True
        expect2 = [((1, 183, badidatetime.date(183, 9, 6),
                     'Test OCS Contribution', 1, 1, '', None, None, None, None,
                     1, 5000, 0), []),
                   ((2, 183, badidatetime.date(183, 8, 5),
                     'Test OCS Contribution', 1, 1, '', None, None, None, None,
                     1, 2000, 0), [])]
        # Test 4
        test_data3 = copy.deepcopy(test_data0)
        test_data3['panel.date'] = badidatetime.date(183, 8, 10)
        expect3 = [((3, 183, badidatetime.date(183, 8, 10), 'Test expenses', 3,
                     1, '', 2, 30000, None, None, None, None, 0),
                    [(3, 'national_baháí_fund', 20000),
                     (3, 'regional_baháí_council', 10000)])]

        data = (
            (test_data0, []),
            (test_data1, expect1),
            (test_data2, expect2),
            (test_data3, expect3),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            panel = SearchDialog(self.fmf)

            for test_data, expected in data:
                self.db.populate_panel_values('search_dialog', panel,
                                              test_data)
                items = self.db.ledger_search_panel(panel)

                if items:
                    # Remove the ctime
                    result = [((item[0][:-1]), item[1]) for item in items]
                else:
                    result = items

                self.assertEqual(expected, result, msg.format(
                    expected, result))
