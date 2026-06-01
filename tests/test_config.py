# -*- coding: utf-8 -*-
#
# tests/test_config.py
#
__docformat__ = "restructuredtext en"

import os
import sys
import unittest
import shutil

from unittest.mock import patch, PropertyMock

import tomlkit as tk

from . import LOGGER_NAME, LOGFILE_NAME, log, check_flag
from .base_dir import BASE_DIR
from .base_database_test import BaseTests
from .conftest import (_TMP_USER_CONFIG_FILE, _TMP_USER_APP_CONFIG_FILE,
                       _TMP_LOCAL_CONFIG_FILE)

PATH = os.path.join(BASE_DIR, 'logs')


def import_in_globals():
    import src
    from src import config
    globals()['src'] = src.__init__
    globals()['Settings'] = config.Settings
    globals()['BaseSystemData'] = config.BaseSystemData
    globals()['TomlMetaData'] = config.TomlMetaData
    globals()['TomlPanelConfig'] = config.TomlPanelConfig
    globals()['TomlAppConfig'] = config.TomlAppConfig
    globals()['TomlCreatePanel'] = config.TomlCreatePanel


def patchers(self):
    sys.modules.pop('src', None)

    logger_name_patcher = patch('src.config.Settings.logger_name',
                                new_callable=PropertyMock)
    mock_name_patcher = logger_name_patcher.start()
    self.addCleanup(logger_name_patcher.stop)
    mock_name_patcher.return_value = LOGGER_NAME

    logfile_path_patcher = patch('src.config.Settings.user_log_fullpath',
                                 new_callable=PropertyMock)
    mock_logfile_path = logfile_path_patcher.start()
    self.addCleanup(logfile_path_patcher.stop)
    mock_logfile_path.return_value = PATH

    logfile_name_patcher = patch('src.config.Settings.logfile_name',
                                 new_callable=PropertyMock)
    mock_logfile_name = logfile_name_patcher.start()
    self.addCleanup(logfile_name_patcher.stop)
    mock_logfile_name.return_value = LOGFILE_NAME
    import_in_globals()


class TestSettingsBorg(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._set = Settings()

    def tearDown(self):
        self._set.debug = False
        self._set.testing = False

    #@unittest.skip("Temporarily skipped")
    def test_debug_setter_getter(self):
        """
        Test that the debug properties cause the directory environment
        to change properly.
        """
        data = (
            (False, False),
            (True, True),
            )
        msg = "Expected {} found {}"

        for set, expected in data:
            self._set.debug = set
            result = self._set.debug
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_testing_setter_getter(self):
        """
        Test that the testing properties cause the directory environment
        to change properly.
        """
        data = (
            (False, False),
            (True, True),
            )
        msg = "Expected {} found {}"

        for set, expected in data:
            self._set.testing = set
            result = self._set.testing
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_SettingsBorg_with_TomlMetaData(self):
        """
        Test that multiple instantiations of the Settings and TomlMetaData
        class' have the same state.
        """
        tmd = TomlMetaData()
        tmd.debug = True
        result = tmd.debug
        msg = f"Expected {True}, found {result}"
        self.assertTrue(result, msg)

    #@unittest.skip("Temporarily skipped")
    def test_SettingsBorg_with_TomlAppConfig(self):
        """
        Test that multiple instantiations of the Settings and TomlAppConfig
        class' have the same state.
        """
        tac = TomlAppConfig()
        tac.debug = True
        result = tac.debug
        msg = f"Expected {True}, found {result}"
        self.assertTrue(result, msg)

    #@unittest.skip("Temporarily skipped")
    def test_SettingsBorg_with_TomlCreatePanel(self):
        """
        Test that multiple instantiations of the Settings and TomlCreatePanel
        class' have the same state.
        """
        tcp = TomlCreatePanel()
        tcp.debug = True
        result = tcp.debug
        msg = f"Expected {True}, found {result}"
        self.assertTrue(result, msg)


class TestSettings(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._set = Settings()

    def tearDown(self):
        self._set.debug = False
        self._set.testing = False

    #@unittest.skip("Temporarily skipped")
    def test_logger_name_patcher(self):
        """
        Test that the logger_name property was patch correctly.
        """
        log.debug("The 'logger_name' property was patched with %s.",
                  self._set.logger_name)
        self.assertEqual(self._set.logger_name, LOGGER_NAME)

    #@unittest.skip("Temporarily skipped")
    def test_logfile_path_patcher(self):
        """
        Test that the user_log_fullpath property was patched correctly.
        """
        log.debug("The 'user_log_fullpath' property was patched with %s.",
                  self._set.user_log_fullpath)
        self.assertEqual(self._set.user_log_fullpath, PATH)

    #@unittest.skip("Temporarily skipped")
    def test_logfile_name_patcher(self):
        """
        Test that the logfile_name property was patched correctly.
        """
        log.debug("The 'logfile_name' property was patched with %s.",
                  self._set.logfile_name)
        self.assertEqual(self._set.logfile_name, LOGFILE_NAME)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.Settings._BASE_DIR', PATH)
    def test_base_dir(self):
        """
        Test that this static method returns the base directory without
        instantiating the class.
        """
        path = Settings.base_dir()
        expected = Settings._BASE_DIR
        msg = f"Expected path '{expected}' found '{path}'."
        self.assertEqual(expected, path, msg)

    #@unittest.skip("Temporarily skipped")
    def test_primary_developer(self):
        """
        Test that the primary developer is returned.
        """
        dev = self._set.primary_developer
        expected = self._set._DEVELOPERS[0]
        msg = f"Expected '{expected}' found '{dev}'"
        self.assertEqual(expected, dev, msg)

    #@unittest.skip("Temporarily skipped")
    def test_contributors(self):
        """
        Test that the contributors are returned.
        """
        # Test that a list is returned.
        cont = self._set.contributors(True)
        expected = self._set._DEVELOPERS
        msg = f"Expected '{expected}' found '{cont}'"
        self.assertEqual(expected, cont, msg)
        # Test that a srting is returned.
        cont = self._set.contributors()
        expected = ''.join([s+'\n' for s in self._set._DEVELOPERS]).strip()
        msg = f"Expected '{expected}' found '{cont}'"
        self.assertEqual(expected, cont, msg)

    #@unittest.skip("Temporarily skipped")
    def test_logger_name(self):
        """
        Test that the data logger name is returned. THIS METHOD IS PATCHED
        SO THE ACTUAL METHOD IS NEVER CALLED see patchers() above.
        """
        name = self._set.logger_name
        expected = LOGGER_NAME
        msg = f"Expected '{expected}' found '{name}'."
        self.assertEqual(expected, name, msg)

    #@unittest.skip("Temporarily skipped")
    def test_logfile_name(self):
        """
        Test that the data logfile name is returned.
        """
        name = self._set.logfile_name
        expected = LOGFILE_NAME
        msg = f"Expected '{expected}' found '{name}'."
        self.assertEqual(expected, name, msg)

    #@unittest.skip("Temporarily skipped")
    def test_data_file_name(self):
        """
        Test that the data file name is returned.
        """
        df = self._set.data_file_name
        expected = self._set._DATA_FILE
        msg = f"Expected '{expected}' found '{df}'."
        self.assertEqual(expected, df, msg)

    #@unittest.skip("Temporarily skipped")
    def test_user_data_fullpath(self):
        """
        Test that the user data file path is returned.
        """
        data = (
            (None, 'user_data_dir'),
            ('debug', '_debug_data_dir'),
            ('testing', '_testing_data_dir'),
            )
        msg = "Expected {}, found {}"

        for env, method in data:
            if env is not None:
                self._set.debug = False
                setattr(self._set, env, True)

            self._set.create_dirs()
            expected = os.path.join(getattr(self._set, method),
                                    self._set.data_file_name)
            result = self._set.user_data_fullpath
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_user_config_fullpath(self):
        """
        Test that the user config file path is returned.
        """
        data = (
            (None, 'user_config_dir'),
            ('debug', '_debug_data_dir'),
            ('testing', '_testing_data_dir'),
            )
        msg = "Expected {}, found {}"

        for env, method in data:
            if env is not None:
                self._set.debug = False
                setattr(self._set, env, True)

            self._set.create_dirs()
            expected = os.path.join(getattr(self._set, method),
                                    self._set._Settings__user_toml)
            result = self._set.user_config_fullpath
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_user_app_config_fullpath(self):
        """
        Test that the user app config file path is returned.
        """
        data = (
            (None, 'user_config_dir'),
            ('debug', '_debug_data_dir'),
            ('testing', '_testing_data_dir'),
            )
        msg = "Expected {}, found {}"

        for env, method in data:
            if env is not None:
                self._set.debug = False
                setattr(self._set, env, True)

            self._set.create_dirs()
            expected = os.path.join(getattr(self._set, method),
                                    self._set._Settings__app_toml)
            result = self._set.user_app_config_fullpath
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_user_log_fullpath(self):
        """
        Test that the user log file path is returned. THIS WILL ALWAYS RETURN
        A PATCHED PATH see patchers() above.
        """
        msg = "Expected {}, found {}"
        expected = os.path.join(BASE_DIR, 'logs')
        result = self._set.user_log_fullpath
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_cached_factory_dir(self):
        """
        Test that the cached_factory_dir method returns the factory path.
        """
        data = (
            (None, 'user_cache_dir'),
            ('debug', '_debug_data_dir'),
            )
        msg = "Expected {}, found {}"

        for env, method in data:
            if env is not None:
                self._set.debug = False
                setattr(self._set, env, True)

            self._set.create_dirs()
            expected = os.path.join(getattr(self._set, method),
                                    self._set.panel_factory_name)
            result = self._set.cached_factory_dir
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_local_config_fullpath(self):
        """
        Test that the local data file path is returned.
        """
        msg = "Expected {}, found {}."
        expected = os.path.join(self._set._LOCAL_CONFIG,
                                self._set._Settings__local_toml)
        result = self._set.local_config_fullpath
        self.assertEqual(expected, result, msg.format(expected, result))


class TestBaseSystemData(BaseTests, unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self._bsd = BaseSystemData()
        self.log_path = os.path.join(self._bsd.user_log_fullpath, LOGFILE_NAME)

    def tearDown(self):
        try:
            os.remove(_TMP_USER_CONFIG_FILE)
        except FileNotFoundError:
            pass

        try:
            os.remove(_TMP_USER_APP_CONFIG_FILE)
        except FileNotFoundError:
            pass

    def _handle_errors(self, doc, filepath):
        if isinstance(doc, int):
            result = self._bsd.ERR_MESSAGES[doc].format(filepath)
        else:
            result = ""

        return result

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.BaseSystemData.user_app_config_fullpath',
           _TMP_USER_APP_CONFIG_FILE)
    @patch('src.config.BaseSystemData.user_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test_parse_toml_user_app_config(self):
        """
        Test that toml files get parsed correctly.
        """
        # Create or copy files to temporary locations.
        tac = TomlAppConfig()
        tac._create_app_config()
        shutil.copy2(self._bsd.local_config_fullpath, _TMP_USER_CONFIG_FILE)
        TOMLDocument = tk.toml_document.TOMLDocument
        data = ('user_config_fullpath', 'user_app_config_fullpath')
        msg = "Expected {}, filepath {}, found {}."

        for prop in data:
            filepath = getattr(self._bsd, prop)
            doc = self._bsd.parse_toml(filepath)
            error = self._handle_errors(doc, filepath)
            self.assertEqual("", error, msg.format("", filepath, error))
            self.assertIsInstance(doc, TOMLDocument, msg.format(
                TOMLDocument, filepath, type(doc)))

    #@unittest.skip("Temporarily skipped")
    def test_parse_toml_local_config(self):
        """
        Test that toml files get pared correctly.
        """
        TOMLDocument = tk.toml_document.TOMLDocument
        data = ('local_config_fullpath',)
        msg = "Expected {}, filepath {}, found {}."

        for prop in data:
            filepath = getattr(self._bsd, prop)
            doc = self._bsd.parse_toml(filepath)
            error = self._handle_errors(doc, filepath)
            self.assertEqual("", error, msg.format("", filepath, error))
            self.assertIsInstance(doc, TOMLDocument, msg.format(
                TOMLDocument, filepath, type(doc)))

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.BaseSystemData.user_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test_parse_toml_errors(self):
        """
        Test that the correct variables are set with error conditions.
        """
        err_msg0 = self._bsd.ERR_MESSAGES[self._bsd.ERR_FILE_NOT_FOUND]
        err_msg1 = self._bsd.ERR_MESSAGES[self._bsd.ERR_TOML_ERROR]
        err_msg2 = self._bsd.ERR_MESSAGES[self._bsd.ERR_ZERO_LENGTH_FILE]
        data = (
            (self._bsd.ERR_FILE_NOT_FOUND, err_msg0),    # ERR_FILE_NOT_FOUND
            (self._bsd.ERR_TOML_ERROR, err_msg1),        # ERR_TOML_ERROR
            (self._bsd.ERR_ZERO_LENGTH_FILE, err_msg2),  # ERR_ZERO_LENGTH_FILE
            )
        msg = "Expected {}, err_code {}, found {}."

        for err_code, expected_results in data:
            if err_code == self._bsd.ERR_FILE_NOT_FOUND:
                pass  # The file was never created.
            elif err_code == self._bsd.ERR_TOML_ERROR:
                # Create an unparsable file.
                with open(_TMP_USER_CONFIG_FILE, 'w') as f:
                    f.write("[meta]\nsomevar = {junk='some_value'")
            elif err_code == self._bsd.ERR_ZERO_LENGTH_FILE:
                # Create a zero length file.
                with open(_TMP_USER_CONFIG_FILE, 'w') as f:
                    f.write("")
            else:
                self.assertTrue(false, f"Invalid error code {err_code}.")

            error = self._bsd.parse_toml(self._bsd.user_config_fullpath)
            self.assertEqual(expected_results, self._bsd.ERR_MESSAGES[error],
                             msg.format(expected_results, err_code, error))

    #@unittest.skip("Temporarily skipped")
    def test_err_msg(self):
        """
        Test that the err_msg properties returns an error message.
        """
        data = (None, "Test Message")
        msg = "Expected '{}', found '{}'."

        for test_msg in data:
            self._bsd.err_msg = test_msg
            result = self._bsd.err_msg
            self.assertEqual(test_msg, result, msg.format(test_msg, result))

    #@unittest.skip("Temporarily skipped")
    def test_error(self):
        """
        Test that the error properties returns an error message.
        """
        data = (None, 1)
        msg = "Expected '{}', found '{}'."

        for test_msg in data:
            self._bsd.error = test_msg
            result = self._bsd.error
            self.assertEqual(test_msg, result, msg.format(test_msg, result))


class BaseTomlTest(BaseTests, unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        patchers(self)


class TestTomlMetaData(BaseTomlTest):
    _NUM_PANELS = 4

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        super().setUp()

        tpc = TomlPanelConfig()
        tpc._read_file(tpc.local_config_fullpath)
        self._tmd = TomlMetaData()
        # Reset the Borg class.
        self._tmd.clear_state()
        self.assertIsInstance(tpc.panel_config, tk.toml_document.TOMLDocument)

        self.NUM_MONTHS = {'bahai': 20, 'generic': 12}.get(
            self._tmd.config_type)

    #@unittest.skip("Temporarily skipped")
    def test_title(self):
        """
        Test that the title property returns the META data title.
        """
        expected = "Bahá'í Bookkeeper"
        result = self._tmd.title
        self.assertEqual(expected, result)

    #@unittest.skip("Temporarily skipped")
    def test_panels_property(self):
        """
        Test that the panel property returns a list of list containing
        [[Menu Name, Toml File Name],...]
        """
        log.debug("Testing test_panels_property")
        panels = self._tmd.panels
        num_panels = len(panels)
        msg = f"There should be {self._NUM_PANELS}, found {num_panels}."
        self.assertEqual(self._NUM_PANELS, num_panels, msg)
        num_in_panel = 2
        msg = ("There should be 2 strings in each panel object, found {} "
               "in panel {}.")

        for panel in panels:
            num = len(panel)
            self.assertEqual(num_in_panel, num, msg.format(num, panel))

    #@unittest.skip("Temporarily skipped")
    def test_locale_prefix_property(self):
        """
        Test that the locality prefix is correct.

        Note: This is only tested for the Bahá'í app.
        """
        if self._tmd.config_type == 'bahai':
            locale_prefix = self._tmd.locale_prefix
            found_num_prefix = len(locale_prefix)
            expected = 2
            msg = f"There should be {expected}, found {found_num_prefix}."
            self.assertEqual(expected, found_num_prefix, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_16_bold(self):
        """
        Test that the font is correct.
        """
        font_16_bold = self._tmd.font_16_bold
        expected = 16
        found_points = font_16_bold[0]
        msg = f"The points should be {expected}, found {found_points}."
        self.assertEqual(expected, found_points, msg)
        # Test weight
        expected = 'FONTWEIGHT_BOLD'
        found_weight = font_16_bold[3]
        msg = f"The weight should be {expected}, found {found_weight}."
        self.assertEqual(expected, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_14_bold(self):
        """
        Test that the font is correct.
        """
        font_14_bold = self._tmd.font_14_bold
        expected = 14
        found_points = font_14_bold[0]
        msg = f"The points should be {expected}, found {found_points}."
        self.assertEqual(expected, found_points, msg)
        # Test weight
        expected = 'FONTWEIGHT_BOLD'
        found_weight = font_14_bold[3]
        msg = f"The weight should be {expected}, found {found_weight}."
        self.assertEqual(expected, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_12_normal_property(self):
        """
        Test that the font is correct.
        """
        font_12_normal = self._tmd.font_12_normal
        # Test points
        expected = 12
        found_points = font_12_normal[0]
        msg = f"The points should be {expected}, found {found_points}."
        self.assertEqual(expected, found_points, msg)
        # Test weight
        expected = 'FONTWEIGHT_NORMAL'
        found_weight = font_12_normal[3]
        msg = f"The weight should be {expected}, found {found_weight}."
        self.assertEqual(expected, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_12_bold_property(self):
        """
        Test that the font is correct.
        """
        font_12_bold = self._tmd.font_12_bold
        # Test points
        expected = 12
        found_points = font_12_bold[0]
        msg = f"The points should be {expected}, found {found_points}."
        self.assertEqual(expected, found_points, msg)
        # Test weight
        expected = 'FONTWEIGHT_BOLD'
        found_weight = font_12_bold[3]
        msg = f"The weight should be {expected}, found {found_weight}."
        self.assertEqual(expected, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_10_normal_property(self):
        """
        Test that the font is correct.
        """
        font_10_normal = self._tmd.font_10_normal
        # Test points
        expected = 10
        found_points = font_10_normal[0]
        msg = f"The points should be {expected}, found {found_points}."
        self.assertEqual(expected, found_points, msg)
        # Test weight
        expected = 'FONTWEIGHT_NORMAL'
        found_weight = font_10_normal[3]
        msg = f"The weight should be {expected}, found {found_weight}."
        self.assertEqual(expected, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_font_10_bold_property(self):
        """
        Test that the font is correct.
        """
        font_10_bold = self._tmd.font_10_bold
        # Test points
        expected = 10
        found_points = font_10_bold[0]
        msg = f"The points should be {expected}, found {found_points}."
        self.assertEqual(expected, found_points, msg)
        # Test weight
        expected = 'FONTWEIGHT_BOLD'
        found_weight = font_10_bold[3]
        msg = f"The weight should be {expected}, found {found_weight}."
        self.assertEqual(expected, found_weight, msg)

    #@unittest.skip("Temporarily skipped")
    def test_get_font(self):
        """
        Test that the proper font is returned.
        """
        fonts = {'font_12_normal': (12, 'FONTWEIGHT_NORMAL'),
                 'font_12_bold': (12, 'FONTWEIGHT_BOLD'),
                 'font_10_normal': (10, 'FONTWEIGHT_NORMAL'),
                 'font_10_bold': (10, 'FONTWEIGHT_BOLD'),
                 'font_100_normal': (100, 'DOES_NOT_EXIST')}
        msg = "The font {} should be {}, found {}. "

        for font_type, values in fonts.items():
            font = self._tmd.get_font(font_type)

            if font is None:
                err_msg0 = f"Invalid font_type, found '{font_type}'"
                full_path = os.path.join(self._tmd.user_log_fullpath,
                                         LOGFILE_NAME)
                file_data = self.read_text_file(full_path)
                result = self.find_text(file_data, 'get_font', 1, err_msg0)
                self.assertIn(err_msg0, result)
            else:
                self.assertEqual(values[0], font[0], msg.format(
                    'points', values[0], font[0]))
                self.assertEqual(values[1], font[3], msg.format(
                    'weight', values[0], font[3]))

    #@unittest.skip("Temporarily skipped")
    def test_data_entry_title_data(self):
        """
        Test that the data_entry_title_data method returns the data entry
        titles.
        """
        result = self._tmd.data_entry_title_data
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], list)

    #@unittest.skip("Temporarily skipped")
    def test_data_entry_labels(self):
        """
        Test that the data_entry_labels method returns the data entry labels.
        """
        result = self._tmd.data_entry_labels
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], list)


class TestTomlPanelConfig(BaseTomlTest):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        super().setUp()
        self._tpc = TomlPanelConfig()
        self.log_path = os.path.join(self._tpc.user_log_fullpath, LOGFILE_NAME)

    def tearDown(self):
        try:
            os.remove(_TMP_USER_CONFIG_FILE)
        except FileNotFoundError:
            pass

        try:
            os.remove(_TMP_LOCAL_CONFIG_FILE)
        except FileNotFoundError:
            pass

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlPanelConfig.user_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test__has_user_config(self):
        """
        Test that the _has_user_config property returns `True` or `False`
        depending on if the user config file exists and that on `False` a
        log message is created.
        """
        err_msg0 = "The path '{}' does not exist, file will be copied."
        data = (False, True)
        msg = "Expected {}, found {}."
        good_file = _TMP_USER_CONFIG_FILE

        for expected in data:
            if expected:
                with open(good_file, 'w') as f:
                    f.write("This is mostly an empty file.")

                with patch('src.config.TomlPanelConfig.user_config_fullpath',
                           good_file):
                    result = self._tpc._has_user_config
                    self.assertTrue(result, msg.format(expected, result))
            else:
                result = self._tpc._has_user_config
                self.assertFalse(result, msg.format(expected, result))
                file_data = self.read_text_file(self.log_path)
                err_msg = err_msg0.format(self._tpc.user_config_fullpath)
                result = self.find_text(
                    file_data, 'Start logging for TestTomlPanelConfig',
                    10, err_msg)
                self.assertIn(err_msg, result)

    #@unittest.skip("Temporarily skipped")
    def test__has_local_config(self):
        """
        Test that the _has_local_config property returns `True` or `False`
        depending on if the local config file exists and that on `False` a
        log message is created.
        """
        err_msg0 = "The path '{}' does not exist, exiting application."
        data = (True, False)
        msg = "Expected {}, found {}."

        for expected in data:
            if expected:
                result = self._tpc._has_local_config
                self.assertTrue(result, msg.format(expected, result))
            else:
                bad_file = '/tmp/DoesNotExist'

                with patch('src.config.TomlPanelConfig.local_config_fullpath',
                           bad_file):
                    result = self._tpc._has_local_config
                    self.assertFalse(result, msg.format(expected, result))
                    file_data = self.read_text_file(self.log_path)
                    err_msg = err_msg0.format(bad_file)
                    result = self.find_text(
                        file_data, 'Start logging for TestTomlPanelConfig',
                        10, err_msg)
                    self.assertIn(err_msg, result)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlPanelConfig.user_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test_is_valid_property(self):
        """
        Test that the is_valid property returns a True for normal operation.
        """
        # Create or copy files to temporary locations.
        shutil.copy2(self._tpc.local_config_fullpath, _TMP_USER_CONFIG_FILE)
        # Run test
        ret = self._tpc.is_valid
        msg = f"Expected True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlPanelConfig.user_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_user_bad_file(self):
        """
        Test that the is_valid property returns a True for a bad file in
        the `user_config_fullpath` property. The bad file is fixed.

        .. note::

           The response to error code 4.
        """
        ret = self._tpc.is_valid
        msg = f"Expected True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlPanelConfig.user_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_user_unparsable(self):
        """
        Test that the is_valid property returns a True for an unparsable
        Toml file in the `user_config_fullpath` property.

        .. note::

            1. The is_valid will fix this issue so it will return a True.
            2. The response to error code 3.
        """
        # Create an unparsable file.
        with open(_TMP_USER_CONFIG_FILE, 'w') as f:
            f.write('')

        ret = self._tpc.is_valid
        msg = f"Expected True, found {ret}."
        self.assertTrue(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlPanelConfig.local_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_local_not_found(self):
        """
        Test that the is_valid property returns a False for a not found
        file in the `local_config_fullpath` property.

        Note: Responds to error code 2.
        """
        ret = self._tpc.is_valid
        msg = f"Expected False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlPanelConfig._LOCAL_CONFIG', '/tmp')
    @patch('src.config.TomlPanelConfig.user_config_fullpath',
           _TMP_USER_CONFIG_FILE)
    def test_is_valid_property_local_unparsable(self):
        """
        Test that the is_valid property returns a False for an unparsable
        Toml file in the `local_config_fullpath` property.
        """
        # Create an unparsable file.
        with open(_TMP_LOCAL_CONFIG_FILE, 'w') as f:
            f.write("[meta]\nsomevar = {junk='some_value'")

        ret = self._tpc.is_valid
        msg = f"Expected False, found {ret}."
        self.assertFalse(ret, msg)

    #@unittest.skip("Temporarily skipped")
    def test__copy_file(self):
        """
        Test that the _copy_file method correctly copies a file.
        """
        file0 = _TMP_USER_CONFIG_FILE
        file1 = file0 + '.bak'
        err_msg0 = f"Could not copy file {file0} to {file1},"

        data = (
            (file0, file1, True),
            ('', file1, False),
            )
        msg = "Expected {}, found {}."

        for f0, f1, expected in data:
            if f0:
                with open(f0, 'w') as f:
                    f.write("Nothin much.")

                self._tpc._copy_file(f0, f1)
                result = os.path.exists(f1)
                self.assertTrue(result, msg.format(expected, result))
            else:
                with self.assertRaises(FileNotFoundError):
                    self._tpc._copy_file(f0, f1)
                    file_data = self.read_text_file(self.log_path)
                    result = self. find_text(
                        file_data, 'Start logging for TestTomlPanelConfig',
                        10, err_msg0)
                    self.assertIn(err_msg0, result)


class TestTomlAppConfig(BaseTomlTest):
    _TMP_USER_APP_FILE = '/tmp/user_app_config.toml'
    _TMP_UNWRITABE_PATH = '/invalid_test.toml'

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        super().setUp()
        self._tac = TomlAppConfig()
        self.log_path = os.path.join(self._tac.user_log_fullpath, LOGFILE_NAME)

    def tearDown(self):
        try:
            os.remove(self._TMP_USER_APP_FILE)
        except FileNotFoundError:
            pass

    def create_config(self):
        self._tac._create_app_config()
        return self._tac.is_valid

    #@unittest.skip("Temporarily skipped")
    def test__has_app_user_config(self):
        """
        Test that the _has_app_user_config property returns `True` or `False`
        depending on if the local config file exists and that on `False` a
        log message is created.
        """
        err_msg0 = "The path '{}' does not exist, file will be created."
        data = (True, False)
        msg = "Expected {}, found {}."
        good_file = self._TMP_USER_APP_FILE

        for expected in data:
            if expected:
                with open(good_file, 'w') as f:
                    f.write("This is mostly an empty file.")

                with patch('src.config.TomlAppConfig.user_app_config_fullpath',
                           good_file):
                    result = self._tac._has_app_user_config
                    self.assertTrue(result, msg.format(expected, result))
            else:
                bad_file = '/tmp/DoesNotExist'

                with patch('src.config.TomlAppConfig.user_app_config_fullpath',
                           bad_file):
                    result = self._tac._has_app_user_config
                    self.assertFalse(result, msg.format(expected, result))
                    file_data = self.read_text_file(self.log_path)
                    err_msg = err_msg0.format(bad_file)
                    result = self.find_text(
                        file_data, 'Start logging for TestTomlAppConfig',
                        10, err_msg)
                    self.assertIn(err_msg, result, msg.format(err_msg, result))

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
           _TMP_USER_APP_FILE)
    def test_is_valid(self):
        """
        Test that the is_valid property returns a boolean for normal
        operation.
        """
        def _check_log():
            result = self._tac.is_valid
            file_data = self.read_text_file(self.log_path)
            err_msg = err_msg0.format(self._TMP_USER_APP_FILE)
            error = self. find_text(
                file_data, 'Start logging for TestTomlAppConfig', 10, err_msg)
            self.assertIn(err_msg, error)
            return result

        err_msg0 = ("Cannot parse file '{}' may be corrupted, Unexpected "
                    "character: '=' at line 2 col 7")
        err_msg1 = "Cannot parse zero length file '{}'."
        data = (
            (self._tac.ERR_FILE_NOT_FOUND, True),
            (self._tac.ERR_TOML_ERROR, True),
            (self._tac.ERR_ZERO_LENGTH_FILE, True),
            )
        msg = "Expected {}, found {}."

        for err, expected in data:
            if err == self._tac.ERR_TOML_ERROR:
                with open(self._TMP_USER_APP_FILE, 'w') as f:
                    f.write("[meta]\ntitle === 'JUNK'\n")

                result = _check_log()
            elif err == self._tac.ERR_ZERO_LENGTH_FILE:
                with open(self._TMP_USER_APP_FILE, 'w') as f:
                    f.write('')

                result = _check_log()
            else:
                result = self._tac.is_valid

            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
           _TMP_USER_APP_FILE)
    def test_create_app_config(self):
        """
        Test that the application config file is created.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        ret = self.create_config()
        msg = f"Expected True, found {ret}."
        self.assertTrue(ret, msg)
        outer_key_list = ('app_size',)
        inner_key_list = ('default', 'size')
        key_msg = "Key '{}' does not exist"
        val_msg = "Value should be a list, found '{}'."

        for j, (outer_key, values) in enumerate(self._tac.app_config.items()):
            self.assertEqual(outer_key_list[j], outer_key,
                             key_msg.format(outer_key))

            for k, (inner_key, value) in enumerate(values.items()):
                self.assertEqual(inner_key_list[k], inner_key,
                                 key_msg.format(inner_key))
                self.assertTrue(isinstance(value, list), val_msg.format(value))

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
           _TMP_USER_APP_FILE)
    def test_get_value(self):
        """
        Test that a value can be found.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        self.create_config()
        value = self._tac.get_value('app_size', 'default')
        msg = f"Value should be a list, found '{value}'."
        self.assertTrue(isinstance(value, list), msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
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
            self._tac.get_value('app_size', invalid_key)

        ex = str(cm.exception)
        msg = f"The key '{invalid_key}' was found, {ex}"
        self.assertIn('invalid', ex, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
           _TMP_USER_APP_FILE)
    def test_update_app_config(self):
        """
        Test that a value can be updated.

        File should contain the following data:
        {'app_size': {'default': [530, 830], 'size': [530, 830]}}
        """
        self.create_config()
        # Test that the 'default' value is the default.
        value = self._tac.get_value('app_size', 'default')
        expected = TomlAppConfig._DEFAULT_SCREEN_SIZE
        msg = f"Expected '{expected}' found '{value}'."
        self.assertEqual(expected, value, msg)

        # Test that the update works properly.
        changed_value = [600, 900]
        self._tac.update_app_config('app_size', 'default', changed_value)
        value = self._tac.get_value('app_size', 'default')
        msg = f"Expected '{changed_value}' found '{value}'."
        self.assertEqual(changed_value, value, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
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
            value = self._tac.get_value('app_size', new_key)

        ex = str(cm.exception)
        msg = f"The key '{new_key}' was found, {ex}"
        self.assertIn(new_key, ex, msg)

        # Test that the new key can be added and found.
        new_value = 'Test Value'
        self._tac.update_app_config('app_size', new_key, new_value)
        value = self._tac.get_value('app_size', new_key)
        msg = f"Expected '{new_value}' found '{value}'."
        self.assertEqual(new_value, value, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
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
            value = self._tac.get_value(new_table, new_key)

        ex = str(cm.exception)
        msg = f"The table '{new_table}' was found, {ex}"
        self.assertIn(new_table, ex, msg)

        # Test that the new table and key can be added and found.
        new_value = 'Test Value'
        self._tac.update_app_config(new_table, new_key, new_value)
        value = self._tac.get_value(new_table, new_key)
        msg = f"Expected '{new_value}' found '{value}'."
        self.assertEqual(new_value, value, msg)

    #@unittest.skip("Temporarily skipped")
    @patch('src.config.TomlAppConfig.user_app_config_fullpath',
           _TMP_UNWRITABE_PATH)
    def test__write_file_open_failed(self):
        """
        Test that writing to a file fails when a unwritable path is provided.
        """
        with self.assertRaises(PermissionError) as cm:
            self._tac._write_file('Invalid path')

        ex = str(cm.exception)
        msg = (f"The file '{self._TMP_UNWRITABE_PATH}' could not be "
               f"written, {ex}")
        self.assertIn(self._TMP_UNWRITABE_PATH, ex, msg)


class TestTomlCreatePanel(BaseTomlTest):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        check_flag(self.__class__.__name__)
        super().setUp()
        self._tcp = TomlCreatePanel()

    def create_toml_doc(self):
        full_path = os.path.join(BASE_DIR, 'tests', 'test_panel.toml')

        with open(full_path, mode='r') as f:
            data = f.read()

        return tk.loads(data)

    #@unittest.skip("Temporarily skipped")
    def test_set_and_get_current_panel(self):
        """
        Test both the setter and getter for the current_panel properties.
        """
        expect = self.create_toml_doc()
        self._tcp.current_panel = expect
        value = self._tcp.current_panel
        msg = f"Expected {expect}, found {value}."
        self.assertEqual(expect, value, msg)

    #@unittest.skip("Temporarily skipped")
    def test_all_field_names(self):
        """
        Test that the all_field_names property returns all the names of
        all panels.
        """
        number_of_widgets = 13
        err_msg = "There is no panel that is currently being worked on."

        try:
            self._tcp.all_field_names
        except AssertionError as e:
            self.assertEqual(err_msg, str(e))

        items = self.create_toml_doc().get('organization',
                                           {}).get('widgets', {})
        self._tcp.current_panel = items
        names = self._tcp.all_field_names
        msg = f"Expected {number_of_widgets}, found {len(names)}."
        self.assertEqual(number_of_widgets, len(names), msg)

    #@unittest.skip("Temporarily skipped")
    def test_field_names(self):
        """
        Test that the field_names property returns the field names of a
        specified panel.
        """
        number_of_widgets = 5
        items = self.create_toml_doc().get('organization',
                                           {}).get('widgets', {})
        self._tcp.current_panel = items
        names = self._tcp.field_names
        msg = f"Expected {number_of_widgets}, found {len(names)}."
        self.assertEqual(number_of_widgets, len(names), msg)

    #@unittest.skip("Temporarily skipped")
    def test_field_names_by_category(self):
        """
        Test that the field_names_by_category property returns the field
        names by category.
        """
        cat0 = 'Locality Prefix'
        cat1 = ('The following Location field is needed to determine '
                'the timezone.')
        data = (
            (cat0, 4),
            (cat1, 1),
            )
        msg = "Expected {}, found {}."
        items = self.create_toml_doc().get('organization',
                                           {}).get('widgets', {})
        self._tcp.current_panel = items

        for cat, expected_result in data:
            names = self._tcp.field_names_by_category.get(cat)
            self.assertEqual(expected_result, len(names), msg.format(
                expected_result, len(names)))
