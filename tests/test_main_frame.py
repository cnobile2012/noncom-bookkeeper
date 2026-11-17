# -*- coding: utf-8 -*-
#
# tests/test_main_frame.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import unittest

from src.main_frame import MainFrame

from . import BASE_DIR, log, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestMainFrame(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self.mf = MainFrame()

    def tearDown(self):
        self.mf = None
        self.tac = None

    @unittest.skip("Temporarily skipped")
    async def test_start(self):
        """
        Test that the start method 
        """
        await self.mf.start()

    @unittest.skip("Temporarily skipped")
    def test_on_timer_closure(self):
        """
        Test that the on_timer_closure method 
        """

    @unittest.skip("Temporarily skipped")
    def test__reset_panel(self):
        """
        Test that the _reset_panel method 
        """

    @unittest.skip("Temporarily skipped")
    def test_load_panels(self):
        """
        Test that the load_panels method 
        """

    @unittest.skip("Temporarily skipped")
    def test_set_size(self):
        """
        Test that the set_size method 
        """

    @unittest.skip("Temporarily skipped")
    def test_setup_resize_event(self):
        """
        Test that the setup_resize_event method 
        """

    @unittest.skip("Temporarily skipped")
    def test_on_size(self):
        """
        Test that the on_size method 
        """

    @unittest.skip("Temporarily skipped")
    def test_on_idle(self):
        """
        Test that the on_idle method 
        """

    @unittest.skip("Temporarily skipped")
    def test_panels_setter_and_getter(self):
        """
        Test that the panels property 
        """

    #@unittest.skip("Temporarily skipped")
    def test_frame(self):
        """
        Test that the frame property returns the frame object.
        """
        frame = self.mf.frame
        self.assertEqual(self.mf, frame)

    @unittest.skip("Temporarily skipped")
    def test_sizer(self):
        """
        Test that the sizer property returns the container sizer.
        """
        sizer = self.mf.sizer
        self.assertEqual(self.mf.container_sizer, sizer)

    @unittest.skip("Temporarily skipped")
    def test_statusbar_warning(self):
        """
        Test that the statusbar_warning property 
        """

    @unittest.skip("Temporarily skipped")
    def test_statusbar_error(self):
        """
        Test that the statusbar_error property 
        """

    @unittest.skip("Temporarily skipped")
    def test_statusbar_message(self):
        """
        Test that the statusbar_message property 
        """

    @unittest.skip("Temporarily skipped")
    def test_add_status(self):
        """
        Test that the add_status method 
        """

    @unittest.skip("Temporarily skipped")
    def test_remove_status(self):
        """
        Test that the remove_status method 
        """
