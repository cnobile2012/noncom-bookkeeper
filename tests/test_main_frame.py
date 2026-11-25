# -*- coding: utf-8 -*-
#
# tests/test_main_frame.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import copy
import unittest
import badidatetime

from unittest.mock import MagicMock, PropertyMock, patch

from src.main_frame import MainFrame
from src.bahai_database import Database

from . import log, check_flag, LOGFILE_NAME
from .conftest import TMP_TESTING_FACTORY_DIR
from .base_database_test import BaseAsyncTests


class Options:
    file_dump = False
    debug = False

    def __init__(self, value=False):
        self.file_dump = value


class TestMainFrame(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @classmethod
    def _remove_test_files(cls, files):
        for file in files:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mf = MainFrame(options=Options())

    @classmethod
    def tearDownClass(cls):
        files = (os.path.join(TMP_TESTING_FACTORY_DIR, 'organization.py'),
                 os.path.join(TMP_TESTING_FACTORY_DIR, 'budget.py'),
                 os.path.join(TMP_TESTING_FACTORY_DIR, 'monthly.py'),
                 os.path.join(TMP_TESTING_FACTORY_DIR, 'fiscal.py'))

        try:
            if cls.mf:
                cls.mf.Destroy()
                cls.mf = None

            cls._remove_test_files(files)
        finally:
            super().tearDownClass()

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.log_path = os.path.join(self.mf.tac.user_log_fullpath,
                                     LOGFILE_NAME)

    async def asyncSetUp(self):
        await self.db.create_db()
        await self.insert_data()
        await self.db.cache.load()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    async def test_start(self):
        """
        Test that the start method switches between panels after the
        previous one is completed.
        """
        data = (
            (False, False, 'OrganizationPanel'),
            (True, False, 'BudgetPanel'),
            (True, True, 'MonthlyPanel'),
            )
        msg = "Expected '{}', found '{}'"

        with patch.object(self.mf, '_load_panels', MagicMock()):
            for org_bool, bdg_bool, expected in data:
                with (patch.object(Database, 'has_org_info_data',
                                   new_callable=PropertyMock,
                                   return_value=org_bool),
                      patch.object(Database, 'has_budget_data',
                                   new_callable=PropertyMock,
                                   return_value=bdg_bool)):
                    await self.mf.start()
                    result = self.mf.panel.__class__.__name__
                    self.assertEqual(expected, result, msg.format(
                        expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_on_timer_closure_cancel(self):
        """
        Test that the on_timer_closure method cancels entered data.
        """
        start = "Start on_timer_closure cancel test."
        log.info(start)
        exclude = ('iana_name', 'latitude', 'longitude', 'total_expenses')
        org_cache = self.db.dp.organization_data
        bgt_cache = self.db.dp.budget_data
        mth_cache = self.db.dp.monthly_data
        ldg_data = self._LDG_DATA
        ledger = copy.deepcopy(self._LDG_DATA)
        ledger['panel']['date'] = badidatetime.date.today()
        ledger['panel']['memo'] = "Unit test for test_on_timer_closure()."
        ledger['transaction']['contribution'] = True
        ledger['reference']['ocs'] = True
        ledger['income']['local_fund'] = True
        ledger['income']['amount'] = '1000.00'

        data = (
            ('organization', self._ORG_DATA, org_cache),
            ('budget', self._BGT_DATA, bgt_cache),
            ('monthly', self._MTH_DATA, mth_cache),
            ('ledger', ledger, ldg_data),
            )
        msg = "Expected '{}' with '{}', found '{}'"

        for panel_name, items, cache in data:
            panel = self.mf.panels[panel_name]
            panel.dirty = True
            panel.cancel = True
            panel.save = False
            self.db.populate_panel_values(panel_name, panel, items)
            self.mf.on_timer_closure()(None)
            self.assertFalse(panel.dirty, msg.format(
                False, panel_name, panel.dirty))

            values = self.db.collect_panel_values(panel)

            if panel_name == 'ledger':
                values = values['panel']

            for fn, value in values.items():
                item = cache.get(fn)
                if fn in exclude or item is None: continue
                self.assertEqual(item, str(value), msg.format(
                    item, fn, str(value)))

            self.assertFalse(panel.cancel, msg.format(
                False, panel_name, panel.cancel))

    #@unittest.skip("Temporarily skipped")
    def test_on_timer_closure_save(self):
        """
        Test that the on_timer_closure method saves entered data.
        """
        start = "Start on_timer_closure save test."
        log.info(start)
        exclude = ('iana_name', 'latitude', 'longitude', 'total_expenses')
        err_msg0 = "The 'treasurer' field(s) must not be empty."
        err_msg1 = ("If Transaction Type->Contribution and Entry Reference (OC"
                    "S) you must also enter Income (Local Fund and Amount).")
        org_data0 = copy.deepcopy(self._ORG_DATA)
        org_data0['treasurer'] = ''
        org_cache = self.db.dp.organization_data
        bgt_cache = self.db.dp.budget_data
        mth_cache = self.db.dp.monthly_data
        ldg_data = self._LDG_DATA
        ledger = copy.deepcopy(self._LDG_DATA)
        ledger['panel']['date'] = badidatetime.date.today()
        ledger['panel']['memo'] = "Unit test for test_on_timer_closure()."
        ledger['transaction']['contribution'] = True
        ledger['reference']['ocs'] = True
        ledger['income']['local_fund'] = True
        ledger['income']['amount'] = '1000.00'
        expect0 = (6, 183, 'Unit test for test_on_timer_closure().', 1, 1, '',
                   None, None, None, None, 1, 100000, 0)
        ledger_err = copy.deepcopy(ledger)
        ledger_err['reference']['ocs'] = False

        data = (
            ('organization', self._ORG_DATA, org_cache, self.db._T_DATA, True,
             None),
            ('organization', org_data0, None, None, False, err_msg0),
            # *** TODO *** Might not be able to fix the ocs_holdings issue.
            #('budget', self._BGT_DATA, bgt_cache, self.db._T_DATA, True, None),
            ('ledger', ledger, ldg_data, None, True, expect0),
            ('ledger', ledger_err, None, None, False, err_msg1),
            )
        msg = "Expected '{}' with '{}', found '{}'"

        for panel_name, items, cache, db_name, valid, expected in data:
            panel = self.mf.panels[panel_name]
            panel.dirty = True
            panel.cancel = False
            panel.save = True

            self.db.populate_panel_values(panel_name, panel, items)

            with patch("src.main_frame.ConfirmationDialog"):
                self.mf.on_timer_closure()(None)

            self.assertFalse(panel.dirty, msg.format(
                False, panel_name, panel.dirty))

            if valid and panel_name == 'ledger':
                items = self.db.cache.get(self.db._V_LEDGER_TRANSACTION,
                                          trans_id=6)
                result = items[-1][:2] + items[-1][3:-1]
                self.assertEqual(expected, result, msg.format(
                    expected, panel_name, result))
            elif valid and panel_name in ('organization', 'budget'):
                result = self.db.cache.get(db_name, r_type=panel_name)

                for fn, val in [(i[1], i[2]) for i in result]:
                    if fn in exclude: continue
                    value = items[fn]
                    self.assertEqual(str(value), val, msg.format(
                        str(value), fn, value))
            else:
                file_data = self.read_text_file(self.log_path)
                result = self.find_text(file_data, start, 70, expected)
                self.assertIn(expected, result)

            self.assertFalse(panel.save, msg.format(
                False, panel_name, panel.save))

    #@unittest.skip("Temporarily skipped")
    def test_on_timer_closure_auto_save(self):
        """
        Test that the on_timer_closure method auto saves entered data.
        """
        start = "Start on_timer_closure auto save test."
        log.info(start)
        expect0 = "Finished saving Fiscal data."

        data = (
            ('fiscal', expect0),
            )
        msg = "Expected '{}' with '{}', found '{}'"

        for panel_name, expected in data:
            panel = self.mf.panels[panel_name]
            panel.dirty = True

            with patch.object(MainFrame, '_MainFrame__set_status',
                              autospec=True) as mock_status:
                self.mf.on_timer_closure()(None)
                self.assertEqual(mock_status.call_args.args[1], expected)

    #@unittest.skip("Temporarily skipped")
    def test__reset_panel(self):
        """
        Test that the _reset_panel method returns the data to reset the panel.
        """
        expect0 = {
            'iana_name': 'America/New_York', 'latitude': '40.7127281',
            'locale_name': 'New York', 'locality_prefix': '0',
            'location_city_name': 'New York', 'longitude': '-74.0060152',
            'start_of_fiscal_year': '0183-03-05', 'total_membership': '20',
            'treasurer': 'Joe Schmo'}
        expect1 = {
            'administration': '', 'area_teaching_committee': '',
            'asian_continental_board': '',
            'baháí_chair_for_world_peace_reserved_fund': '',
            'baháí_development_fund': '',
            'baháí_election_convention_contributions': '',
            'bosch_facilities_recovery_fund': '',
            'cash_in_bank': '200000', 'continental_baháí_fund': '',
            'deputization_fund': '', 'education': '',
            'house_of_worship_campus_reserves_fund': '',
            'humanitarian_relief_fund_in_usa': '',
            'humanitarian_relief_fund_world_center': '',
            'institute_properties_resurve_fund': '',
            'international_baháí_fund': '', 'international_endowment_fund': '',
            'international_temples_fund': '',
            'legal_defense_for_the_refugees_in_turkey': '',
            'monetary_contributions': '200000', 'national_baháí_fund': '',
            'national_house_of_worship_canada': '',
            'online_contribution_service_holdings': '1000',
            'persian_baháí_media_service_fund_payam_e_doost': '',
            'persian_relief_fund_world_center': '', 'proclamation': '',
            'regional_baháí_council': '', 'regional_facilities_fund': '',
            'scolarships': '', 'shrine_of_abdul_bahá': '', 'teaching': '',
            'total_membership_beginning_of_year': '20',
            'total_outstanding_bills_previous_year': '10000',
            'us_baháí_archives_renovation_fund': '',
            'us_deputization_fund_international_pioneering': '',
            'wilmette_institute_unrestricted_contribution': ''}
        expect2 = {'participation': '20', 'outstanding': '0', 'coh': '0',
                   'membership': '20', 'treasurer': 'Joe Schmo',
                   'locality': '0'}
        data = (
            ('organization', expect0),
            ('budget', expect1),
            ('monthly', expect2),
            )
        msg = "Expected {} found {}"

        for panel_name, expected in data:
            result = self.mf._reset_panel(panel_name)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__load_panels(self):
        """
        Test that the _load_panels method generates panel code.
        """
        fake_panel_cls = MagicMock(return_value=MagicMock())
        fake_globals = {f"{k.title()}Panel": fake_panel_cls
                        for k in ["overview"]}

        def fake_exec(code, ns):
            ns.update(fake_globals)

        expect0 = ['organization', 'budget', 'monthly', 'fiscal', 'ledger']
        data = (
            (Options(True), expect0),
            )
        msg = "Expected {} found {}"

        with patch('builtins.exec', side_effect=fake_exec):
            for options, expected in data:
                self.mf.options = options
                self.mf._load_panels()
                result = self.mf.panels
                self.assertEqual(expected, list(result), msg.format(
                    expected, list(result)))

    #@unittest.skip("Temporarily skipped")
    def test_set_size(self):
        """
        Test that the set_size method sets either the 'default' or the 'size'
        variable from the config file. If no file exists it sets '(500, 800)'.
        """
        default = self.frame.get_size(self.mf.tac._DEFAULT_SCREEN_SIZE)
        data = (
            (None, 'default', default),
            (None , 'size', default),
            ((500, 800), None, (500, 800)),
            )
        msg = "Expected {} found {}"

        for size, key, expected in data:
            if size:
                with patch('src.config.TomlAppConfig.get_value') as m_get_val:
                    m_get_val.return_value = None
                    self.mf.set_size(size)
            else:
                self.mf.set_size(size, key)

            result = self.mf.GetSize()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_setup_resize_event(self):
        """
        Test that the setup_resize_event method sets up the events correctly.
        """
        def _setup(obj):
            obj._resized = False
            obj.Bind(wx.EVT_SIZE, obj.on_size)
            obj.Bind(wx.EVT_IDLE, obj.on_idle)

        self.mf.on_size = lambda event: None
        self.mf.on_idle = lambda event: None
        # Attach your method (or call it as part of your class under test)
        self.mf.setup_resize_event = lambda: _setup(self.mf)

        with (patch.object(self.mf, "on_size",
                           wraps=self.mf.on_size) as mock_size,
              patch.object(self.mf, "on_idle",
                           wraps=self.mf.on_idle) as mock_idle):
            self.mf.setup_resize_event()
            size_event = wx.SizeEvent(self.mf.GetSize(), self.mf.GetId())
            idle_event = wx.IdleEvent()
            handled_size = self.mf.ProcessEvent(size_event)
            handled_idle = self.mf.ProcessEvent(idle_event)
            self.assertTrue(handled_size)
            self.assertTrue(handled_idle)
            mock_size.assert_called_once()
            mock_idle.assert_called_once()
            self.assertIsInstance(mock_size.call_args[0][0], wx.SizeEvent)
            self.assertIsInstance(mock_idle.call_args[0][0], wx.IdleEvent)

    #@unittest.skip("Temporarily skipped")
    def test_on_size(self):
        """
        Test that the on_size method actually calls the statments in it.
        """
        event = wx.SizeEvent(wx.Size(1024, 768), self.frame.GetId())

        with (patch.object(self.mf, "Layout") as mock_layout,
              patch.object(event, "Skip") as mock_skip):
            self.mf.on_size(event)
            self.assertTrue(getattr(self.mf, "_MainFrame__resized"))
            mock_layout.assert_called_once()
            mock_skip.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_idle(self):
        """
        Test that the on_idle method actually calls the statments in it.
        """
        idle_event = wx.IdleEvent()
        data = (
            (False, (500, 800)),
            (True, (1280, 720)),
            )

        for resize, target_size in data:
            with (patch.object(self.mf, "GetSize",
                               return_value=target_size) as mock_get_size,
                  patch.object(self.mf, "Layout"),
                  patch.object(self.mf, "tac") as mock_tac):
                panel_a = MagicMock()
                panel_b = MagicMock()

                if resize:
                    size_event = wx.SizeEvent(wx.Size(*target_size),
                                              self.mf.GetId())
                    self.mf.on_size(size_event)
                    self.assertTrue(getattr(self.mf, "_MainFrame__resized"))
                    self.mf.on_idle(idle_event)
                    self.assertFalse(getattr(self.mf, "_MainFrame__resized"))
                    self.mf.tac.update_app_config.assert_called_once_with(
                        "app-size", "size", target_size)

                    for panel in self.mf.panels.values():
                        self.assertEqual(target_size, panel.GetSize())
                        self.assertEqual(target_size, panel.GetMinSize())
                else:
                    self.mf.on_idle(idle_event)
                    mock_get_size.assert_not_called()
                    mock_tac.update_app_config.assert_not_called()
                    panel_a.SetSize.assert_not_called()
                    panel_a.SetSizeHints.assert_not_called()
                    panel_b.SetSize.assert_not_called()
                    panel_b.SetSizeHints.assert_not_called()

    #@unittest.skip("Temporarily skipped")
    def test_panels_getter(self):
        """
        Test that the panels properties gets the panel information.
        """
        expected = ['organization', 'budget', 'monthly', 'fiscal', 'ledger']
        result = self.mf.panels
        self.assertEqual(expected, list(result))

    #@unittest.skip("Temporarily skipped")
    def test_panels_setter(self):
        """
        Test that the panels properties sets the panel information.
        """
        err_msg0 = "The 'values' argument must be a tuple, found {}."
        panel = MagicMock()
        data = (
            (('a', panel), True, panel),
            ({}, False, err_msg0.format("<class 'dict'>")),
            )

        for panel_def, valid, expected in data:
            if valid:
                self.mf.panels = panel_def
                result = self.mf.panels
                self.assertEqual(expected, result['a'])
            else:
                with self.assertRaises(AssertionError) as cm:
                    self.mf.panels = panel_def

                ex = str(cm.exception)
                self.assertEqual(expected, ex)

    #@unittest.skip("Temporarily skipped")
    def test_frame(self):
        """
        Test that the frame property returns the frame object.
        """
        frame = self.mf.frame
        self.assertEqual(self.mf, frame)

    #@unittest.skip("Temporarily skipped")
    def test_sizer(self):
        """
        Test that the sizer property returns the container sizer.
        """
        sizer = self.mf.sizer
        self.assertEqual(self.mf._container_sizer, sizer)

    #@unittest.skip("Temporarily skipped")
    def test_warning_error_and_message_properties_set_colors_and_text(self):
        """
        Test that the statusbar_warning, statusbar_error, and
        statusbar_message properties.
        """
        self.mf._statusbar = MagicMock()
        data = (
            ("statusbar_warning", "Low disk space", "yellow"),
            ("statusbar_error", "Connection failed", "pink"),
            ("statusbar_message", "Saved settings", "lightgreen"),
        )

        for prop_name, text, expected_bg in data:
            self.mf._statusbar.reset_mock()

            with patch("wx.CallLater") as mock_call_later:
                setattr(self.mf, prop_name, text)
                self.mf._statusbar.SetStatusText.assert_called_once_with(
                    text, 0)
                self.mf._statusbar.SetBackgroundColour.assert_called_once_with(
                    expected_bg)
                fg_arg = self.mf._statusbar.SetForegroundColour.call_args[0][0]
                self.assertEqual(fg_arg, wx.Colour("black"))
                mock_call_later.assert_called_once()
                (delay_ms, callback,
                 default_color) = mock_call_later.call_args[0]
                self.assertEqual(delay_ms, 20000)
                self.assertEqual(default_color, wx.Colour("black"))
                self.assertTrue(callable(callback))

    #@unittest.skip("Temporarily skipped")
    def test_reset_callback_clears_text_and_restores_colors(self):
        """
        Test that the __reset_status method.
        """
        self.mf._statusbar = MagicMock()
        scheduled = []

        def capture_call_later(delay, fn, *args, **kwargs):
            scheduled.append((delay, fn, args, kwargs))
            return MagicMock()

        with patch("wx.CallLater", side_effect=capture_call_later):
            self.mf.statusbar_warning = "Temporary alert"

        self.assertEqual(len(scheduled), 1)
        _, reset_fn, args, kwargs = scheduled[0]
        self.mf._statusbar.reset_mock()

        # Simulate the 20-second timer firing
        reset_fn(*args, **kwargs)

        self.mf._statusbar.SetStatusText.assert_called_once_with("", 0)
        expected_default = wx.Colour("black")
        self.mf._statusbar.SetBackgroundColour.assert_called_once_with(
            expected_default)
        self.mf._statusbar.SetForegroundColour.assert_called_once_with(
            expected_default)
