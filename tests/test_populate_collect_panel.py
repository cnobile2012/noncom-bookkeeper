# -*- coding: utf-8 -*-
#
# tests/test_populate_collect_panel.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import unittest
import datetime
import badidatetime

from unittest.mock import patch

from src.bases import BaseGenerated
from src.config import TomlPanelConfig
from src.utilities import StoreObjects
#from src.bahai_database import Database

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestPopulateCollect(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._tpc = TomlPanelConfig()
        self.log_path = os.path.join(self._tpc.user_log_fullpath, LOGFILE_NAME)
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

    @unittest.skip("Temporarily skipped")
    async def test_has_org_info_data(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test_has_budget_data(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test_open_ledger_entry(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__check_panels_for_entries(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test_collect_panel_values(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test_populate_panel_values(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__process_value(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__find_child_sets(self):
        """
        """
        pass

    @unittest.skip("Temporarily skipped")
    async def test__add_fiscal_year_choices(self):
        """
        """
        pass

    #@unittest.skip("Temporarily skipped")
    def test__value_to_db(self):
        """
        Test that the _value_to_db method correctly converts a currency
        value to an integer.
        """
        data = (
            (195214, True, '195214'),
            ('1952.14', True, '195214'),
            ('-1952.14', True, '-195214'),
            ('+1952.14', True, '195214'),
            ('$1952.14', True, '195214'),
            ('=1952.14', True, '195214'),
            (badidatetime.datetime(183, 3, 5), False, '0183-03-05T00:00:00'),
            (datetime.datetime(2026, 5, 1), False, '2026-05-01 00:00:00'),
            (wx.DateTime(1, 5, 2026), False,
             'Mon 01 Jun 2026 12:00:00 AM EDT'),
            (' 123456 ', False, '123456'),
            )
        msg = "Expected {}, found {}."

        for value, financial, expected in data:
            result = self.db._value_to_db(value, financial)
            self.assertEqual(expected, result, msg.format(expected, result))

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
            ('qwerty', (0, err_msg0.format('qwerty'))),
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

        for year, expected in data:
            with patch.object(self.db, '_mf', self.fmf):
                self.db.populate_fiscal_panel(year)
                fiscal = self.fmf.panels['fiscal']
                index = -1

                for w0, w1 in self.db._find_child_sets(fiscal):
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

        for current, work_on, audit, expected in data:
            with patch.object(self.db, '_mf', self.fmf):
                self.db.set_fiscal_panel(current, work_on, audit)
                fiscal = self.fmf.panels['fiscal']

                for w0, w1 in self.db._find_child_sets(fiscal):
                    if w0[1] == expected[0]:
                        result = w1[2].GetValue()
                        self.assertEqual(expected[1], result, msg.format(
                            expected[1], result))

    #@unittest.skip("Temporarily skipped")
    async def test_update_monthly_panel(self):
        """
        Test that the update_monthly_panel method updates the monthly panel.
        """
        insert_data = {'treasurer': 'Joe Schmo', 'month_of_year': 0,
                       'cal_year_month': (183, 3), 'participation': 5,
                       'outstanding': '1000', 'coh': '000', 'locality': 0,
                       'membership': 20}
        await self.db.cache.insert(self.db._T_MONTHLY, {'year': 183,
                                                        'data': insert_data})
        widget_data = {'treasurer_this_month': 'Joe Schmo', 'month_of_year': 0,
                       'participation': '5', 'outstanding_bills': '10.00',
                       'end_of_month_cash_on_hand': '0.00',
                       'locality_prefix_month': 0,
                       'total_membership_this_month': '20'}
        min_widget_data = {'treasurer_this_month': '', 'month_of_year': 1,
                           'participation': '', 'outstanding_bills': '',
                           'end_of_month_cash_on_hand': '',
                           'locality_prefix_month': 0,
                           'total_membership_this_month': ''}
        data = (
            ('183-03 Jamál', widget_data),
            #("183-04 ‘Aẓamat", min_widget_data)
            )
        msg = "Expected {}, field_name '{}', found '{}'."

        for date_str, expected in data:
            with patch.object(self.db, '_mf', self.fmf):
                self.db.update_monthly_panel(date_str)
                monthly = self.fmf.panels['monthly']

                for w0, w1 in self.db._find_child_sets(monthly):
                    if w1 is not None:
                        for field_name, value in expected.items():
                            if w0[1] == field_name:
                                if field_name == 'locality_prefix_month':
                                    result = w0[2].GetSelection()
                                else:
                                    result = w1[2].GetValue()

                                self.assertEqual(value, result, msg.format(
                                    value, field_name, result))
