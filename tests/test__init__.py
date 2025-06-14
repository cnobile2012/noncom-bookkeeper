# -*- coding: utf-8 -*-
#
# test/test__init__.py
#
__docformat__ = "restructuredtext en"

import io
import logging
import os
import unittest
from contextlib import redirect_stdout
from testfixtures import LogCapture

from . import check_flag
from src import Logger


class TestLogger(unittest.TestCase):
    """
    https://testfixtures.readthedocs.io/en/latest/logging.html
    """
    _TMP_LOGGER_FILE = '/tmp/test_logger.log'

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)

    def tearDown(self):
        logging.shutdown()

        try:
            os.remove(self._TMP_LOGGER_FILE)
        except FileNotFoundError:
            pass

    def create_buffer(self, **kwargs):
        """
        Creates a StringIO buffer for tests.
        """
        logger_name = kwargs.pop('logger_name', '')
        test_msg_1 = kwargs.pop('test_msg_1', '')
        test_msg_2 = kwargs.pop('test_msg_2', '')
        cb = kwargs.pop('callback', None)
        data = ''

        with io.StringIO() as buff:
            with redirect_stdout(buff) as buff:
                logger = Logger()
                logger.config(**kwargs)
                log = logging.getLogger(logger_name)
                if test_msg_1: log.info(test_msg_1)
                result = cb(logger, log, test_msg_2) if cb else None

            data = buff.getvalue()

        return data, result

    #@unittest.skip("Temporarily skipped")
    def test_config_normal_usage(self):
        """
        Test that with both the 'loger_name' and 'file_path' arguments
        a logger object is created.
        """
        name = 'TestName'

        with LogCapture() as l:
            Logger().config(logger_name=name, file_path=self._TMP_LOGGER_FILE,
                            initial_msg=False)

            log = logging.getLogger(name)
            test_msg = "Test logging"
            log.info(test_msg)
            data = ""

            with open(self._TMP_LOGGER_FILE, 'r') as f:
                data = f.read()

            msg = (f"Should find a {name} logger with {test_msg} found "
                   f"in {data}")
            self.assertIn(test_msg, data, msg)
            self.assertIn(name, data, msg)

        l.uninstall()

    #@unittest.skip("Temporarily skipped")
    def test_config_root_logger_to_file(self):
        """
        Test that with only the 'file_path' argument a root logger
        object is created.
        """
        Logger().config(file_path=self._TMP_LOGGER_FILE, initial_msg=False)
        log = logging.getLogger()
        test_msg = "Test logging to file."
        log.info(test_msg)
        data = ""

        with open(self._TMP_LOGGER_FILE, 'r') as f:
            data = f.read()

        name = 'root'
        msg = (f"Should find a {name} logger with {test_msg} found "
               f"in {data}")
        self.assertIn(test_msg, data, msg)
        self.assertIn(name, data, msg)

    @unittest.skip("Temporarily skipped")
    def test_config_root_logger_to_stdout(self):
        """
        Test that with neither 'loger_name' or 'file_path' arguments
        a root logger object is created to stdout.
        """
        test_msg_1 = "Test logging to stream."
        kwargs = {'test_msg_1': test_msg_1, 'initial_msg': False}
        data, result = self.create_buffer(**kwargs)
        name = 'root'
        msg = (f"Should find a {name} logger with '{test_msg_1}' "
               f"found in {data}")
        self.assertIn(test_msg_1, data, msg)
        self.assertIn(name, data, msg)

    @unittest.skip("Temporarily skipped")
    def test_level_get(self):
        """
        Test that getting a new level works properly.
        """
        def callback(logger, log, msg):
            return logging.getLevelName(logger.level)

        name = 'TestName'
        kwargs = {'callback': callback, 'logger_name': name,
                  'initial_msg': False}
        data, found_level = self.create_buffer(**kwargs)
        should_be_level = logging.getLevelName(logging.INFO)
        msg = (f"The logging level should be '{should_be_level}' "
               f"found '{found_level}'")
        self.assertEqual(should_be_level, found_level, msg)

    @unittest.skip("Temporarily skipped")
    def test_level_set(self):
        """
        Test that setting a new level works properly.
        """
        def callback(logger, log, msg):
            logger.level = logging.WARNING
            log.info(msg)  # should_not_be_in_log message

        name = 'TestLoggerName'
        should_be_in_log = "This message should be in the log file."
        should_not_be_in_log = "This message should not be in the log file."
        kwargs = {'callback': callback, 'test_msg_1': should_be_in_log,
                  'test_msg_2': should_not_be_in_log, 'logger_name': name,
                  'initial_msg': False}
        data, result = self.create_buffer(**kwargs)
        msg = f"Could not fine '{should_be_in_log}' in log file '{data}'"
        self.assertIn(should_be_in_log, data, msg)
        msg = f"Could not fine '{should_not_be_in_log}' in log file '{data}'"
        self.assertNotIn(should_not_be_in_log, data, msg)
