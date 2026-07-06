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

    #@unittest.skip("Temporarily skipped")
    async def test_collect_panel_values(self):
        """
        Test that the collect_panel_values method collects data from
        panels and converts it to appropreate values for the database.
        """
        org_data = {'locality_prefix': 0, 'locale_name': 'New York',
                    'total_membership': '20', 'treasurer': 'Joe Schmo',
                    'start_of_fiscal_year': badidatetime.date(183, 3, 5),
                    'location_city_name': 'New York', 'iana_name': None,
                    'latitude': None, 'longitude': None}
        bgt_data = {'cash_in_bank': '200000', 'ocs_holdings': '10000',
                    'total_outstanding_bills_previous_year': '000',
                    'total_membership_beginning_of_year': '20',
                    'monetary_contributions': '200000'}
        mth_data = {'month_index': '183-03 Jamál', 'participation': '',
                    'outstanding_bills': '', 'end_of_month_cash_on_hand': '',
                    'total_membership_this_month': '',
                    'treasurer_this_month': '', 'locality_prefix_month': 0}
        mth_values = dict(mth_data)
        mth_values['month_index'] = 0
        fy_data = {'fiscal_year_choice': 0, 'current_fiscal_year': False,
                   'work_on_this_fiscal_year': False, 'audit_complete': False}
        data = (
            ('organization', 9, org_data, org_data),
            ('budget', 36, bgt_data, bgt_data),
            ('monthly', 7, mth_values, mth_data),
            ('fiscal', 4, fy_data, fy_data),
            )
        msg = "Expected {}, found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, count, values, expected in data:
                panel = self.fmf.panels[panel_name]
                self.db.populate_panel_values(panel_name, panel, values)
                result = self.db.collect_panel_values(panel)
                self.assertEqual(count, len(result))

                for field_name, value in expected.items():
                    self.assertEqual(value, result[field_name], msg.format(
                        value, result[field_name]))

    #@unittest.skip("Temporarily skipped")
    async def test_populate_panel_values(self):
        """
        Test that the populate_panel_values method populates the panel
        with the database values.
        """
        org_data = {'locale_name': 'New York', 'locality_prefix': 0,
                    'location_city_name': 'New York',
                    'start_of_fiscal_year': '0183-03-05',
                    'total_membership': '20', 'treasurer': 'Joe Schmo'}
        bgt_data = {'cash_in_bank': '200000', 'ocs_holdings': '10000',
                    'total_outstanding_bills_previous_year': '000',
                    'total_membership_beginning_of_year': '20',
                    'monetary_contributions': '200000'}
        fy_data = {'fiscal_year_choice': 0, 'current_fiscal_year': False,
                   'work_on_this_fiscal_year': False, 'audit_complete': False}
        data = (
            ('organization', org_data, False, True),
            ('budget', bgt_data, False, True),
            ('fiscal', fy_data, False, True),
            ('fiscal', {}, True, True),
            )
        msg = "Expected {}, field_name '{}', found {}."

        with patch.object(self.db, '_mf', self.fmf):
            for panel_name, values, first_run, valid in data:
                panel = self.fmf.panels[panel_name]

                if valid:
                    self.db.populate_panel_values(panel_name, panel, values)
                    result = self.db.collect_panel_values(panel)

                    if first_run:
                        combobox = panel.GetChildren()[3]
                        self.assertEqual(2, combobox.Count)
                    else:
                        for field_name, value in values.items():
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
    def test__find_child_sets(self):
        """
        Test that the _find_child_sets method correctly finds the children
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

                for w0, w1 in self.db._find_child_sets(panel):
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

        with patch.object(self.db, '_mf', self.fmf):
            for current, work_on, audit, expected in data:
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
        insert_data = {'treasurer': 'Joe Schmo', 'month_index': 0,
                       'cal_year_month': (183, 3), 'participation': 5,
                       'outstanding': '1000', 'coh': '000', 'locality': 0,
                       'membership': 20}
        await self.db.cache.insert(self.db._T_MONTHLY, {'year': 183,
                                                        'data': insert_data})
        widget_data = {'treasurer_this_month': 'Joe Schmo', 'month_index': 0,
                       'participation': '5', 'outstanding_bills': '10.00',
                       'end_of_month_cash_on_hand': '0.00',
                       'locality_prefix_month': 0,
                       'total_membership_this_month': '20'}
        min_widget_data = {'treasurer_this_month': '', 'month_index': 1,
                           'participation': '', 'outstanding_bills': '',
                           'end_of_month_cash_on_hand': '',
                           'locality_prefix_month': 0,
                           'total_membership_this_month': ''}
        data = (
            ('183-03 Jamál', widget_data),
            #("183-04 ‘Aẓamat", min_widget_data)
            )
        msg = "Expected '{}', field_name '{}', found '{}'."

        with patch.object(self.db, '_mf', self.fmf):
            for date_str, expected in data:
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
