# -*- coding: utf-8 -*-
#
# src/config.py
#
__docformat__ = "restructuredtext en"

import os
import re
import logging
import shutil
from datetime import datetime
from appdirs import AppDirs

import tomlkit as tk

from .bases import find_dict
from .utilities import Borg


class Settings(AppDirs, Borg):
    """
    This class has all the default app, file, and log names used bye the
    system.
    """
    _DEBUG = False
    _TESTING = False
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _APP_NAME = "nc-bookkeeper"
    _DEVELOPERS = ('Carl J. Nobile',)
    _LOGGER_NAME = "ncb"
    _LOGFILE_NAME = "ncbookkeeper.log"
    _LOCAL_CONFIG = os.path.join(_BASE_DIR, 'config')
    _DATA_FILE = 'data.sqlite3'
    _PANEL_FACTORY_DIR = 'factory'
    _CONFIG_FILES = {'local': {'bahai': 'default_bahai.toml',
                               'generic': 'default_generic.toml'},
                     'user': {'bahai': 'bahai.toml',
                              'generic': 'generic.toml'}}

    # Even if not in debug mode these two variables need to be defined
    # or the Borg won't like it and you may get assimilated.
    _debug_data_dir = ''
    _debug_log_dir = ''
    _testing_data_dir = ''

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(appname=self.app_name,
                         appauthor=self.primary_developer, *args, **kwargs)
        # The three lines below read an environment variable which is used
        # during the app build process. The default is to use the Baha'i
        # configuration.
        self.__config_type = os.environ.get('NCB_TYPE', 'bahai')
        self.__user_toml = self._CONFIG_FILES['user'][self.__config_type]
        self.__local_toml = self._CONFIG_FILES['local'][self.__config_type]
        # Setup the logger for this module.
        self.__app_toml = 'nc-bookkeeper.toml'
        self._log = logging.getLogger(self.logger_name)
        self.log_level = logging.INFO

    def create_dirs(self) -> None:
        """
        Create the directory tree based on the debug, testing, or absence
        of these flags.
        """
        if self.debug:
            self._debug_data_dir = os.path.join(self._BASE_DIR, 'data')
            self._debug_log_dir = os.path.join(self._debug_data_dir, 'log')

            if not os.path.exists(self._debug_data_dir):  # pragma: no cover
                os.makedirs(self._debug_data_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self._debug_log_dir):  # pragma: no cover
                os.makedirs(self._debug_log_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.cached_factory_dir):  # pragma: no cover
                os.makedirs(self.cached_factory_dir, mode=0o775, exist_ok=True)

            paths = (self._debug_data_dir, self._debug_log_dir,
                     self.cached_factory_dir)
        elif self.testing:
            self._testing_data_dir = os.path.join(
                self._BASE_DIR, 'tests', 'data')

            if not os.path.exists(self._testing_data_dir):  # pragma: no cover
                os.makedirs(self._testing_data_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.cached_factory_dir):  # pragma: no cover
                os.makedirs(self.cached_factory_dir, mode=0o775, exist_ok=True)

            paths = (self._testing_data_dir, self.cached_factory_dir)
        else:
            if not os.path.exists(self.user_data_dir):  # pragma: no cover
                os.makedirs(self.user_data_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.user_config_dir):  # pragma: no cover
                os.makedirs(self.user_config_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.user_cache_dir):  # pragma: no cover
                os.makedirs(self.user_cache_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.user_log_dir):  # pragma: no cover
                os.makedirs(self.user_log_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.cached_factory_dir):  # pragma: no cover
                os.makedirs(self.cached_factory_dir, mode=0o775, exist_ok=True)

            paths = (self.user_data_dir, self.user_config_dir,
                     self.user_cache_dir, self.user_log_dir,
                     self.cached_factory_dir)

        self._log.info("Created, if necessary, the following paths: %s", paths)

    @property
    def log_level(self) -> int:
        return self._log.level

    @log_level.setter
    def log_level(self, level: int) -> None:
        self._log.setLevel(level)

    @property
    def debug(self) -> bool:
        return self._DEBUG

    @debug.setter
    def debug(self, value: bool) -> None:
        self._DEBUG = value

    @property
    def testing(self) -> bool:
        return self._TESTING

    @testing.setter
    def testing(self, value: bool) -> None:
        self._TESTING = value

    @staticmethod
    def base_dir() -> str:
        return Settings._BASE_DIR

    @property
    def app_name(self) -> str:
        return self._APP_NAME

    @property
    def primary_developer(self) -> str:
        return self._DEVELOPERS[0]

    def contributors(self, array: bool=False) -> str | tuple:
        result = None

        if array:
            result = self._DEVELOPERS
        else:
            result = ''.join([s+'\n' for s in self._DEVELOPERS]).strip()

        return result

    @property
    def logger_name(self) -> str:
        return self._LOGGER_NAME

    @property
    def logfile_name(self) -> str:
        return self._LOGFILE_NAME

    @property
    def data_file_name(self) -> str:
        return self._DATA_FILE

    @property
    def panel_factory_name(self) -> str:
        return self._PANEL_FACTORY_DIR

    @property
    def user_data_fullpath(self) -> str:
        if self.debug:
            path = os.path.join(self._debug_data_dir, self.data_file_name)
        elif self.testing:
            path = os.path.join(self._testing_data_dir, self.data_file_name)
        else:
            path = os.path.join(self.user_data_dir, self.data_file_name)

        assert 'data' in path or '.local' in path, (
            f"user_data_fullpath: {path}")
        return path

    @property
    def user_config_fullpath(self) -> str:
        if self.debug:
            path = os.path.join(self._debug_data_dir, self.__user_toml)
        elif self.testing:
            path = os.path.join(self._testing_data_dir, self.__user_toml)
        else:
            path = os.path.join(self.user_config_dir, self.__user_toml)

        assert 'data' in path or '.config' in path, (
            f"user_config_fullpath: {path}")
        return path

    @property
    def user_app_config_fullpath(self) -> str:
        if self.debug:
            path = os.path.join(self._debug_data_dir, self.__app_toml)
        elif self.testing:
            path = os.path.join(self._testing_data_dir, self.__app_toml)
        else:
            path = os.path.join(self.user_config_dir, self.__app_toml)

        assert 'data' in path or '.config' in path, (
            f"user_app_config_fullpath: {path}")
        return path

    @property
    def user_log_fullpath(self) -> str:  # pragma: no cover
        if self.debug:
            path = os.path.join(self._debug_log_dir, self.logfile_name)
        else:
            path = os.path.join(self.user_log_dir, self.logfile_name)

        assert 'data' in path or '.cache' in path, (
            f"user_log_fullpath: {path}")
        return path

    @property
    def cached_factory_dir(self) -> str:
        if self.debug:
            path = os.path.join(self._debug_data_dir, self.panel_factory_name)
        elif self.testing:
            path = os.path.join(self._testing_data_dir,
                                self.panel_factory_name)
        else:
            path = os.path.join(self.user_cache_dir, self.panel_factory_name)

        assert 'data' in path or '.cache' in path, (
            f"cached_factory_dir: {path}")
        return path

    @property
    def local_config_fullpath(self) -> str:
        return os.path.join(self._LOCAL_CONFIG, self.__local_toml)

    @property
    def config_type(self) -> str:
        return self.__config_type


class BaseSystemData(Settings):
    """
    This base class writes and reads config files and is used
    in all the types of config sub-classes.
    """
    SYS_FILES = {'data': None, 'panel_config': None, 'app_config': None}
    # Error conditions
    ERR_FILE_NOT_FOUND = 1    # Cannot find file
    ERR_TOML_ERROR = 2        # TOML error, maybe corrupted
    ERR_ZERO_LENGTH_FILE = 3  # Zero length file
    ERR_UNKNOWN_ERROR = 4     # Could be any of PermissionError, IOError,
                              # OSError
    ERR_MESSAGES = {
        ERR_FILE_NOT_FOUND: "File '{}' not found.",
        ERR_TOML_ERROR: "Cannot parse file '{}' may be corrupted.",
        ERR_ZERO_LENGTH_FILE: "Cannot parse zero length file '{}'.",
        ERR_UNKNOWN_ERROR: "Critical unknown error."
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__err_msg = None
        self.__error = None

    @property
    def panel_config(self) -> tk.TOMLDocument | None:
        """
        Get the entire TOML doc for the panels.

        :returns: The TOML document.
        :rtype: tk.TOMLDocument or None
        """
        return self.SYS_FILES.get('panel_config')

    @panel_config.setter
    def panel_config(self, value) -> None:
        """
        Set the entire TOML doc for the panels.

        :param tk.TOMLDocument value: The TOML doc.
        """
        self.SYS_FILES['panel_config'] = value

    @property
    def app_config(self):
        return self.SYS_FILES.get('app_config')

    @app_config.setter
    def app_config(self, value):
        self.SYS_FILES['app_config'] = value

    def parse_toml(self, filepath: str) -> tk.TOMLDocument | int:
        """
        Open and read the specified TOML file.

        :param str filepath: The file to open and read.
        :returns: TOML doc if no error or a tuple (errmsg, errcode) if
                  an error.
        :rtype: tk.TOMLDocument or int
        """
        error = doc = None

        try:
            with open(filepath, 'r') as f:
                raw_doc = f.read()
        except FileNotFoundError as e:
            msg = self.ERR_MESSAGES[self.ERR_FILE_NOT_FOUND].format(filepath)
            self._log.error(msg[:-1] + ", %s", e)
            error = self.ERR_FILE_NOT_FOUND
        else:
            if raw_doc != "":
                try:
                    doc = tk.parse(raw_doc)
                except tk.exceptions.TOMLKitError as e:
                    msg = self.ERR_MESSAGES[
                        self.ERR_TOML_ERROR].format(filepath)
                    self._log.error(msg[:-1] + ", %s", e)
                    error = self.ERR_TOML_ERROR
            else:
                msg = self.ERR_MESSAGES[
                    self.ERR_ZERO_LENGTH_FILE].format(filepath)
                self._log.error(msg)
                error = self.ERR_ZERO_LENGTH_FILE

        return error if error else doc

    @property
    def err_msg(self) -> str:
        return self.__err_msg

    @err_msg.setter
    def err_msg(self, msg: str) -> None:
        self.__err_msg = msg

    @property
    def error(self) -> int:
        return self.__error

    @error.setter
    def error(self, err: int) -> None:
        self.__error = err


class TomlMetaData(BaseSystemData):
    """
    Get the META data from the TOML panel config file.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def title(self) -> str:
        return self.panel_config.get('meta', {}).get('title')

    @property
    def panels(self):
        return self.panel_config.get('meta', {}).get('panels')

    @property
    def locale_prefix(self):
        return self.panel_config.get('meta', {}).get('locale_prefix')

    @property
    def font_16_bold(self) -> list:
        return self.panel_config.get('meta', {}).get('font_16_bold')

    @property
    def font_14_bold(self) -> list:
        return self.panel_config.get('meta', {}).get('font_14_bold')

    @property
    def font_12_normal(self) -> list:
        return self.panel_config.get('meta', {}).get('font_12_normal')

    @property
    def font_12_bold(self) -> list:
        return self.panel_config.get('meta', {}).get('font_12_bold')

    @property
    def font_10_normal(self) -> list:
        return self.panel_config.get('meta', {}).get('font_10_normal')

    @property
    def font_10_bold(self) -> list:
        return self.panel_config.get('meta', {}).get('font_10_bold')

    def get_font(self, font_type):
        try:
            return getattr(self, font_type)
        except AttributeError as e:
            self._log.error("Invalid font_type, found '%s', %s", font_type, e)

    @property
    def data_entry_title_data(self):
        return self.panel_config.get('meta', {}).get('data_entry_titles')

    @property
    def data_entry_labels(self):
        return self.panel_config.get('meta', {}).get('data_entry_labels')


class TomlPanelConfig(BaseSystemData):
    """
    Read and write the TOML panel config file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._backup_file = f"{self.user_config_fullpath}.bak"

    @property
    def _has_user_config(self) -> bool:
        """
        Check if the user panel config exists.

        :returns: True if file exists and False if it does not exist.
        :rtype: bool
         """
        fullpath = self.user_config_fullpath

        if not (has := os.path.exists(fullpath)):
            msg = "The path '%s' does not exist, file will be copied."
            self._log.info(msg, fullpath)
            self.err_msg = msg

        return has

    @property
    def _has_local_config(self) -> bool:
        """
        Check if the local panel config exists. This is a fatal and
        critical error if it does not exist.

        :returns: True if file exists and False if it does not exist.
        :rtype: bool
        """
        fullpath = self.local_config_fullpath

        if not (has := os.path.exists(fullpath)):
            msg = "The path '%s' does not exist, exiting application."
            self._log.critical(msg, fullpath)
            self.err_msg = msg

        return has

    def initializing_config(self) -> None:
        """
        Initialize the config files.
        """
        if not self._has_user_config:
            if self._has_local_config:
                self._copy_file(self.local_config_fullpath,
                                self.user_config_fullpath)
                self._copy_file(self.local_config_fullpath, self._backup_file)
            else:  # pragma: no cover
                msg = ("The original config file could not be found, "
                       "you may need to contact the developer.")
                self._log.critical(msg)

    def recover_config(self) -> None:
        """
        Try to recover from damaged or missing config files.
        """
        if self.error:
            self._log.warning("Error: %s is corrupted, using the backup file.",
                              self.user_config_fullpath)
            # First try to copy the backup file to the user file.
            self._copy_file(self._backup_file, self.user_config_fullpath)

            if not self._validate():
                if self.error:
                    self.err_msg = self.ERR_MESSAGES[self.error].format(
                        self.user_config_fullpath)

                # Second try to copy the local file to the user file.
                # We need to remove any corrupted file fist.
                try:
                    os.remove(self.user_config_fullpath)
                except FileNotFoundError:
                    pass
                except Exception as e:  # pragma: no cover
                    self._log.warning(
                        "Error: %s could not remove the user file.",
                        self.user_config_fullpath)

                self.initializing_config()

    @property
    def is_valid(self) -> bool:
        return self._validate()

    def _validate(self) -> bool:
        """
        Read the TOML file and determine if it is valid.

        :returns: `True` if the file is valid and `False` if it is invalid.
        :rtype: bool
        """
        ret = True
        fullpath = self.user_config_fullpath
        self._read_toml_file(fullpath)

        if self.error:
            self.err_msg = self.ERR_MESSAGES[self.error].format(fullpath)
            ret = False

        return ret

    def _read_toml_file(self, filepath: str) -> None:
        """
        Open and read the local panel file.

        :param str filepath: The full path to the file that will be parsed.
        """
        doc = self.parse_toml(filepath)

        if isinstance(doc, int):  # Has an error
            self.error = doc  # If an error then doc is an error code.
        else:
            self.panel_config = doc
            self.error = None

    def _copy_file(self, fname0: str, fname1: str) -> None:
        """
        Copy the TOML config files.

        :param str fname0: File name that is to be copied.
        :param str fname1: File name to copy to.
        """
        try:
            shutil.copy2(fname0, fname1)
        except FileNotFoundError as e:
            self._log.error("Could not copy file %s to %s, %s",
                            fname0, fname1, e)
            self.error = self.ERR_FILE_NOT_FOUND
        except Exception as e:  # pragma: no cover
            self._log.error("Could not copy file %s to %s, %s",
                            fname0, fname1, e)
            self.error = self.ERR_UNKNOWN_ERROR


class TomlAppConfig(BaseSystemData):
    """
    Read and write the TOML app config file.
    """
    _FILE_LIST = ('user_app_config_fullpath',)
    _DEFAULT_SCREEN_SIZE = [570, 830]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def _has_app_user_config(self) -> bool:
        """
        Check if the user app config exists.

        :returns: True if file exists and False if it does not exist.
        :rtype: bool
        """
        fullpath = self.user_app_config_fullpath

        if not (has := os.path.exists(fullpath)):
            msg = "The path '%s' does not exist, file will be created."
            self._log.info(msg, fullpath)
            self.err_msg = msg

        return has

    def initializing_config(self) -> None:
        """
        Initialize the config files.
        """
        if not self._has_app_user_config:
            self._create_app_config()

    def recover_config(self) -> None:
        """
        Try to recover from damaged or missing config files.
        """
        if self.error:
            fullpath = self.user_app_config_fullpath
            self.err_msg = self.ERR_MESSAGES[self.error].format(fullpath)
            self._log.warning("Error: %s is corrupted, recreating file.",
                              fullpath)
            self._create_app_config()

    @property
    def is_valid(self) -> bool:
        """
        Test the app config file that it can be parsed and that it exists.
        This property always returns True.

        :returns: A `True` or `False` depending on the validity of the
                  toml file.
        :rtype: bool
        """
        return self._validate()

    def _validate(self) -> bool:
        """
        Read the TOML file and determine if it is valid.

        :returns: `True` if the file is valid and `False` if it is invalid.
        :rtype: bool
        """
        ret = True
        fullpath = self.user_app_config_fullpath
        self._read_toml_file(fullpath)

        if self.error:
            self.err_msg = self.ERR_MESSAGES[self.error].format(fullpath)
            ret = False

        return ret

    def _read_toml_file(self, filepath) -> None:
        """
        Open and read the local panel file. If successful store the toml
        document object.

        :param str filepath: The full path to the toml document file.
        """
        doc = self.parse_toml(filepath)
        assert doc, "Invalid document--possible coding error."

        if isinstance(doc, int):  # Has an error
            self.error = doc  # If an error then doc is an error code.
        else:
            self.app_config = doc
            self.error = None

    def _create_app_config(self) -> None:
        doc = tk.document()
        # Create header
        doc.add(tk.comment(""))
        doc.add(tk.comment("Noncommercial Accounting System config file."))
        doc.add(tk.comment(""))
        doc.add(tk.comment(f"Date Created: {datetime.now()}"))
        doc.add(tk.comment(""))
        doc.add(tk.nl())
        # Create app size
        app_size = tk.table()
        app_size.add('default', self._DEFAULT_SCREEN_SIZE)
        app_size.add('size', self._DEFAULT_SCREEN_SIZE)
        doc.add('app_size', app_size)
        self._write_file(tk.dumps(doc))

    def get_value(self, table: str, key: str) -> None:
        doc = self.app_config
        assert doc, f"The {doc=} must be a valid toml document."
        item_table = doc.get(table)
        have_keys = False

        if item_table:
            item_key = item_table.get(key)

            if item_key:
                have_keys = True
                return doc[table][key]

        msg = (f"Could not find the table '{table}' or key: '{key}' in "
               f"{self.user_app_config_fullpath}.")
        self._log.error(msg)
        assert have_keys, msg

    def update_app_config(self, table: str, key: str, value) -> None:
        doc = self.app_config
        item_table = doc.get(table)

        if item_table:
            item_key = item_table.get(key)

            if item_key:
                doc[table][key] = value
            else:
                item_table.add(key, value)
        else:
            item_table = tk.table()
            item_table.add(key, value)
            doc.add(table, item_table)

        self._write_file(tk.dumps(doc))

    def _write_file(self, data) -> None:
        try:
            with open(self.user_app_config_fullpath, 'w') as f:
                f.write(data)
        except (OSError, PermissionError) as e:
            msg = (f"Could not create the {self.user_app_config_fullpath} "
                   f"file, {str(e)}")
            self._log.critical(msg)
            raise e


class TomlCreatePanel(BaseSystemData):
    """
    Create an updated panel Toml file.
    """
    _KEY_NUM = re.compile(r"^.*_(?P<count>\d+)$")
    _LAST_CHANGED = None
    __panel = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def last_changed(self) -> tuple | None:
        return self._LAST_CHANGED

    @last_changed.setter
    def last_changed(self, change: tuple) -> None:
        self._LAST_CHANGED = change

    @property
    def current_panel(self):
        """
        Returns the Toml doc of the current panel.
        """
        return self.__panel

    @current_panel.setter
    def current_panel(self, current) -> tk.TOMLDocument:
        """
        Make a copy of the Toml doc for the current panel.

        :param tk.TOMLDocument current: The current panel's Toml doc.
        """
        self.__panel = current.copy()

    @property
    def all_field_names(self):
        """
        Get all field names.
        """
        assert self.__panel, (
            "There is no panel that is currently being worked on.")
        names = []

        for item in self.__panel.values():
            list_ = find_dict(item).get('args', [])

            if len(list_) >= 3 and list_[2] != '':
                names.append(list_[2])

        return names

    @property
    def field_names(self) -> list:
        """
        A list of field names not including title names.
        """
        return [name for name in self.all_field_names
                if name and name.endswith(':')]

    @property
    def field_names_by_category(self):
        items = {}
        last_name = 'no-cat'

        for name in self.all_field_names:
            if name and not name.endswith(':'):
                last_name = name
                items.setdefault(last_name, [])
            elif name:
                names = items.setdefault(last_name, [])
                names.append(name)

        return items

    def add_name(self, name: str, key_num: int=None) -> None:
        """
        Add the named StaticText and its companion the TextCtrl to the end
        of the current panel's section in the Toml file. If `key_num` is
        provided the `key_num is the x coordinate and 0 will be the y
        continent.

        :param str name: The value name of the StaticText widget.
        :param int key_num: The key number to use.
        """
        assert self.__panel, "Programming error: Current panel not set."

        if key_num is None:
            key_num = self._next_widget_num

        x, y = (key_num, 0)
        key = self._make_key(key_num)
        self.__panel[key] = [
            'StaticText', 'w_fg_color_1',
            {'args': ['self', 'ID_ANY', name],
             'min': [-1, -1],
             'add': [0, 'ALIGN_BOTTOM | LEFT | RIGHT | TOP', 6],
             'pos': [x, y],
             'span': [1, 1]}]
        key = self._make_key(key_num + 1)
        self.__panel[key] = [
            'TextCtrl', 'w_bg_color_1', 'w_fg_color_1',
            {'args': ['self', 'ID_ANY', ''], 'style': 'TE_RIGHT',
             'min': [-1, -1],
             'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP', 6],
             'pos': [x, y+1],
             'span': [1, 1]}]
        self.last_changed = (name, key_num, 'add')

    def hide_widget(self, label: str, *, undo: bool=False) -> None:
        """
        Hide the StaticText with the provided label and its companion
        the TextCtrl in the TOML doc.

        :param str label: The label of the StaticText widget.
        :param bool undo: If `False` (default) hide the widgets, else `True`
                          unhide the widgets.
        """
        key0, dict_ = self._find_label_in_panel(label)

        if key0 and dict_:
            # Update the StaticText
            dict_['hidden'] = False if undo else True
            # Update the CtrlText
            key_num = self._find_key_num(key0)
            key1 = self._make_key(key_num + 1)
            item = self.__panel[key1]
            dict_ = find_dict(item)
            dict_['hidden'] = False if undo else True
            self.last_changed = (label, 'hide')

    def rename_label(self, old_label: str, new_label: str) -> None:
        """
        Rename the field in the TOML doc.

        :param str old_label: The field to rename.
        :param str new_label: The new name for the field.
        """
        key, dict_ = self._find_label_in_panel(old_label)

        if key and dict_:
            list_ = dict_.get('args', [])
            list_[2] = new_label
            self.last_changed = (old_label, new_label, 'rename')

    def undo_change(self) -> None:
        """
        Undo last changed field.
        """
        if self.last_changed:
            type_ = self.last_changed[-1]

            if type_ == 'add':
                label, pos = self.last_changed[:2]
                key, dict_ = self._find_label_in_panel(label)
                w0 = self.__panel.pop(key)
                key_num = self._find_key_num(key)
                w1 = self.__panel.pop(self._make_key(key_num + 1))
                self.last_changed = None
            elif type_ == 'hide':
                self.hide_widget(self.last_changed[0], undo=True)
                self.last_changed = None
            elif type_ == 'rename':
                old_name, new_name = self.last_changed[:2]
                self.rename_label(new_name, old_name)
                self.last_changed = None

    def _find_label_in_panel(self, label: str) -> tuple:
        """
        With the widget label return the key and the data.

        :param str label: The widget label.
        :returns: The widget name (key) and data.
        :rtype: tuple
        """
        w_key = data = None

        for key, item in self.__panel.items():
            dict_ = find_dict(item)
            list_ = dict_.get('args', [])

            if label in list_:
                w_key = key
                data = dict_
                break

        return w_key, data

    def _reorder(self, panel: dict) -> tk.document:
        """
        Reorder the items in the TOML doc.

        :param tk.document panel: This is the currently worked on Toml doc
                                  for the panel.
        :returns: A reordered the TOML doc.
        :rtype: tk.document
        """
        keys = sorted(list(panel))
        doc = tk.document()

        for idx, key in enumerate(keys):
            value = panel[key]
            doc[self._make_key(idx)] = value

        return doc

    def _create_hole(self, start: int) -> None:
        """
        Create a hole in the widget panel doc. All widgets after the hole
        will get its key bumped up by two since there are always two widgets
        created together.

        :param int start: Where to start the reordering. Should be the widget
                          set that will be after the hole.
         """
        doc = tk.document()

        for key, value in self.__panel.item():
            old_num = self._find_key_num(key)

            if old_num != start:
                doc[key] = value
            else:
                new_key = self._make_key(old_num + 1)
                doc[new_key] = value

        self.__panel = doc

    @property
    def _next_widget_num(self) -> int:
        """
        Get the next widget key to be used when adding a new widget.

        :returns: The next widget number.
        :rtype: int
        """
        last_key = list(self.__panel.keys())[-1]
        return self._find_key_num(last_key) + 1

    def _find_key_num(self, key: int) -> int:
        """
        With the widget name (key) find the widget number (key_num).

        :param int key: The widget name. eg widget_01
        :returns: The number attached to the widget name. eg. For widget_01
                  the value of 1 is returned.
        :rtype: int
        """
        sre = self._KEY_NUM.search(key)
        assert sre is not None, f"The key '{key}' was an invalid."
        return int(sre.group('count'))

    def _make_key(self, key_num):
        return f"widget_{key_num:>02}"
