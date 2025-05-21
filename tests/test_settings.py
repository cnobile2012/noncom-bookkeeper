# -*- coding: utf-8 -*-
#
# test/test_settings.py
#
__docformat__ = "restructuredtext en"

import unittest
import wx


from src.settings import FiscalSettings, Paths
from src.custom_widgits import EVT_COLOR_CHECKBOX

from . import FakeFrame, FakePanel, check_flag


class TestFiscalSettings(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.app = wx.App(False)

    def tearDown(self):
        hasattr(self, 'frame') and self.frame.Destroy()
        self.app.Destroy()

    def create_fiscal_settings_instance(self):
        self.frame = FakeFrame()
        fiscal_panel = FakePanel(self.frame)
        self.frame.panels = {'fiscal': fiscal_panel}
        panel = wx.Panel(self.frame)  # Need to mimic the actual design.
        return FiscalSettings(panel)

    def fire_event(self, widget, evt_type):
        event = wx.CommandEvent(evt_type.typeId, widget.GetId())
        event.SetEventObject(widget)
        wx.PostEvent(widget, event)
        wx.Yield()

    #@unittest.skip("Temporarily skipped")
    def test_constructor(self):
        """
        Test that the constructor creates three widgets.
        """
        expected_result = 3
        widgets = [
            var for var in FiscalSettings.create_display.__code__.co_varnames
            if var.startswith('widget')]
        expect = len(widgets)
        msg = f"Should be '{expected_result}' widgets expect '{expect}'"
        self.assertEqual(expected_result, expect, msg)

    #@unittest.skip("Temporarily skipped")
    def test_background_color(self):
        """
        Test that the color for the property background_color is returned.
        """
        fs = self.create_fiscal_settings_instance()
        expected_result = fs._bg_color
        bg_color = fs.background_color
        msg = f"Expected {expected_result} expect {bg_color}"
        self.assertEqual(expected_result, bg_color, msg)

    #@unittest.skip("Temporarily skipped")
    def test_enable_current(self):
        """
        Test that the enable_current event method enables a widget in
        another panel.
        """
        msg = "Expected '{}', found '{}'."
        fs = self.create_fiscal_settings_instance()
        # Test for normal operation.
        fiscal_panel = self.frame.panels['fiscal']
        fp_widget = fiscal_panel.FindWindowByName('current')
        state = fp_widget.GetEnableState()
        self.assertFalse(state, msg.format(False, state))
        # Test for event operation.
        widget = fs.FindWindowByName('current_state')
        self.fire_event(widget, EVT_COLOR_CHECKBOX)
        state = fp_widget.GetEnableState()
        self.assertTrue(state, msg.format(True, state))


class TestPaths(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)

    #@unittest.skip("Temporarily skipped")
    def test_constructor(self):
        """
        Test that the constructor creates eight widgets.
        """
        expected_result = 9
        widgets = [var for var in Paths.create_display.__code__.co_varnames
                   if var.startswith('widget')]
        expect = len(widgets)
        msg = f"Expected '{expected_result}' widgets expect '{expect}'"
        self.assertEqual(expected_result, expect, msg)

    #@unittest.skip("Temporarily skipped")
    def test_background_color(self):
        """
        Test that the color for the property background_color is returned.
        """
        app = wx.App()
        paths = Paths(FakeFrame(None))
        expected_result = paths._bg_color
        bg_color = paths.background_color
        msg = f"Expected {expected_result} expect {bg_color}"
        self.assertEqual(expected_result, bg_color, msg)
