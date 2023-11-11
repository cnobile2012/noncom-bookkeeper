# -*- coding: utf-8 -*-
#
# test/test_settings.py
#
__docformat__ = "restructuredtext en"

import unittest

from . import log, check_flag
from src.ncb import CheckPanelConfig, CheckAppConfig


class TestCheckPanelConfig(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.cpc = CheckPanelConfig()

    def test_has_valid_data(self):
        """
        Test that the config data is valid.
        """





