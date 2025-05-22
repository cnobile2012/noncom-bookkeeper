# Create loging object.

import os
import logging

from .base_dir import BASE_DIR
from .fixtures import FakeFrame, FakeWidget, FakeEvent, FakePanel

__all__ = ('FakeFrame', 'FakeWidget', 'FakeEvent', 'FakePanel', 'log',
           'check_flag',)

LOGGER_NAME = 'config'
LOGFILE_NAME = 'config.log'


def setup_logging():
    from src import Logger

    full_path = os.path.abspath(os.path.join(BASE_DIR, 'logs', LOGFILE_NAME))
    logger = Logger()
    logger.config(LOGGER_NAME, full_path, logging.DEBUG, initial_msg=False)
    return logging.getLogger(LOGGER_NAME)


log = setup_logging()


def initial_log_message(message, *args, **kwargs):
    log.info(message, *args, **kwargs)


RUN_FLAG = {'TestBadiCalendarPopup': False,
            'TestBadiDateChangedEvent': False,
            'TestBootstrap': False,
            'TestFunctions': False,
            'TestLogger': False,
            'TestBases': False,
            'TestSettings': False,
            'TestBaseSystemData': False,
            'TestTomlMetaData': False,
            'TestTomlPanelConfig': False,
            'TestTomlAppConfig': False,
            'TestTomlCreatePanel': False,
            'TestExceptions': False,
            'TestFiscalSettings': False,
            'TestPaths': False,
            'TestCheckPanelConfig': False,
            'TestCheckAppConfig': False,
            'TestGridBagSizer': False,
            'TestConfirmationDialog': False,
            'Test_ClickPosition': False,
            'TestEventStaticText': False}


def check_flag(name):
    if not RUN_FLAG[name]:
        initial_log_message("Start logging for %s", name)
        RUN_FLAG[name] = True
