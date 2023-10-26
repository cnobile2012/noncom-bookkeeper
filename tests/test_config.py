#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# test/test_config.py
#
__docformat__ = "restructuredtext en"

import os
import unittest

try:
    from unittest.mock import patch
except:
    from mock import patch

from . import log, initial_log_message, get_path
from src.config import (TomlMetaData, TomlPanelConfig, TomlAppConfig,
                        TomlCreatePanel)
from src.ncb import CheckPanelConfig, CheckAppConfig
#from src import Logger

#logger = Logger()
#logger.config(logger_name='debug', user_stdout=True)

RUN_FLAG = {'TestTomlMetaData': False, 'TestTomlPanelConfig': False,
            'TestTomlAppConfig': False, 'TestTomlCreatePanel': False}


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
    _TMP_USER_CONFIG_FILE = '/tmp/user_config.toml'

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.tpc = TomlPanelConfig()

    def tearDown(self):
        try:
            os.remove(self._TMP_USER_CONFIG_FILE)
        except FileNotFoundError:
            pass

    #@unittest.skip("Temporarily skipped")
    def test_is_valid_property(self):
        """
        Test that the is_valid property returns a True for normal operation.
        """
        ret = self.tpc.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_user_bad_path(self):
        """
        Test that the is_valid property returns a False for a bad path in
        the `user_config_fullpath` property.
        """
        ret = self.tpc.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_user_unparsable(self):
        """
        Test that the is_valid property returns a True for an unparsable
        Toml file in the `user_config_fullpath` property.

        Note: The is_valid will fix this issue so it will return a True.
        """
        # Create an unparsable file.
        with open(self._TMP_USER_CONFIG_FILE, 'w') as f:
            f.write('')

        ret = self.tpc.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'local_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_local_bad_path(self):
        """
        Test that the is_valid property returns a False for a bad path in
        the `local_config_fullpath` property.
        """
        ret = self.tpc.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, '_LOCAL_CONFIG', get_path())
    def test_is_valid_property_local_unparsable(self):
        """
        Test that the is_valid property returns a False for an unparsable
        Toml file in the `local_config_fullpath` property.
        """
        ret = self.tpc.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)


class TestTomlAppConfig(BaseTest):
    _TMP_USER_APP_FILE = '/tmp/user_app_config.toml'
    _TMP_UNWRITABE_PATH = '/invalid_test.toml'

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.tac = TomlAppConfig()

    def tearDown(self):
        try:
            os.remove(self._TMP_USER_APP_FILE)
        except FileNotFoundError:
            pass

    def create_config(self):
        self.tac.create_app_config()
        return self.tac.is_valid

    #@unittest.skip("Temporarily skipped")
    def test_is_valid_property(self):
        """
        Test that the is_valid property returns a boolean for normal
        operation.
        """
        ret = self.tac.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_is_valid_property_user_not_found(self):
        """
        Test that the is_valid property returns a boolean for a bad
        path in the `user_app_config_fullpath` property.
        """
        ret = self.tac.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_is_valid_property_user_unparsable(self):
        """
        Test that the is_valid property returns a boolean for a bad
        path in the `user_app_config_fullpath` property.
        """
        # Create an unparsable file.
        with open(self._TMP_USER_APP_FILE, 'w') as f:
            f.write('')

        ret = self.tac.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_create_app_config(self):
        """
        Test that the application config file is created.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        ret = self.create_config()
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)
        outer_key_list = ('app_size',)
        inner_key_list = ('default', 'size')
        key_msg = "Key '{}' does not exist"
        val_msg = "Value should be a list, found '{}'."

        for j, (outer_key, values) in enumerate(self.tac.app_config.items()):
            self.assertEquals(outer_key_list[j], outer_key,
                              key_msg.format(outer_key))

            for k, (inner_key, value) in enumerate(values.items()):
                self.assertEquals(inner_key_list[k], inner_key,
                                  key_msg.format(inner_key))
                self.assertTrue(isinstance(value, list), val_msg.format(value))

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_get_value(self):
        """
        Test that a value can be found.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        self.create_config()
        value = self.tac.get_value('app_size', 'default')
        msg = f"Value should be a list, found '{value}'."
        self.assertTrue(isinstance(value, list), msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_get_value_invalid_key(self):
        """
        Test that an invalid key is logged.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        self.create_config()
        invalid_key = 'invalid'

        with self.assertRaises(AssertionError) as cm:
            self.tac.get_value('app_size', invalid_key)

        ex = str(cm.exception)
        msg = f"The key '{invalid_key}' was found, {ex}"
        self.assertIn('invalid', ex, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_update_app_config(self):
        """
        Test that a value can be updated.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        self.create_config()
        # Test that the 'default' value is the default.
        value = self.tac.get_value('app_size', 'default')
        should_be = [530, 830]
        msg = f"Should be '{should_be}' found '{value}'."
        self.assertEqual(should_be, value, msg)

        # Test that the update works properly.
        changed_value = [600, 900]
        self.tac.update_app_config('app_size', 'default', changed_value)
        value = self.tac.get_value('app_size', 'default')
        msg = f"Should be '{changed_value}' found '{value}'."
        self.assertEqual(changed_value, value, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_update_app_config_key_not_found(self):
        """
        Test that a value for a new key gets added properly.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        self.create_config()
        # Test that the new key does not exist yet.
        new_key = 'test_key'

        with self.assertRaises(AssertionError) as cm:
            value = self.tac.get_value('app_size', new_key)

        ex = str(cm.exception)
        msg = f"The key '{new_key}' was found, {ex}"
        self.assertIn(new_key, ex, msg)

        # Test that the new key can be added and found.
        new_value = 'Test Value'
        self.tac.update_app_config('app_size', new_key, new_value)
        value = self.tac.get_value('app_size', new_key)
        msg = f"Should be '{new_value}' found '{value}'."
        self.assertEquals(new_value, value, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_USER_APP_FILE)
    def test_update_app_config_table_not_found(self):
        """
        Test that a value for a new table and key gets added properly.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        self.create_config()
        # Test that the new table is not found.
        new_table = 'new_table'
        new_key = 'test_key'

        with self.assertRaises(AssertionError) as cm:
            value = self.tac.get_value(new_table, new_key)

        ex = str(cm.exception)
        msg = f"The table '{new_table}' was found, {ex}"
        self.assertIn(new_table, ex, msg)

        # Test that the new table and key can be added and found.
        new_value = 'Test Value'
        self.tac.update_app_config(new_table, new_key, new_value)
        value = self.tac.get_value(new_table, new_key)
        msg = f"Should be '{new_value}' found '{value}'."
        self.assertEquals(new_value, value, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, 'user_app_config_fullpath',
                  _TMP_UNWRITABE_PATH)
    def test__write_file_open_failed(self):
        """
        Test that writing to a file fails when a unwritable path is provided.
        """
        with self.assertRaises(PermissionError) as cm:
            self.tac._write_file('Invalid path')

        ex = str(cm.exception)
        msg = (f"The file '{self._TMP_UNWRITABE_PATH}' could not be "
               f"written, {ex}")
        self.assertIn(self._TMP_UNWRITABE_PATH, ex, msg)



