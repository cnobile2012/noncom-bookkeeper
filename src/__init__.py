# -*- coding: utf-8 -*-
#
# src/__init__.py
#
__docformat__ = "restructuredtext en"

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

__all__ = ('Logger',)


class Logger:
    """
    Setup some basic logging.
    """
    _DEFAULT_FORMAT = ("%(asctime)s %(levelname)s %(name)s %(module)s "
                       "%(funcName)s [line:%(lineno)d] %(message)s")
    _ASSERT_MSG = "The 'config()' method must be called first."

    def __init__(self, format_str=None):
        self._format = format_str if format_str else self._DEFAULT_FORMAT
        self.logger = None

    def config(self, logger_name=None, file_path=None, max_bytes=5000000,
               backup_count=5, level=logging.INFO, initial_msg=True):
        """
        Config the logger.

        :param str logger_name: The name of the specific logger needed.
        :param str file_path: The path to the logging file. If left as None
                              logging will be to the screen.
        :param int max_bytes: The rollover bytes.
        :param int backup_count: The number of files before they are deleted.
        :param int level: The lowest level to generate logs for. See the
                          Python logger docs.
        :param bool initial_msg: Print the initial log message. The default
                                 is True.
        """
        if logger_name and file_path:
            self._make_log_dir(file_path)
            self.logger = logging.getLogger(logger_name)
            self.logger.handlers.clear()
            self.logger.setLevel(level)
            handler = RotatingFileHandler(file_path, maxBytes=max_bytes,
                                          backupCount=backup_count)
            formatter = logging.Formatter(self._format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        elif file_path:  # Creates a file root logger.
            self._make_log_dir(file_path)
            logging.basicConfig(filename=file_path, format=self._format,
                                level=level, force=True)
            self.logger = logging.getLogger()
        else:  # Creates a stdout root logger.
            logging.basicConfig(stream=sys.stdout, format=self._format,
                                level=level, force=True)
            self.logger = logging.getLogger()

        if logger_name:
            log = logging.getLogger(logger_name)
        else:
            log = logging.getLogger()

        if initial_msg:
            log.info("Logging start for %s.", logger_name)

    def _make_log_dir(self, full_path):
        path, filename = os.path.split(full_path)

        if not os.path.exists(path):
            os.mkdir(path)

    @property
    def level(self):
        assert self.logger, self._ASSERT_MSG
        return self.logger.getEffectiveLevel()

    @level.setter
    def level(self, level):
        assert self.logger, self._ASSERT_MSG
        self.logger.setLevel(level)
