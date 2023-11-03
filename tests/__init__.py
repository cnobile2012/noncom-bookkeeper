# Create loging object.

import os
import logging

from .base_dir import BASE_DIR
from src import Logger

from .fixtures import FakeWidget, FakeEvent


def setup_logging():
    LOGGER_NAME = 'config'
    filename = 'config.log'
    full_path = os.path.abspath(os.path.join(BASE_DIR, 'logs', filename))
    logger = Logger()
    logger.config(LOGGER_NAME, full_path, logging.DEBUG, initial_msg=False)
    return logging.getLogger(LOGGER_NAME)

log = setup_logging()


def initial_log_message(message, *args, **kwargs):
    log.info(message, *args, **kwargs)


def get_path():
    return os.path.join(BASE_DIR, 'tests')


RUN_FLAG = {'TestBootstrap': False,
            'TestLogger': False,
            'TestBases': False,
            'TestSettings': False,
            'TestBaseSystemData': False,
            'TestTomlMetaData': False,
            'TestTomlPanelConfig': False,
            'TestTomlAppConfig': False,
            'TestTomlCreatePanel': False,
            'TestExceptions': False}


def check_flag(name):
    if not RUN_FLAG[name]:
        initial_log_message("Start logging for %s", name)
        RUN_FLAG[name] = True


__all__ = (log, get_path, check_flag, FakeWidget, FakeEvent)
