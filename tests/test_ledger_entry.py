# -*- coding: utf-8 -*-
#
# tests/test_ledger_entry.py
#
__docformat__ = "restructuredtext en"

import copy
import wx
import unittest
import types
import badidatetime

from unittest.mock import patch, MagicMock
from wx.lib.scrolledpanel import ScrolledPanel

from src.ledger_entry import (_CreateWidgets, LedgerDataEntry, SearchDialog,
                              SearchResult)
from src.utilities import StoreObjects
from src.custom_widgits import ColorCheckBox

from . import LOGFILE_NAME, check_flag, patchers
from .base_database_test import BaseAsyncTests
from .fixtures import FakeEvent


class CreateWidgetsPanel(ScrolledPanel, _CreateWidgets):

    def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
        super().__init__(parent, id, *args, **kwargs)
        self.w_fg_color = wx.Colour(50, 50, 204)     # Dark Blue
        self.gbs = wx.GridBagSizer(2, 2)


class Test_CreateWidgets(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self.cw = CreateWidgetsPanel(self.frame)

    def tearDown(self):
        self.cw = None

    #@unittest.skip("Temporarily skipped")
    def test__title_generator(self):
        """
        Test that the _title_generator method returns a generator of the
        title data.
        """
        data = [
            ['Transaction Type', 4, 0, 'top', 2, True],
            ['Entry Reference', 4, 1, 'top', 2, True],
            ['Cash in Bank', 2, 2, 'top', 2, True],
            ['Cash on Hand', 2, 2, 'top', 2, True],
            ['Income', 3, 2, 'top', 2, True],
            ['Expenses', 0, 0, '', 2, False],
            ["Local Bahá'í Expenses", 0, 5, 'bottom', 1, False],
            ["National Bahá'í Funds", 0, 11, 'bottom', 1, False],
            ['Continental and International Funds', 0, 11, 'bottom', 1, False],
            ['Regional Funds', 0, 3, 'bottom', 1, False],
            ['Area Funds', 0, 1, 'bottom', 1, False],
            ]
        msg = "Expected '{}', found '{}'."
        items = []

        with patch.object(self.db, 'mf', self.frame):
            gen = self.cw._title_generator()

            while gen:
                values = []

                try:
                    for item in next(gen):
                        values.append(item)

                    items.append(values)
                except StopIteration:
                    break

        for idx, title in enumerate(data):
            result = items[idx]
            self.assertEqual(title, result, msg.format(items, result))

    #@unittest.skip("Temporarily skipped")
    def test__label_generator(self):
        """
        Test that the _label_generator method returns a generator of the
        label data.
        """
        data = [
            ['transaction', 'Contribution:', 'Distribution:', 'Expense:',
             'Other:'],
            ['$reference', 'OCS:', 'Check:', 'Receipt:', 'Deposit:',
             'Number:'],
            ['$bank', 'Deposit:', 'Withdrawal:', '@Amount:', '%Balance:'],
            ['$coh', 'Replenishment:', 'Disbursement:', '@Amount:',
             '%Balance:'],
            ['$income', 'Local Fund:', 'Contributed Expense:', 'Other:',
             '@Amount:', '%Balance:']
            ]
        msg = "Expected '{}', found '{}'."
        items = []

        with patch.object(self.db, 'mf', self.frame):
            gen = self.cw._label_generator()

            while gen:
                values = []

                try:
                    for item in next(gen):
                        values.append(item)

                    items.append(values)
                except StopIteration:
                    break

        for idx, title in enumerate(data):
            result = items[idx]
            self.assertEqual(title, result, msg.format(items, result))

    #@unittest.skip("Temporarily skipped")
    def test__make_heading(self):
        """
        Test that the _make_heading method returns a wx button object and
        the GridBagSizer position.
        """
        data = (
            ('Transaction Type', 0, 2, True, (wx.Button, 2)),
            ('Entry Reference', 2, 2, True, (wx.Button, 4)),
            ('Expenses', 4, 2, False, (types.NoneType, 6)),
            ('Area Funds', 6, 1, False, (types.NoneType, 8)),
            )
        msg = "Expected '{}', found '{}'."

        for title, o_pos, span, btn, expected in data:
            obj, pos = self.cw._make_heading(title, o_pos, span=span, btn=btn)
            wdg, new_pos = expected
            self.assertIsInstance(obj, wdg, msg.format(obj, wdg))
            self.assertEqual(new_pos, pos)

    #@unittest.skip("Temporarily skipped")
    def test__next_title_and_labels(self):
        """
        Test that the _next_title_and_labels method returns the title
        and it's labels.
        """
        data = (
            (['Transaction Type', 4, 0, 'top', 2, True],
             ['transaction', 'Contribution:', 'Distribution:', 'Expense:',
              'Other:']),
            (['Entry Reference', 4, 1, 'top', 2, True],
             ['$reference', 'OCS:', 'Check:', 'Receipt:', 'Deposit:',
              'Number:']),
            (['Cash in Bank', 2, 2, 'top', 2, True],
             ['$bank', 'Deposit:', 'Withdrawal:', '@Amount:', '%Balance:']),
            (['Cash on Hand', 2, 2, 'top', 2, True],
             ['$coh', 'Replenishment:', 'Disbursement:', '@Amount:',
              '%Balance:']),
            (['Income', 3, 2, 'top', 2, True],
             ['$income', 'Local Fund:', 'Contributed Expense:', 'Other:',
              '@Amount:', '%Balance:']),
            (['Expenses', 0, 0, '', 2, False], ['&expenses']),
            (["Local Bahá'í Expenses", 0, 5, 'bottom', 1, False],
             ['&local_baháí_expenses', '@Administration:', '@Education:',
              '@Proclamation:', '@Scolarships:', '@Teaching:']),
            (["National Bahá'í Funds", 0, 11, 'bottom', 1, False],
             ['&national_baháí_funds', "@National Bahá'í Fund:",
              "@Bahá'í Chair for World Peace - Reserved Fund:",
              "@Persian Bahá'í Media Service Fund (Payam-e-Doost):",
              '@House of Worship Campus Reserves Fund:',
              '@Wilmette Institute - Unrestricted Contribution:',
              '@Humanitarian Relief Fund - In USA:',
              "@US Bahá'í Archives Renovation Fund:",
              "@Bahá'í Election Convention Contributions:",
              '@Bosch Facilities Recovery Fund:',
              '@Institute Properties Resurve Fund:',
              '@Legal Defense for the Refugees in Turkey:']),
            (['Continental and International Funds', 0, 11, 'bottom', 1,
              False],
             ['&continental_and_international_funds',
              "@International Bahá'í Fund:", "@Bahá'í Development Fund:",
              '@International Endowment Fund:', "@Continental Bahá'í Fund:",
              '@National House of Worship - Canada:',
              "@Shrine of 'Abdu'l-Bahá:",
              '@Humanitarian Relief Fund (World Center):',
              '@Persian Relief Fund (World Center):',
              '@International Temples Fund:', '@Asian Continental Board:',
              '@US Deputization Fund - International Pioneering:']),
            (['Regional Funds', 0, 3, 'bottom', 1, False],
             ['&regional_funds', "@Regional Bahá'í Council:",
              '@Deputization Fund:', '@Regional Facilities Fund:']),
            (['Area Funds', 0, 1, 'bottom', 1, False],
             ['&area_funds', '@Area Teaching Committee:']),
            )
        msg = "Expected '{}', found '{}'."
        title_gen = self.cw._title_generator()
        label_gen = self.cw._label_generator()
        result = self.cw._next_title_and_labels(title_gen, label_gen)
        idx = 0

        while None not in result:
            expected = data[idx]
            self.assertEqual(expected, result, msg.format(expected, result))
            result = self.cw._next_title_and_labels(title_gen, label_gen)
            idx += 1
            if idx >= len(data): break


class TestLedgerDataEntry(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self.frame.create_panels()

        with patch.object(self.db, 'mf', self.frame):
            self.panel = self.frame.panels.get('ledger')

    def tearDown(self):
        self.panel = None

    #@unittest.skip("Temporarily skipped")
    def test_ledger_labels(self):
        """
        Test that the ledger_labels property returns the ledger categories
        and fields.
        """
        data = (
            ('panel', ['transaction_id', 'date', 'memo', 'total_expenses']),
            ('transaction', ['contribution', 'distribution', 'expense',
                             'other']),
            ('reference', ['ocs', 'check', 'receipt', 'deposit', 'number']),
            ('bank', ['deposit', 'withdrawal', 'amount', 'balance']),
            ('coh', ['replenishment', 'disbursement', 'amount', 'balance']),
            ('income', ['local_fund', 'contributed_expense', 'other', 'amount',
                        'balance']),
            ('expenses', ['administration', 'education', 'proclamation',
                          'scolarships', 'teaching', 'national_baháí_fund',
                          'baháí_chair_for_world_peace_reserved_fund',
                          'persian_baháí_media_service_fund_payam_e_doost',
                          'house_of_worship_campus_reserves_fund',
                          'wilmette_institute_unrestricted_contribution',
                          'humanitarian_relief_fund_in_usa',
                          'us_baháí_archives_renovation_fund',
                          'baháí_election_convention_contributions',
                          'bosch_facilities_recovery_fund',
                          'institute_properties_resurve_fund',
                          'legal_defense_for_the_refugees_in_turkey',
                          'international_baháí_fund', 'baháí_development_fund',
                          'international_endowment_fund',
                          'continental_baháí_fund',
                          'national_house_of_worship_canada',
                          'shrine_of_abdul_bahá',
                          'humanitarian_relief_fund_world_center',
                          'persian_relief_fund_world_center',
                          'international_temples_fund',
                          'asian_continental_board',
                          'us_deputization_fund_international_pioneering',
                          'regional_baháí_council', 'deputization_fund',
                          'regional_facilities_fund',
                          'area_teaching_committee']),
            )
        msg = "Expected '{}', found '{}'."
        result = self.panel.ledger_labels

        for idx, (category, fields) in enumerate(result.items()):
            expect0, expect1 = data[idx]
            self.assertEqual(expect0, category, msg.format(expect0, category))
            self.assertEqual(expect1, fields, msg.format(expect1, fields))

    #@unittest.skip("Temporarily skipped")
    def test_button_save(self):
        """
        Test that the button_save method sets the save variable properly
        when a button is pressed.
        """
        msg = "Expected '{}', found '{}'."
        btn_panel = self.panel.GetChildren()[-1]
        save_btn = btn_panel.GetChildren()[0]
        self.assertIsInstance(save_btn, wx.Button, msg.format(
            save_btn, wx.Button))
        self.assertFalse(self.panel.save, msg.format(False, self.panel.save))
        event = wx.CommandEvent(wx.wxEVT_BUTTON, save_btn.GetId())
        save_btn.GetEventHandler().ProcessEvent(event)
        self.assertTrue(self.panel.save, msg.format(True, self.panel.save))

    #@unittest.skip("Temporarily skipped")
    def test_save_setter_and_getter(self):
        """
        Test that the save properties set and get the save value properly.
        """
        data = (
            (False, False, False),
            (True, False, True),
            #(False, True, False),  # Both tests fail when run with full suite.
            #(True, True, True),
            )
        msg = "Expected {} found {}"

        for set, dirty, expected in data:
            if dirty:
                self.panel.dirty = True

            self.panel.save = set
            result = self.panel.save
            self.assertEqual(expected, result, msg.format(expected, result))

            if dirty:
                e_msg = 'Saving data.'
                s_msg = self.db.mf.statusbar_message
                self.assertEqual(e_msg, s_msg, msg.format(e_msg, s_msg))

    #@unittest.skip("Temporarily skipped")
    def test_button_cancel(self):
        """
        Test that the button_cancel method cancels and exits the panel when
        the button is pressed.
        """
        msg = "Expected '{}', found '{}'."
        btn_panel = self.panel.GetChildren()[-1]
        cancel_btn = btn_panel.GetChildren()[1]
        self.assertIsInstance(cancel_btn, wx.Button, msg.format(
            cancel_btn, wx.Button))
        self.assertFalse(self.panel.cancel, msg.format(
            False, self.panel.cancel))
        event = wx.CommandEvent(wx.wxEVT_BUTTON, cancel_btn.GetId())
        cancel_btn.GetEventHandler().ProcessEvent(event)
        self.assertTrue(self.panel.cancel, msg.format(True, self.panel.cancel))

    #@unittest.skip("Temporarily skipped")
    def test_cancel_setter_and_getter(self):
        """
        Test that the cancel properties set and get the cancel value properly.
        """
        data = (
            (False, False, False),
            (True, False, True),
            #(False, True, False),  # Both tests fail when run with full suite.
            #(True, True, True),
            )
        msg = "Expected {} found {}"

        for set, dirty, expected in data:
            if dirty:
                self.panel.dirty = True

            self.panel.cancel = set
            result = self.panel.cancel
            self.assertEqual(expected, result, msg.format(expected, result))

            if dirty:
                e_msg = 'Restoring data.'
                s_msg = self.db.mf.statusbar_message
                self.assertEqual(e_msg, s_msg, msg.format(e_msg, s_msg))

    #@unittest.skip("Temporarily skipped")
    def test_reset_buttons(self):
        """
        Test that the reset_buttons method resets all the 'Clear' buttons
        on the ledger panel.
        """
        boxes = []

        for child in self.panel.GetChildren():
            if isinstance(child, ColorCheckBox):
                boxes.append(child)

        for box in boxes:
            self.assertFalse(box.GetValue())
            box.SetValue(True)
            self.assertTrue(box.GetValue())

        for ch in self.panel.GetChildren():
            if isinstance(ch, wx.Button) and ch.GetLabel() == '&Clear':
                event = wx.CommandEvent(wx.wxEVT_BUTTON, ch.GetId())
                event.SetEventObject(ch)
                ch.GetEventHandler().ProcessEvent(event)

        for box in boxes:
            self.assertFalse(box.GetValue())

    #@unittest.skip("Temporarily skipped")
    def test_search_box(self):
        """
        Test that the search_box method opens the search box when the
        'Search' button is pressed.
        """
        with patch.object(wx.Frame, "Show") as mock_show:
            btn = self.panel.FindWindowByLabel('Search')
            event = wx.CommandEvent(wx.wxEVT_BUTTON, btn.GetId())
            event.SetEventObject(btn)
            btn.GetEventHandler().ProcessEvent(event)
            mock_show.assert_called_once_with(True)
            self.assertIsInstance(self.panel.sd, SearchDialog)

    #@unittest.skip("Temporarily skipped")
    def test_on_expense_changed(self):
        """
        Test that the on_expense_changed method updates the "Total Expenses"
        field.
        """
        fields = {"national_baháí_fund": None,
                  "shrine_of_abdul_bahá": None,
                  "regional_baháí_council": None,
                  "total_expenses": None}
        names = tuple(fields.keys())

        for w0, w1 in self.db.find_child_sets(self.panel):
            name0, field_name, widget0 = w0

            if w1:
                name1, _, widget1 = w1

            if field_name in names:
                fields[field_name] = widget1

        data = (
            (names[0], '500.00', '500.00'),
            (names[1], '100.00', '600.00'),
            (names[2], '50.00', '650.00'),
            (names[1], '', '550.00'),
            )
        msg = "Expected {} found {}"
        total_expenses = fields["total_expenses"]

        for field, amount, balance in data:
            fields[field].SetValue(amount)
            self.assertEqual(balance, total_expenses.GetValue())

    #@unittest.skip("Temporarily skipped")
    async def test_on_arrow(self):
        """
        Test that the on_arrow method gets the next or previous transaction
        by the transaction ID.
        """
        await self.db.create_db()
        await self.insert_data()
        await self.db.cache.load()
        expect0 = copy.deepcopy(self._LDG_DATA)
        expect0['panel']['transaction_id'] = '5'
        expect0['panel']['date'] = badidatetime.date(183, 9, 8)
        expect0['panel']['memo'] = 'Test OCS Distribution Update'
        expect0['panel']['total_expenses'] = 0
        expect0['transaction']['distribution'] = True
        expect0['reference']['ocs'] = True
        expect0['bank']['deposit'] = True
        expect0['bank']['amount'] = 50000
        expect0['bank']['balance'] = 90000
        expect0['coh']['balance'] = 2500
        expect0['income']['balance'] = 7500
        expect1 = copy.deepcopy(self._LDG_DATA)
        expect1['panel']['transaction_id'] = '4'
        expect1['panel']['date'] = badidatetime.date(183, 9, 6)
        expect1['panel']['memo'] = 'Test expense'
        expect1['panel']['total_expenses'] = 25000
        expect1['transaction']['expense'] = True
        expect1['reference']['ocs'] = True
        expect1['bank']['withdrawal'] = True
        expect1['bank']['amount'] = 25000
        expect1['bank']['balance'] = 90000
        expect1['coh']['balance'] = 2500
        expect1['income']['balance'] = 7500
        expect1['expenses']['national_baháí_fund'] = 15000
        expect1['expenses']['shrine_of_abdul_bahá'] = 10000
        data = (
            (FakeEvent(), 'right', '6', expect0),
            (FakeEvent(), 'left', '6', expect0),
            (FakeEvent(), 'left', '5', expect1),
            )
        msg = "Expected {} found {}"

        with patch.object(self.db, 'mf', self.frame):
            panel = self.frame.panels.get('ledger')

            for event, fe_value, fp_value, expected in data:
                event.direction = fe_value
                panel.widget_02.SetValue(fp_value)
                panel.on_arrow(event)
                result = self.db.collect_panel_values(panel)
                self.assertEqual(expected, result, msg.format(
                    expected, result))
                self.db.clear_panel(panel)

        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    def test_background_color(self):
        """
        Test that the background_color property returns the background color.
        """
        color = self.panel.background_color
        self.assertIsInstance(color, wx.Colour)


class TestSearchDialog(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self.frame.create_panels()

    def _setup_panel(self):
        panel = SearchDialog(self.frame)
        parent = MagicMock()
        parent.Parent.bg_color = wx.Colour(10, 20, 30)
        parent.Parent.w_fg_color = wx.Colour(200, 210, 220)
        panel.parent = parent
        return panel

    #@unittest.skip("Temporarily skipped")
    def test_button_search_with_rows_shows_result_dialog(self):
        """
        Test that the button_search method shows the dialog with rows of data.
        """
        panel = self._setup_panel()
        now = badidatetime.datetime.now()
        rows = [((5, 183, badidatetime.date(183, 8, 10), 'Test expenses',
                 3, 1, '', 2, 30000, None, None, None, None, 0, now, now),
                [(5, 183, 'national_baháí_fund', 20000),
                 (5, 183, 'regional_baháí_council', 10000)])]
        event = MagicMock()

        with (patch.object(self.db, 'ledger_search_panel',
                           return_value=rows) as mock_search,
              patch('src.ledger_entry.SearchResult') as mock_dlg_cls,
              patch.object(panel, 'warn_text') as mock_warn):
            panel.button_search(event)

        mock_search.assert_called_once_with(panel)
        mock_dlg_cls.assert_called_once_with(
            panel.parent, "Choose Search Results", "Search Results", rows=rows,
            bg_color=panel.parent.Parent.bg_color,
            fg_color=panel.parent.Parent.w_fg_color)
        self.assertIs(panel._dlg, mock_dlg_cls.return_value)
        panel.parent.Hide.assert_called_once()
        mock_dlg_cls.return_value.ShowModal.assert_called_once()
        mock_warn.SetLabel.assert_not_called()
        event.Skip.assert_called_once()
        # Needed to keep the Borg state from affecting other tests.
        self.db.clear_state()

    #@unittest.skip("Temporarily skipped")
    def test_button_search_no_rows_shows_warning(self):
        """
        Test that the button_search method shows warning without rows of data.
        """
        panel = self._setup_panel()
        event = MagicMock()

        with (patch.object(self.db, 'ledger_search_panel', return_value=[]),
              patch('src.ledger_entry.SearchResult') as mock_dlg_cls,
              patch.object(panel, 'warn_text') as mock_warn,
              patch.object(panel, 'Layout') as mock_layout):
            panel.button_search(event)

        mock_dlg_cls.assert_not_called()
        panel.parent.Hide.assert_not_called()
        mock_warn.SetLabel.assert_called_once_with("Found no results.")
        mock_warn.Wrap.assert_called_once_with(250)
        mock_warn.Show.assert_called_once()
        mock_layout.assert_called_once()
        event.Skip.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_button_cancel(self):
        """
        Test that the button_cancel method closes the search dialog.
        """
        with patch.object(self.db, 'mf', self.frame):
            panel = self.frame.panels.get('ledger')

        with (patch.object(wx.Frame, "Show") as mock_show,
              patch.object(wx.Frame, "Destroy") as mock_destroy):
            btn = panel.FindWindowByLabel('Search')
            event = wx.CommandEvent(wx.wxEVT_BUTTON, btn.GetId())
            event.SetEventObject(btn)
            btn.GetEventHandler().ProcessEvent(event)
            mock_show.assert_called_once_with(True)
            self.assertIsInstance(panel.sd, SearchDialog)
            # Click cancel button
            cnl = wx.FindWindowById(wx.ID_CANCEL, panel.sd)
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId, cnl.GetId())
            evt.SetEventObject(cnl)
            cnl.GetEventHandler().ProcessEvent(evt)
            mock_destroy.assert_called_once()
            self.assertIsNone(panel.sd)
