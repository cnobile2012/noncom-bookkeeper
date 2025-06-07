# -*- coding: utf-8 -*-
#
# src/__init__.py
#
__docformat__ = "restructuredtext en"

import sys
import logging


__all__ = ('Logger',)


class Logger:
    """
    Setup some basic logging. This uses the borg patten, it's kind of like a
    singlton but has a side affect of assimulation.
    """
    _DEFAULT_FORMAT = ("%(asctime)s %(levelname)s %(name)s %(module)s "
                       "%(funcName)s [line:%(lineno)d] %(message)s")

    def __init__(self, format_str=None):
        self._format = format_str if format_str else self._DEFAULT_FORMAT
        self.logger = None

    def config(self, logger_name=None, file_path=None, level=logging.INFO,
               initial_msg=True):
        """
        Config the logger.

        :param logger_name: The name of the specific logger needed.
        :type logger_name: str
        :param file_path: The path to the logging file. If left as None
                          logging will be to the screen.
        :type file_path: str
        :param level: The lowest level to generate logs for. See the
                      Python logger docs.
        :type level: int
        :param initial_msg: Print the inital log message. The default is True.
        :type initial_msg: bool
        """
        if logger_name and file_path:
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(level)
            handler = logging.FileHandler(file_path)
            formatter = logging.Formatter(self._format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        elif file_path:  # Creates a file root logger.
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

    @property
    def level(self):
        assert self.logger, "The 'config()' method must be called first."
        return self.logger.getEffectiveLevel()

    @level.setter
    def level(self, level):
        assert self.logger, "The 'config()' method must be called first."
        self.logger.setLevel(level)
