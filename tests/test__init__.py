# -*- coding: utf-8 -*-
#
# test/test__init__.py
#
__docformat__ = "restructuredtext en"

import io
import logging
import os
import unittest
from testfixtures import LogCapture

from . import check_flag, BASE_DIR
from src import Logger

from .base_database_test import BaseTests


class TestLogger(BaseTests, unittest.TestCase):
    """
    https://testfixtures.readthedocs.io/en/latest/logging.html
    """
    LOG_PATH = os.path.join(BASE_DIR, 'logs')
    LOGGER_NAMES = ['test_logger', 'root']

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.logger = Logger()

    def tearDown(self):
        self.logger = None
        logging.shutdown()

        for log_name in self.LOGGER_NAMES:
            log = logging.getLogger(log_name)
            log.handlers.clear()

        for file in [file for file in os.listdir(self.LOG_PATH)
                     if file.startswith('testfile_')]:
            path = os.path.join(self.LOG_PATH, file)

            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    #@unittest.skip("Temporarily skipped")
    def test_config_rotating_logger(self):
        """
        Test that the config method properly configures the rotating file
        logging system.
        """
        name = 'test_logger'
        filepath = os.path.join(self.LOG_PATH, 'testfile_rotate.log')
        log_msg = ("Test" * 20 + " ") * 100
        expected = 3
        msg = "Expected '{}', found '{}'."
        self.logger.config(name, filepath, 500, 2)
        log = logging.getLogger(name)
        [log.info(m) for m in log_msg.split(' ')]
        files = [file for file in os.listdir(self.LOG_PATH)
                 if file.startswith('testfile_')]
        self.assertEqual(expected, len(files), msg.format(
            expected, len(files)))

    #@unittest.skip("Temporarily skipped")
    def test_config_basic_file_logger(self):
        """
        Test that the config method properly configures the basic file
        logging systems.
        """
        filepath = os.path.join(self.LOG_PATH, 'testfile_basic_file.log')
        msg = "Expected '{}', found '{}'."
        self.logger.config(file_path=filepath)
        log = logging.getLogger()
        log_msg = "Testing the basic file logger."
        log.warning(log_msg)
        full_log = self.read_text_file(filepath)
        result = self.find_text(full_log, log_msg, 1, full_log)
        self.assertIn(log_msg, result, msg.format(log_msg, result))

    #@unittest.skip("Temporarily skipped")
    def test_config_basic_stdout_logger(self):
        """
        Test that the config method properly configures the basic stdout
        logging systems.
        """
        msg = "Expected '{}', found '{}'."
        log_msg = "Testing the basic file logger."
        self.logger.config(initial_msg=False)

        with self.assertLogs(level="DEBUG") as cm:
            log = logging.getLogger()
            log.warning(log_msg)

        result = "\n".join(cm.output)
        self.assertIn(log_msg, result, msg.format(log_msg, result))

    #@unittest.skip("Temporarily skipped")
    def test__make_log_dir(self):
        """
        Test that the _make_log_dir method creates the logging path if needed.
        """
        fullpath = os.path.join(BASE_DIR, 'tests', 'delete', 'no_file.log')
        self.logger._make_log_dir(fullpath)
        path, filename = os.path.split(fullpath)
        stats = os.stat(path)
        self.assertEqual(4096, stats.st_size)
        os.rmdir(path)

    #@unittest.skip("Temporarily skipped")
    def test_level_setter_and_getter(self):
        """
        Test that the level setter and getter work properly.
        """
        err_msg = self.logger._ASSERT_MSG
        data = (
            (True, False, None, err_msg),
            (False, True, None, err_msg),
            (None, None, logging.DEBUG, logging.DEBUG),
            (None, None, logging.INFO, logging.INFO),
            )
        msg = "Expected '{}', found '{}'."

        for set_err, get_err, level, expected in data:
            if set_err:
                with self.assertRaises(AssertionError) as cm:
                    self.logger.level = logging.DEBUG

                result = str(cm.exception)
            elif get_err:
                with self.assertRaises(AssertionError) as cm:
                    self.logger.level

                result = str(cm.exception)
            else:
                self.logger.config(initial_msg=False)
                self.logger.level = level
                result = self.logger.level

            self.assertEqual(expected, result, msg.format(expected, result))
