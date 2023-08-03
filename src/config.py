# -*- coding: utf-8 -*-
#
# src/config.py
#
__docformat__ = "restructuredtext en"

import os
import logging
import shutil
from appdirs import AppDirs

from .exceptions import InvalidTomlException

import tomlkit


class Settings(AppDirs):
    """
    This class has all the default app, file, and log names used bye the
    system.
    """
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _APP_NAME = "NC-Bookkeeper"
    _DEVELOPERS = ('Carl J. Nobile',)
    _LOGGER_NAME = "NC-Bookkeeper"
    _LOGFILE_NAME = "ncbookkeeper.log"
    _LOCAL_CONFIG = os.path.join(_BASE_DIR, 'config')
    _DATA_FILE = 'data.sqlite3'
    _CONFIG_FILES = {'local': {'bahai': 'default_bahai.toml',
                               'generic': 'default_generic.toml'},
                     'user': {'bahai': 'bahai.toml',
                              'generic': 'generic.toml'}}
    _ALREADY_RUN = False

    def __init__(self):
        super().__init__(appname=self.app_name,
                         appauthor=self.primary_developer)
        # The two lines below read an environment variable whicj is used
        # during the app build process.
        value = os.environ.get('NCB_TYPE', 'bahai')
        self.__user_toml = self._CONFIG_FILES['user'][value]
        self.__local_toml = self._CONFIG_FILES['local'][value]

    def create_dirs(self):
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir, mode=0o775, exist_ok=True)

        if not os.path.exists(self.user_config_dir):
            os.makedirs(self.user_config_dir, mode=0o775, exist_ok=True)

        if not os.path.exists(self.user_cache_dir):
            os.makedirs(self.user_cache_dir, mode=0o775, exist_ok=True)

        if not os.path.exists(self.user_log_dir):
            os.makedirs(self.user_log_dir, mode=0o775, exist_ok=True)

    @property
    def already_run(self):
        return self._ALREADY_RUN

    @already_run.setter
    def already_run(self, value):
        assert isinstance(value, bool), (f"The 'already_run' value '{value}'"
                                         f" is not a boolean.")
        self._ALREADY_RUN = value

    @property
    def primary_developer(self):
        return self._DEVELOPERS[0]

    @property
    def app_name(self):
        return self._APP_NAME

    @property
    def contributors(self, array=False):
        result = None

        if array:
            result = self._DEVELOPERS
        else:
            result = ''.join([s+'\n' for s in self._DEVELOPERS]).strip()

        return result

    @property
    def logger_name(self):
        return self._LOGGER_NAME

    @property
    def logfile_name(self):
        return self._LOGFILE_NAME

    @property
    def data_file_name(self):
        return self._DATA_FILE

    @property
    def user_data_fullpath(self):
        return os.path.join(self.user_data_dir, self.data_file_name)

    @property
    def user_config_fullpath(self):
        return os.path.join(self.user_config_dir, self.__user_toml)

    @property
    def user_log_fullpath(self):
        return os.path.join(self.user_log_dir, self.logfile_name)

    @property
    def local_config_fullpath(self):
        return os.path.join(self._LOCAL_CONFIG, self.__local_toml)


class BaseSystemData(Settings):
    """
    This base class writes and reads config files and is used
    in all the types of config subclasses.
    """
    SYS_FILES = {'data': None, 'config': None}

    def __init__(self):
        super().__init__()
        self._log = logging.getLogger(self.logger_name)

    ## @property
    ## def data(self):
    ##     return self.SYS_FILES.get('data')

    ## @data.setter
    ## def data(self, value):
    ##     self.SYS_FILES['data'] = value

    @property
    def config(self):
        return self.SYS_FILES.get('config')

    @config.setter
    def config(self, value):
        self.SYS_FILES['config'] = value

    def parse_toml(self):
        raw_doc = None
        errors = []
        # The order of the tuple below is important.
        user_local = ('user_config_fullpath', 'local_config_fullpath')

        for file_type in user_local:
            with open(getattr(self, file_type),'r') as f:
                raw_doc = f.read()

            try:
                doc = tomlkit.parse(raw_doc)
            except tomlkit.exceptions.TOMLKitError as e:
                self._log.error("TOML error: %s", str(e))
                errors.append(file_type)
                continue
            else:
                if 'user_config' in file_type:
                    self.config = doc
                elif self.config is None and 'local_config' in file_type:
                    # Executed only on first run.
                    self.config = doc

        return errors

class TomlConfig(BaseSystemData):
    """
    Read and write the TOML config file.
    """
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state
        super().__init__()

    @property
    def is_valid(self):
        ret = True
        errors = self.parse_toml()

        for error in errors:
            if error == 'user_config_fullpath':
                # Backup bad file then over write the original with the default.
                fname = self.user_config_fullpath
                bad_file = f'{fname}.bad'
                shutil.copy2(fname, bad_file)
                shutil.copy2(self.local_config_fullpath, fname)
                msg = ("Found an invalid config file and reverted "
                       "to the default version. The original bad file has "
                       f"been backed up to {bad_file}.")
                self._log.warning(msg)
                # *** TODO *** This needs to be shown on the screen if detected.
            else:
                msg = (f"The file {getattr(self, error)} could not be "
                       f"parsed. It will need to be replaced.")
                self._log.warning(msg)
                # *** TODO *** This needs to be shown on the screen if detected.
                ret = False

        return ret

class Database(BaseSystemData):
    pass
