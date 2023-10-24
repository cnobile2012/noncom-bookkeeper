#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# test/test_config.py
#
__docformat__ = "restructuredtext en"

import unittest

try:
    from unittest.mock import patch
except:
    from mock import patch

from . import log, initial_log_message, get_path
from src.config import (TomlMetaData, TomlPanelConfig, TomlAppConfig,
                        TomlCreatePanel)
from src.ncb import CheckPanelConfig, CheckAppConfig


RUN_FLAG = {'TestTomlMetaData': False, 'TestTomlPanelConfig': False,
            'TomlAppConfig': False, 'TomlCreatePanel': False}


def check_flag(name):
    if not RUN_FLAG[name]:
        initial_log_message("Start logging for %s", name)
        RUN_FLAG[name] = True


class BaseTest(unittest.TestCase):
    _cpd = CheckPanelConfig()
    _cad = CheckAppConfig()

    def __init__(self, name):
        super().__init__(name)
        self._cpd.has_valid_data


class TestTomlMetaData(BaseTest):
    _NUM_PANELS = 3

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.tmd = TomlMetaData()
        self.NUM_MONTHS = {'bahai': 20, 'generic': 12}.get(
            self.tmd.config_type)

    #@unittest.skip("Temporarily skipped")
    def test_panels_property(self):
        """
        Test that the panel property returns a list of list containing
        [[Menu Name, Toml File Name],...]
        """
        log.debug("Testing test_panels_property")
        panels = self.tmd.panels
        num_panels = len(panels)
        msg = f"There should be {self._NUM_PANELS}, found {num_panels}."
        self.assertEquals(self._NUM_PANELS, num_panels, msg)
        num_in_panel = 2
        msg = (f"There should be 2 strings in each panel object, found {{}} "
               f"in panel {{}}.")

        for panel in panels:
            num = len(panel)
            self.assertEquals(num_in_panel, num, msg.format(num, panel))

    #@unittest.skip("Temporarily skipped")
    def test_months_property(self):
        """
        Test that there are the correct number of months.
        """
        months = self.tmd.months
        num_months = len(months)
        msg = f"There should be {self.NUM_MONTHS}, found {num_months}."
        self.assertEquals(self.NUM_MONTHS, num_months, msg)

    #@unittest.skip("Temporarily skipped")
    def test_locale_prefix_property(self):
        """
        Test that the locality prefix is correct.

        Note: This is only tested for the Bahá'í app.
        """
        if self.tmd.config_type == 'bahai':
            locale_prefix = self.tmd.locale_prefix
            found_num_prefix = len(locale_prefix)
            should_be_num = 2
            msg = f"There should be {should_be_num}, found {found_num_prefix}."
            self.assertEquals(should_be_num, found_num_prefix, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_12_normal_property(self):
        """
        Test that the font is correct.
        """
        font_12_normal = self.tmd.font_12_normal
        # Test points
        should_be_points = 12
        found_points = font_12_normal[0]
        msg = f"The points should be {should_be_points}, found {found_points}."
        self.assertEquals(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_NORMAL'
        found_weight = font_12_normal[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEquals(should_be_weight, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_12_bold_property(self):
        """
        Test that the font is correct.
        """
        font_12_bold = self.tmd.font_12_bold
        # Test points
        should_be_points = 12
        found_points = font_12_bold[0]
        msg = f"The points should be {should_be_points}, found {found_points}."
        self.assertEquals(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_BOLD'
        found_weight = font_12_bold[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEquals(should_be_weight, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_10_normal_property(self):
        """
        Test that the font is correct.
        """
        font_10_normal = self.tmd.font_10_normal
        # Test points
        should_be_points = 10
        found_points = font_10_normal[0]
        msg = f"The points should be {should_be_points}, found {found_points}."
        self.assertEquals(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_NORMAL'
        found_weight = font_10_normal[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEquals(should_be_weight, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_10_bold_property(self):
        """
        Test that the font is correct.
        """
        font_10_bold = self.tmd.font_10_bold
        # Test points
        should_be_points = 10
        found_points = font_10_bold[0]
        msg = f"The points should be {should_be_points}, found {found_points}."
        self.assertEquals(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_BOLD'
        found_weight = font_10_bold[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEquals(should_be_weight, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_get_font(self):
        """
        Test that the proper font is returned.
        """
        fonts = {'font_12_normal': (12, 'FONTWEIGHT_NORMAL'),
                 'font_12_bold': (12, 'FONTWEIGHT_BOLD'),
                 'font_10_normal': (10, 'FONTWEIGHT_NORMAL'),
                 'font_10_bold': (10, 'FONTWEIGHT_BOLD')}
        msg = "The font {} should be {}, found {}. "

        for font_type, values in fonts.items():
            font = self.tmd.get_font(font_type)
            self.assertEquals(values[0], font[0],
                              msg.format('points', values[0], font[0]))
            self.assertEquals(values[1], font[3],
                              msg.format('weight', values[0], font[3]))


class TestTomlPanelConfig(BaseTest):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.tpc = TomlPanelConfig()

    #@unittest.skip("Temporarily skipped")
    def test_is_valid_property(self):
        """
        Test that the is_valid property returns a boolean for normal
        operation.
        """
        ret = self.tpc.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'user_config_fullpath',
                  '/tmp/fake_file.toml')
    def test_is_valid_property_user_bad_path(self):
        """
        Test that the is_valid property returns a boolean for a bad
        path in the `user_config_fullpath` property.
        """
        ret = self.tpc.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'user_config_dir', get_path())
    def test_is_valid_property_user_unparsable(self):
        """
        Test that the is_valid property returns a boolean for an
        unparsable Toml file in the `user_config_fullpath` property.
        """
        ret = self.tpc.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'local_config_fullpath',
                  '/tmp/fake_file.toml')
    def test_is_valid_property_local_bad_path(self):
        """
        Test that the is_valid property returns a boolean for a bad
        path in the `local_config_fullpath` property.
        """
        ret = self.tpc.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, '_LOCAL_CONFIG', get_path())
    def test_is_valid_property_local_unparsable(self):
        """
        Test that the is_valid property returns a boolean for an
        unparsable Toml file in the `local_config_fullpath` property.
        """
        ret = self.tpc.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)


class TestTomlAppConfig(BaseTest):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        self.tac = TomlAppConfig()



