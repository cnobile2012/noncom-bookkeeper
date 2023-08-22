#
# src/__init__.py
#
__docformat__ = "restructuredtext en"

import os
import logging

from .config import Settings

__all__ = ('Logger',)


class Bootstrap(Settings):
    """
    Bootstrap the app. We create the directories that we need.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_dirs()


class Logger:
    """
    Setup some basic logging. This uses the borg patten, it's kind of like a
    singlton but has a side affect of assimulation.
    """
    _shared_state = {}
    _DEFAULT_FORMAT = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                       "[line:%(lineno)d] %(message)s")

    def __init__(self, format_str=None):
        self.__dict__ = self._shared_state
        self._format = format_str if format_str else self._DEFAULT_FORMAT
        self.logger = None

    def config(self, logger_name=None, file_path=None, level=logging.INFO):
        """
        Config the logger.

        :param logger_name: The name of the specific logger needed.
        :type logger_name: str
        :param file_path: The path to the logging file. If left as None
                          logging will be to the screen.
        :type file_path: str
        :param level: The lewest leven to generate lofs for. See the
                      Python logger docs.
        :type level: int
        """
        if logger_name and file_path:
            self.log_name = logger_name
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(level)
            handler = logging.FileHandler(file_path)
            formatter = logging.Formatter(self._format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            logging.basicConfig(filename=file_path, format=self._format,
                                level=level)

        if logger_name:
            log = logging.getLogger(logger_name)
        else:
            log = logging.getLogger()

        log.info("Logging start for %s.", Bootstrap().logger_name)

    @property
    def level(self, level):
        self.logger.setLevel(level)

# The lines below runs the Bootstrap class for the first time.
_logger = Logger()
_logger.config(logger_name=Bootstrap().logger_name,
               file_path=Bootstrap().user_log_fullpath)
