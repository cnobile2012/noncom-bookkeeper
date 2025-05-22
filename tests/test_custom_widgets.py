# -*- coding: utf-8 -*-
#
# tests/test_custom_widgits.py
#
__docformat__ = "restructuredtext en"

import unittest
import wx

from badidatetime import date, MONTHNAMES

from src.custom_widgits import (
    ordered_month, EVT_BADI_DATE_CHANGED, BadiDateChangedEvent,
    EVT_COLOR_CHECKBOX, ColorCheckBoxEvent)

from . import FakeFrame, FakePanel, check_flag


class TestFunctions(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)

    #@unittest.skip("Temporarily skipped")
    def test_ordered_month(self):
        """
        Test that the ordered_month function returns a dict of month
        number and name.
        """
        months = ordered_month()
        msg = "Expected {}, found {}."
        expected_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                          12, 13, 14, 15, 16, 17, 18, 0, 19]
        expected_month = MONTHNAMES

        for idx, (order, month) in enumerate(months.items()):
            expect_ord = expected_order[idx]
            self.assertEqual(expect_ord, order, msg.format(expect_ord, order))
            expect_mon = expected_month[idx]
            self.assertEqual(expect_mon, month, msg.format(expect_mon, month))


class TestBadiDateChangedEvent(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.app = wx.App(False)
        self.frame = FakeFrame()
        fake_panel = FakePanel(self.frame)
        self.bdate = date(182, 4, 6)
        self.bdce = BadiDateChangedEvent(fake_panel, self.bdate)

    #@unittest.skip("Temporarily skipped")
    def test_constructor(self):
        """
        Test that the __init__ constructor sets the Badi date correctly.
        """
        msg = f"Expected {self.bdate}, found {self.bdce._bdate}."
        self.assertEqual(self.bdate, self.bdce._bdate, msg)

    #@unittest.skip("Temporarily skipped")
    def test_GetBadiDate(self):
        """
        Test that the GetBadiDate method returns the Badi date.
        """
        bdate = self.bdce.GetBadiDate()
        msg = f"Expected {self.bdate}, found {bdate}."
        self.assertEqual(self.bdate, bdate, msg)


# class TestBadiCalendarPopup(unittest.TestCase):

#     def __init__(self, name):
#         super().__init__(name)

#     def setUp(self):
#         check_flag(self.__class__.__name__)
#         self.app = wx.App(False)
#         self.frame = FakeFrame()
#         self.panel = FakePanel(self.frame)

#     #@unittest.skip("Temporarily skipped")
#     def test_on_paint_border(self):
#         """
#         Test that the on_paint_border method sets the pen, brush, and
#         rectangle correctly.
#         """
#         expected_result = 0
#         widget = self.panel.FindWindowByName('test_popup')
#         # dc = wx.PaintDC(widget.panel)
#         # print(dc.GetPen())

#         # widget.on_paint_border(None)
#         # dc = wx.PaintDC(widget.panel)
#         # print(dc.GetPen())

#         # msg = f"Should be '{expected_result}' widgets expect '{expect}'"
#         # self.assertEqual(expected_result, expect, msg)
