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

    def __init__(self, *args, **kwargs):
        super().__init__(appname=self.app_name,
                         appauthor=self.primary_developer, *args, **kwargs)
        # The next two lines are needed for debug mode only.
        self._debug_data_dir = os.path.join(self._BASE_DIR, 'data')
        self._debug_log_dir = os.path.join(self._debug_data_dir, 'log')

        # The three lines below read an environment variable which is used
        # during the app build process. The default is to use the Baha'i
        # configuration.
        self.__config_type = os.environ.get('NCB_TYPE', 'bahai')
        self.__user_toml = self._CONFIG_FILES['user'][self.__config_type]
        self.__local_toml = self._CONFIG_FILES['local'][self.__config_type]

        # Setup the logger for this monule.
        self.__app_toml = 'nc-bookkeeper.toml'
        self._log = logging.getLogger(self.logger_name)

    def create_dirs(self):
        if not self._DEBUG:
            if not os.path.exists(self.user_data_dir):
                os.makedirs(self.user_data_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.user_config_dir):
                os.makedirs(self.user_config_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.user_cache_dir):
                os.makedirs(self.user_cache_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.user_log_dir):
                os.makedirs(self.user_log_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.cached_factory_dir):
                os.makedirs(self.cached_factory_dir, mode=0o775, exist_ok=True)

            paths = (self.user_data_dir, self.user_config_dir,
                     self.user_cache_dir, self.user_log_dir,
                     self.cached_factory_dir)
        else:
            if not os.path.exists(self._debug_data_dir):
                os.makedirs(self._debug_data_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self._debug_log_dir):
                os.makedirs(self._debug_log_dir, mode=0o775, exist_ok=True)

            if not os.path.exists(self.cached_factory_dir):
                os.makedirs(self.cached_factory_dir, mode=0o775, exist_ok=True)

            paths = (self._debug_data_dir, self._debug_log_dir)

        self._log.info("Created, if necessary, the following paths: %s", paths)

    @property
    def debug(self):
        return self._DEBUG

    @debug.setter
    def debug(self, value: bool):
        self._DEBUG = value

    @staticmethod
    def base_dir():
        return Settings._BASE_DIR

    @property
    def app_name(self):
        return self._APP_NAME

    @property
    def primary_developer(self):
        return self._DEVELOPERS[0]

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
    def panel_factory_name(self):
        return self._PANEL_FACTORY_DIR

    @property
    def user_data_fullpath(self):
        if self.debug:
            return os.path.join(self._debug_data_dir, self.data_file_name)
        else:
            return os.path.join(self.user_data_dir, self.data_file_name)

    @property
    def user_config_fullpath(self):
        if self.debug:
            return os.path.join(self._debug_data_dir, self.__user_toml)
        else:
            return os.path.join(self.user_config_dir, self.__user_toml)

    @property
    def user_app_config_fullpath(self):
        if self.debug:
            return os.path.join(self._debug_data_dir, self.__app_toml)
        else:
            return os.path.join(self.user_config_dir, self.__app_toml)

    @property
    def user_log_fullpath(self):
        if self.debug:
            return os.path.join(self._debug_log_dir, self.logfile_name)
        else:
            return os.path.join(self.user_log_dir, self.logfile_name)

    @property
    def cached_factory_dir(self):
        if self.debug:
            return os.path.join(self._debug_data_dir, self.panel_factory_name)
        else:
            return os.path.join(self.user_cache_dir, self.panel_factory_name)

    @property
    def local_config_fullpath(self):
        return os.path.join(self._LOCAL_CONFIG, self.__local_toml)

    @property
    def config_type(self):
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
    ERR_MESSAGES = {ERR_FILE_NOT_FOUND: "File '{}' not found.",
                    ERR_TOML_ERROR: "Cannot parse file '{}' may be corrupted.",
                    ERR_ZERO_LENGTH_FILE: "Cannot parse zero length file '{}'."
                    }

    @property
    def panel_config(self):
        """
        Get the entire TOML doc for the panels.

        :returns: The TOML document.
        :rtype: tk.toml_document.TOMLDocument
        """
        return self.SYS_FILES.get('panel_config')

    @panel_config.setter
    def panel_config(self, value):
        """
        Set the entire TOML doc for the panels.

        :param tk.toml_document.TOMLDocument value: The TOML doc.
        """
        self.SYS_FILES['panel_config'] = value

    @property
    def app_config(self):
        return self.SYS_FILES.get('app_config')

    @app_config.setter
    def app_config(self, value):
        self.SYS_FILES['app_config'] = value

    def parse_toml(self, filepath: str):
        """
        Open and read the specified TOML file.

        :param str filepath: The file to open and read.
        :return: TOML doc if no error or a tuple (errmsg, errcode) if an error.
        :rtype: TOLM doc or int
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


class TomlMetaData(BaseSystemData):
    """
    Get the META data from the TOML panel config file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def panels(self):
        return self.panel_config.get('meta', {}).get('panels')

    @property
    def months(self):
        return self.panel_config.get('meta', {}).get('months')

    @property
    def locale_prefix(self):
        return self.panel_config.get('meta', {}).get('locale_prefix')

    @property
    def font_16_bold(self):
        return self.panel_config.get('meta', {}).get('font_16_bold')

    @property
    def font_14_bold(self):
        return self.panel_config.get('meta', {}).get('font_14_bold')

    @property
    def font_12_normal(self):
        return self.panel_config.get('meta', {}).get('font_12_normal')

    @property
    def font_12_bold(self):
        return self.panel_config.get('meta', {}).get('font_12_bold')

    @property
    def font_10_normal(self):
        return self.panel_config.get('meta', {}).get('font_10_normal')

    @property
    def font_10_bold(self):
        return self.panel_config.get('meta', {}).get('font_10_bold')

    def get_font(self, font_type):
        try:
            return getattr(self, font_type)
        except AttributeError as e:
            self._log.error("Invalid font_type, found '%s', %s", font_type, e)


class TomlPanelConfig(BaseSystemData):
    """
    Read and write the TOML panel config file.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__error = None
        self.__err_msg = None

    @property
    def _has_local_config(self):
        """
        Check if the local panel config exists. This is a fatal and
        critical error if it does not exist.

        :returns: True if file exists and False if it does not exist.
        :rtype: bool
        """
        if not (has := os.path.exists(self.local_config_fullpath)):
            msg = (f"The path '{self.local_config_fullpath}' does not exist, "
                   "exiting application.")
            self._log.critical(msg)
            self.__err_msg = msg

        return has

    @property
    def _has_user_config(self):
        """
        Check if the user panel config exists.

        :returns: True if file exists and False if it does not exist.
        :rtype: bool
         """
        if not (has := os.path.exists(self.user_config_fullpath)):
            msg = (f"The path '{self.user_config_fullpath}' does not exist, "
                   "file will be coped.")
            self._log.info(msg)
            self.__err_msg = msg

        return has

    @property
    def is_valid(self):
        ret = True
        backup_file = f"{self.user_config_fullpath}.bak"
        count = 0

        while self._has_user_config and count < 2:
            count += 1
            self._read_file(self.user_config_fullpath)

            if self.__error:
                self.__err_msg = self.ERR_MESSAGES[self.__error].format(
                    self.local_config_fullpath)

                if count < 2:
                    self._log.warning(
                        "Error: %s is corrupted, using the backup file.",
                        self.user_config_fullpath)
                    self._copy_file(backup_file, self.user_config_fullpath)
                else:
                    ret = False
                    break
        else:
            if self._has_local_config:
                self._copy_file(self.local_config_fullpath,
                                self.user_config_fullpath)
                self._copy_file(self.local_config_fullpath, backup_file)
                self._read_file(self.user_config_fullpath)

                if self.__error:  # All these errors are critical.
                    self.__err_msg = self.ERR_MESSAGES[self.__error].format(
                        self.user_config_fullpath)
                    ret = False
            else:
                ret = False

        return ret

    @property
    def get_err_msg(self):
        return self.__err_msg

    def _read_file(self, filepath):
        """
        Open and read the local panel file.
        """
        doc = self.parse_toml(filepath)
        assert doc, "Invalid document--possible coding error."

        if isinstance(doc, int):  # Has an error
            self.__error = doc
        else:
            self.panel_config = doc
            self.__error = None

    def _copy_file(self, fname0, fname1):
        try:
            shutil.copy2(fname0, fname1)
        except Exception as e:
            self._log.error("Could not copy file %s to %s, %s",
                            fname0, fname1, e)
            raise e


class TomlAppConfig(BaseSystemData):
    """
    Read and write the TOML app config file.
    """
    _FILE_LIST = ('user_app_config_fullpath',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__error = None
        self.__err_msg = None

    @property
    def _has_user_config(self):
        """
        Check if the user app config exists.

        :returns: True if file exists and False if it does not exist.
        :rtype: bool
         """
        if not (has := os.path.exists(self.user_app_config_fullpath)):
            msg = (f"The path '{self.user_config_fullpath}' does not exist, "
                   "file will be coped.")
            self._log.info(msg)
            self.__err_msg = msg

        return has

    @property
    def is_valid(self):
        """
        Test the app config file that it can be parsed and that it exists.
        This property always returns True.
        """
        ret = True

        if self._has_user_config:
            ret = self.__loop_has_user_config()
        else:
            self._create_app_config()
            ret = self.__loop_has_user_config()

        return ret

    def __loop_has_user_config(self):
        count = 0
        ret = True

        while self._has_user_config and count < 2:
            count += 1
            self._read_file(self.user_app_config_fullpath)

            if self.__error:
                self.__err_msg = self.ERR_MESSAGES[self.__error].format(
                    self.user_app_config_fullpath)

                if count < 2:
                    self._log.warning(
                        "Error: %s is corrupted, recreating file.",
                        self.user_app_config_fullpath)
                    self._create_app_config()
                    count = 0
                else:
                    self._log.critical("The %s is corrupted beyond repair "
                                       "contact the developer.",
                                       self.user_app_config_fullpath)
                    ret = False

        return ret

    @property
    def get_err_msg(self):
        return self.__err_msg

    def _read_file(self, filepath):
        """
        Open and read the local panel file.
        """
        doc = self.parse_toml(filepath)
        assert doc, "Invalid document--possible coding error."

        if isinstance(doc, int):  # Has an error
            self.__error = doc
        else:
            self.app_config = doc
            self.__error = None

    def _create_app_config(self):
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
        app_size.add('default', [536, 830])
        app_size.add('size', [536, 830])
        doc.add('app_size', app_size)
        self._write_file(tk.dumps(doc))

    def get_value(self, table, key):
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

    def update_app_config(self, table, key, value):
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

    def _write_file(self, data):
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
    _last_removed = None
    __panel = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def current_panel(self):
        """
        Returns the Toml doc of the current panel.
        """
        return self.__panel

    @current_panel.setter
    def current_panel(self, current):
        """
        Make a copy of the Toml doc of the current panel.

        :param  current: The current panel's Toml doc.
        :type current: tomlkit.toml_document.TOMLDocument
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

            if len(list_) >= 3:
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

    def add_name(self, name, key_num=None):
        """
        Add the named StaticText and it companion the TextCtrl to the end
        Toml file. If `key_num` is provided the `key_num is the y coordinate
        and 0 will be the y continent.

        :param str name: The value name of the StaticText widget.
        :param int key_num: The key number to use.
        """
        assert self.__panel, "Current panel not set."

        if key_num is None:
            x, y = self._find_widget_gbs_pos(key_num=self._next_widget_num)
        else:
            x, y = (key_num, 0)

        key_num = self._next_widget_num
        key = self._make_key(key_num)
        self.__panel[key] = [
            'StaticText', 'w_fg_color_1',
            {'args': ['self', 'ID_ANY', name],
             'min': [-1, -1],
             'add': [0, 'ALIGN_BOTTOM | LEFT | RIGHT | TOP', 6],
             'pos': [x, y],
             'span': [1, 1]}]
        key = self._make_key(key_num+1)
        self.__panel[key] = [
            'TextCtrl', 'w_bg_color_1', 'w_fg_color_1',
            {'args': ['self', 'ID_ANY', ''], 'style': 'TE_RIGHT',
             'min': [-1, -1],
             'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP', 6],
             'pos': [x, y+1],
             'span': [1, 1]}]

    def remove_name(self, name):
        """
        Remove the named StaticText and it companion the TextCtrl from
        the Toml file.

        :param name: The value name of the StaticText widget.
        :type name: str
        """
        for key, item in self.__panel.items():
            list_ = find_dict(item).get('args', [])
            if name in list_: break

        self._remove_two_consecutive_keys(key)
        self._last_removed = (key, name)

    def undo_name(self, name):
        """
        Undo a removed field.

        :param name: The value name of the StaticText widget.
        :type name: str
        """
        ret = None

        if self._last_removed:
            old_key, name = self._last_removed
            self._create_hole(old_key+1)

            #self.add_name(name, row_count)
            self._last_removed = None
            new_key = self._make_key(self._next_widget_num())

        return ret

    def _remove_two_consecutive_keys(self, key):
        """
        Remove two consecutive keys using the first key as a starting
        point. This works because we are removing the StaticText widget
        by name then the TextCtrl that will be right after it.

        :param key: The Toml key.
        :type key: str
        """
        key_num = self._find_key_num(key)
        self.__panel.pop(key, None)
        second_key = self._make_key(key_num+1)
        self.__panel.pop(second_key, None)

    def _reorder(self, panel):
        """
        Re order the items in the Toml doc.

        :param panel: This is the Toml doc for the panel that is being
                      worked on.
        :type panel: Toml doc
        :return: A reordered Toml doc.
        :rtype: Toml doc
        """
        keys = sorted(list(panel))
        doc = tk.document()

        for idx, key in enumerate(keys):
            value = panel[key]
            doc[self._make_key(idx)] = value

        return doc

    def _create_hole(self, start):
        """
        Create a hole in the widget panel. All widgets after the hole
        will get its key bumped up by two.

        :param start: Where to start the reordering. Should be the widget
                      set that will be after the hole.
        :type start: int
        """
        doc = tk.document()

        for key, value in self.__panel.item():
            old_num = self._find_key_num(key)

            if old_num != start:
                doc[key] = value
            else:
                new_key = self._make_key(old_num+1)
                doc[new_key] = value

        self.__panel = doc

    @property
    def _next_widget_num(self):
        """
        Get the next widget key to be used when adding a new widget.

        :return: The next widget number.
        :rtype: int
        """
        last_key = list(self.__panel.keys())[-1]
        return self._find_key_num(last_key) + 1

    def _find_widget_gbs_pos(self, *, name=None, key_num=None):
        """
        Find the GridBagSizer position for either the name or the key number.

        :param name: The value name of the StaticText widget.
        :type name: str
        :param key_num: The number of the widget key.
        :type key_num: int
        """
        assert name or key_num is not None, (
            f"Either the name '{name}' or the key_num '{key_num}' must "
            "be set.")
        pos = ()

        if name:
            for value in self.__panel.value():
                dict_ = find_dict(value)

                if name in dict_['args']:
                    pos = dict_['pos']
                    break
                elif key_num is not None:
                    value = self.__panel.get(self._make_key(key_num), [])
                    assert value, "An invalid key_num was provided."
                    dict_ = find_dict(value)
                    pos = dict_['pos']
                    break

        return pos

    def _find_key_num(self, key):
        sre = self._KEY_NUM.search(key)
        assert sre is not None, f"There was an invalid key: {key}."
        return int(sre.group('count'))

    def _make_key(self, key_num):
        return f"widget_{key_num:>02}"
