# -*- coding: utf-8 -*-
#
# test/test_settings.py
#
__docformat__ = "restructuredtext en"

import unittest

from . import check_flag
from src.ncb import CheckPanelConfig, CheckAppConfig


class TestCheckPanelConfig(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.cpc = CheckPanelConfig()

    def test_has_valid_data(self):
        """
        Test that the config data is valid. This is a quick tests since the
        internals of the is_valid property is tested elsewhere.
        """
        ret = self.cpc.has_valid_data
        msg = f"Should be True found {ret}"
        self.assertTrue(ret, msg)


class TestCheckAppConfig(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.cac = CheckAppConfig()

    def test_has_valid_data(self):
        """
        Test that the config data is valid. This is a quick tests since the
        internals of the is_valid property is tested elsewhere.
        """
        ret = self.cac.has_valid_data
        msg = f"Should be True found {ret}"
        self.assertTrue(ret, msg)
