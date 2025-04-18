# -*- coding: utf-8 -*-
#
# test/test_config.py
#
__docformat__ = "restructuredtext en"

import os
import unittest
import shutil

try:
    from unittest.mock import patch
except:
    from mock import patch

import tomlkit as tk

from . import log, check_flag
from src.config import (Settings, BaseSystemData, TomlMetaData,
                        TomlPanelConfig, TomlAppConfig, TomlCreatePanel)
from src.ncb import CheckPanelConfig, CheckAppConfig

#from src import Logger; Logger().config()


class TestSettings(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.set = Settings()

    #@unittest.skip("Temporarily skipped")
    def test_base_dir(self):
        """
        Test that this static method returns the base directory without
        instantiating the class.
        """
        path = Settings.base_dir()
        should_be = Settings._BASE_DIR
        msg = f"Path should be '{should_be}' found '{path}'."
        self.assertEqual(should_be, path, msg)

    #@unittest.skip("Temporarily skipped")
    def test_primary_developer(self):
        """
        Test that the primary developer is returned.
        """
        dev = self.set.primary_developer
        should_be_dev = self.set._DEVELOPERS[0]
        msg = f"Should be '{should_be_dev}' found '{dev}'"
        self.assertEqual(should_be_dev, dev, msg)

    #@unittest.skip("Temporarily skipped")
    def test_contributors(self):
        """
        Test that the contributors are returned.
        """
        # Test that a list is returned.
        cont = self.set.contributors(True)
        should_be_cont = self.set._DEVELOPERS
        msg = f"Should be '{should_be_cont}' found '{cont}'"
        self.assertEqual(should_be_cont, cont, msg)
        # Test that a srting is returned.
        cont = self.set.contributors()
        should_be_cont = ''.join([s+'\n' for s in self.set._DEVELOPERS]
                                 ).strip()
        msg = f"Should be '{should_be_cont}' found '{cont}'"
        self.assertEqual(should_be_cont, cont, msg)

    #@unittest.skip("Temporarily skipped")
    def test_logger_name(self):
        """
        Test that the data logger name is returned.
        """
        name = self.set.logger_name
        should_be_name = self.set._LOGGER_NAME
        msg = f"Should be '{should_be_name}' found '{name}'."
        self.assertEqual(should_be_name, name, msg)

    #@unittest.skip("Temporarily skipped")
    def test_logfile_name(self):
        """
        Test that the data logfile name is returned.
        """
        name = self.set.logfile_name
        should_be_name = self.set._LOGFILE_NAME
        msg = f"Should be '{should_be_name}' found '{name}'."
        self.assertEqual(should_be_name, name, msg)

    #@unittest.skip("Temporarily skipped")
    def test_data_file_name(self):
        """
        Test that the data file name is returned.
        """
        df = self.set.data_file_name
        should_be_df = self.set._DATA_FILE
        msg = f"Should be '{should_be_df}' found '{df}'."
        self.assertEqual(should_be_df, df, msg)

    #@unittest.skip("Temporarily skipped")
    def test_user_data_fullpath(self):
        """
        Test that the user data file path is returned.
        """
        fp = self.set.user_data_fullpath
        should_be_fp = os.path.join(self.set.user_data_dir,
                                    self.set.data_file_name)
        msg = f"Should be '{should_be_fp}' found '{fp}'."
        self.assertEqual(should_be_fp, fp, msg)

    #@unittest.skip("Temporarily skipped")
    def test_user_config_fullpath(self):
        """
        Test that the user config file path is returned.
        """
        fp = self.set.user_config_fullpath
        should_be_fp = os.path.join(self.set.user_config_dir,
                                    self.set._Settings__user_toml)
        msg = f"Should be '{should_be_fp}' found '{fp}'."
        self.assertEqual(should_be_fp, fp, msg)

    #@unittest.skip("Temporarily skipped")
    def test_user_app_config_fullpath(self):
        """
        Test that the user app config file path is returned.
        """
        fp = self.set.user_app_config_fullpath
        should_be_fp = os.path.join(self.set.user_config_dir,
                                    self.set._Settings__app_toml)
        msg = f"Should be '{should_be_fp}' found '{fp}'."
        self.assertEqual(should_be_fp, fp, msg)

    #@unittest.skip("Temporarily skipped")
    def test_user_log_fullpath(self):
        """
        Test that the user log file path is returned.
        """
        fp = self.set.user_log_fullpath
        should_be_fp = os.path.join(self.set.user_log_dir,
                                    self.set.logfile_name)
        msg = f"Should be '{should_be_fp}' found '{fp}'."
        self.assertEqual(should_be_fp, fp, msg)

    #@unittest.skip("Temporarily skipped")
    def test_local_config_fullpath(self):
        """
        Test that the local data file path is returned.
        """
        fp = self.set.local_config_fullpath
        should_be_fp = os.path.join(self.set._LOCAL_CONFIG,
                                    self.set._Settings__local_toml)
        msg = f"Should be '{should_be_fp}' found '{fp}'."
        self.assertEqual(should_be_fp, fp, msg)


class TestBaseSystemData(unittest.TestCase):
    _TMP_USER_CONFIG_FILE = '/tmp/user_config.toml'
    _TMP_USER_APP_CONFIG_FILE = '/tmp/user_app_config.toml'

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.bsd = BaseSystemData()

    def tearDown(self):
        try:
            os.remove(self._TMP_USER_CONFIG_FILE)
            os.remove(self._TMP_USER_APP_CONFIG_FILE)
        except FileNotFoundError:
            pass

    #@unittest.skip("Temporarily skipped")
    @patch.object(BaseSystemData, 'user_app_config_fullpath',
                  _TMP_USER_APP_CONFIG_FILE)
    @patch.object(BaseSystemData, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_parse_toml_user_app_config(self):
        """
        Test that toml files get parsed correctly.
        """
        # Create or copy files to temporary locations.
        tac = TomlAppConfig()
        tac.create_app_config()
        shutil.copy2(self.bsd.local_config_fullpath,
                     self._TMP_USER_CONFIG_FILE)
        # Run test
        file_types = ('user_config_fullpath', 'user_app_config_fullpath')
        errors = self.bsd.parse_toml(file_types)
        self.assertFalse(errors)
        results = {'user_config_fullpath': self.bsd.panel_config,
                   'user_app_config_fullpath': self.bsd.app_config}

        for key, result in results.items():
            valid = isinstance(result, tk.toml_document.TOMLDocument)
            msg = f"Have parsed data for {key} '{valid}'"
            self.assertTrue(valid, msg)

    #@unittest.skip("Temporarily skipped")
    def test_parse_toml_local_config(self):
        """
        Test that toml files get pared correctly.
        """
        self.bsd.panel_config = None
        file_types = ('local_config_fullpath',)
        errors = self.bsd.parse_toml(file_types)
        self.assertFalse(errors)
        results = {'local_config_fullpath': self.bsd.panel_config}

        for key, result in results.items():
            valid = isinstance(result, tk.toml_document.TOMLDocument)
            msg = f"Have parsed data for {key} '{valid}'"
            self.assertTrue(valid, msg)

    #@unittest.skip("Temporarily skipped")
    def test_parse_toml_invalid_file_type(self):
        """
        Test that an exception is raised when a wrong file type is found.
        """
        errors = self.bsd.parse_toml(('non_existant_file',))

        for error in errors:
            msg = f"Should have error '{error[1]}'"
            self.assertIn('Invalid property, ', error[1])

    #@unittest.skip("Temporarily skipped")
    @patch.object(BaseSystemData, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_parse_toml_file_not_found_error(self):
        """
        Test that an exception is raised when a file is not found.
        """
        errors = self.bsd.parse_toml(('user_config_fullpath',))

        for error in errors:
            msg = f"Should have error '{error[1]}'"
            self.assertIn('Cannot find file ', error[1])

    #@unittest.skip("Temporarily skipped")
    @patch.object(BaseSystemData, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_parse_toml_parse_error(self):
        """
        Test that an exception is raised when a parse error is found.
        """
        # Create an unparsable file.
        with open(self._TMP_USER_CONFIG_FILE, 'w') as f:
            f.write("[meta]\nsomevar = {junk='some_value'")

        errors = self.bsd.parse_toml(('user_config_fullpath',))

        for error in errors:
            msg = f"Should have error '{error[1]}'"
            self.assertIn('TOML error: ', error[1])

    #@unittest.skip("Temporarily skipped")
    @patch.object(BaseSystemData, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_parse_toml_empty_file_error(self):
        """
        Test that an exception is raised when a zero length file is found.
        """
        # Create an unparsable file.
        with open(self._TMP_USER_CONFIG_FILE, 'w') as f:
            f.write("")

        errors = self.bsd.parse_toml(('user_config_fullpath',))

        for error in errors:
            msg = f"Should have error '{error[1]}'"
            self.assertIn('Cannot parse zero length file ', error[1])


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
        self.assertEqual(self._NUM_PANELS, num_panels, msg)
        num_in_panel = 2
        msg = (f"There should be 2 strings in each panel object, found {{}} "
               f"in panel {{}}.")

        for panel in panels:
            num = len(panel)
            self.assertEqual(num_in_panel, num, msg.format(num, panel))

    #@unittest.skip("Temporarily skipped")
    def test_months_property(self):
        """
        Test that there are the correct number of months.
        """
        months = self.tmd.months
        num_months = len(months)
        msg = f"There should be {self.NUM_MONTHS}, found {num_months}."
        self.assertEqual(self.NUM_MONTHS, num_months, msg)

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
            self.assertEqual(should_be_num, found_num_prefix, msg)

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
        self.assertEqual(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_NORMAL'
        found_weight = font_12_normal[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEqual(should_be_weight, found_weight, msg)

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
        self.assertEqual(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_BOLD'
        found_weight = font_12_bold[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEqual(should_be_weight, found_weight, msg)

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
        self.assertEqual(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_NORMAL'
        found_weight = font_10_normal[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEqual(should_be_weight, found_weight, msg)

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
        self.assertEqual(should_be_points, found_points, msg)
        # Test weight
        should_be_weight = 'FONTWEIGHT_BOLD'
        found_weight = font_10_bold[3]
        msg = f"The weight should be {should_be_weight}, found {found_weight}."
        self.assertEqual(should_be_weight, found_weight, msg)

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
            self.assertEqual(values[0], font[0],
                              msg.format('points', values[0], font[0]))
            self.assertEqual(values[1], font[3],
                              msg.format('weight', values[0], font[3]))


class TestTomlPanelConfig(BaseTest):
    _TMP_USER_CONFIG_FILE = '/tmp/user_config.toml'
    _TMP_LOCAL_CONFIG_FILE = '/tmp/default_bahai.toml'

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

        try:
            os.remove(self._TMP_LOCAL_CONFIG_FILE)
        except FileNotFoundError:
            pass

        try:
            os.remove(f"{self._TMP_USER_CONFIG_FILE}.bad")
        except FileNotFoundError:
            pass

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, '_FILE_LIST', ('user_invalid_property',
                                                  'local_invalid_property'))
    def test_is_valid_property_invalid(self):
        """
        Test that an invalid property causes an error.
        """
        ret = self.tpc.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_is_valid_property(self):
        """
        Test that the is_valid property returns a True for normal operation.
        """
        # Create or copy files to temporary locations.
        shutil.copy2(self.tpc.local_config_fullpath,
                     self._TMP_USER_CONFIG_FILE)
        # Run test
        ret = self.tpc.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_user_bad_file(self):
        """
        Test that the is_valid property returns a True for a bad file in
        the `user_config_fullpath` property. The bad file is fixed.

        Note: The responds to error code 4.
        """
        ret = self.tpc.is_valid
        msg = f"Should be True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_user_unparsable(self):
        """
        Test that the is_valid property returns a True for an unparsable
        Toml file in the `user_config_fullpath` property.

        Note: 1. The is_valid will fix this issue so it will return a True.
              2. Responds to error code 3.
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
    def test_is_valid_property_local_not_found(self):
        """
        Test that the is_valid property returns a False for a not found
        file in the `local_config_fullpath` property.

        Note: Responds to error code 2.
        """
        ret = self.tpc.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlPanelConfig, '_LOCAL_CONFIG', '/tmp')
    @patch.object(TomlPanelConfig, 'user_config_fullpath',
                  _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_local_unparsable(self):
        """
        Test that the is_valid property returns a False for an unparsable
        Toml file in the `local_config_fullpath` property.
        """
        # Create an unparsable file.
        with open(self._TMP_LOCAL_CONFIG_FILE, 'w') as f:
            f.write("[meta]\nsomevar = {junk='some_value'")

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

        try:
            os.remove(f"{self._TMP_USER_APP_FILE}.bad")
        except FileNotFoundError:
            pass

    def create_config(self):
        self.tac.create_app_config()
        return self.tac.is_valid

    #@unittest.skip("Temporarily skipped")
    @patch.object(TomlAppConfig, '_FILE_LIST', ('user_invalid_property',))
    def test_is_valid_property_invalid(self):
        """
        Test that an invalid property causes an error.
        """
        ret = self.tac.is_valid
        msg = f"Should be False, found {ret}."
        self.assertFalse(ret, msg)

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
            self.assertEqual(outer_key_list[j], outer_key,
                              key_msg.format(outer_key))

            for k, (inner_key, value) in enumerate(values.items()):
                self.assertEqual(inner_key_list[k], inner_key,
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
        self.assertEqual(new_value, value, msg)

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
        self.assertEqual(new_value, value, msg)

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
