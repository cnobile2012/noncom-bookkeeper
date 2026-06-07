# Create loging object.

import os
import sys
import logging

from unittest.mock import patch, PropertyMock

from .fixtures import FakeFrame, FakeWidget, FakeEvent, FakePanel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

__all__ = ('FakeFrame', 'FakeWidget', 'FakeEvent', 'FakePanel', 'log',
           'check_flag', 'Settings', 'BaseSystemData', 'TomlMetaData',
           'TomlPanelConfig', 'TomlAppConfig', 'TomlCreatePanel')

LOGGER_NAME = 'config'
LOGFILE_NAME = 'config.log'
PATH = os.path.join(BASE_DIR, 'logs')


def setup_logging():
    from src import Logger

    log_path = os.path.abspath(os.path.join(BASE_DIR, 'logs'))

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    full_path = os.path.abspath(os.path.join(log_path, LOGFILE_NAME))
    logger = Logger()
    logger.config(LOGGER_NAME, full_path, logging.DEBUG, initial_msg=False)
    return logging.getLogger(LOGGER_NAME)


log = setup_logging()


def initial_log_message(message, *args, **kwargs):
    log.info(message, *args, **kwargs)


RUN_FLAG = {'TestBadiCalendarPopup': False,
            'TestBadiDateChangedEvent': False,
            'TestBaseFunctions': False,
            'TestBasePanel': False,
            'TestBaseGenerated': False,
            'TestCustomTextCtrl': False,
            'TestFunctions': False,
            'TestLogger': False,
            'TestSettings': False,
            'TestSettingsBorg': False,
            'TestBaseSystemData': False,
            'TestTomlMetaData': False,
            'TestTomlPanelConfig': False,
            'TestTomlAppConfig': False,
            'TestTomlCreatePanel': False,
            'TestExceptions': False,
            'TestFiscalSettings': False,
            'TestPaths': False,
            'TestGridBagSizer': False,
            'TestConfirmationDialog': False,
            'Test_ClickPosition': False,
            'TestEventStaticText': False,
            'TestDataPreperation': False,
            'TestCache': False}


def check_flag(name):
    if not RUN_FLAG[name]:
        initial_log_message("Start logging for %s", name)
        RUN_FLAG[name] = True


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
