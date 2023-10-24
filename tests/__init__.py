# Create loging object.

import os
import logging

from .base_dir import BASE_DIR
from src import Logger


def setup_logging():
    LOGGER_NAME = 'configuration'
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


__all__ = (log, initial_log_message, get_path)
