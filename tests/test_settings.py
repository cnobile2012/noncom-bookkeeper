# -*- coding: utf-8 -*-
#
# test/test_settings.py
#
__docformat__ = "restructuredtext en"

import unittest
import wx


from src.settings import Paths

from . import log, check_flag


class FakeFrame(wx.Frame):

    def __init__(self, parent):
        super().__init__(parent)


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
        app = wx.App()
        paths = Paths(FakeFrame(None))
        should_be_num = 8
        widgets = [var for var in Paths.create_display.__code__.co_varnames
                   if var.startswith('widget')]
        found = len(widgets)
        msg = f"Should be '{should_be_num}' widgets found '{found}'"
        self.assertEqual(should_be_num, found, msg)

    #@unittest.skip("Temporarily skipped")
    def test_background_color(self):
        """
        Test that the color for the property background_color is returned.
        """
        app = wx.App()
        self.paths = Paths(FakeFrame(None))
        should_be = self.paths._bg_color
        bg_color = self.paths.background_color
        msg = f"Should be {should_be} found {bg_color}"
        self.assertEqual(should_be, bg_color, msg)
