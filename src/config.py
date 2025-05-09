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


class Settings(AppDirs):
    """
    This class has all the default app, file, and log names used bye the
    system.
    """
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
        super().__init__(*args, appname=self.app_name,
                         appauthor=self.primary_developer, **kwargs)
        # The two lines below read an environment variable which is used
        # during the app build process. The default is to use the Baha'i
        # configuration.
        self.__config_type = os.environ.get('NCB_TYPE', 'bahai')
        self.__user_toml = self._CONFIG_FILES['user'][self.__config_type]
        self.__local_toml = self._CONFIG_FILES['local'][self.__config_type]
        self.__app_toml = 'nc-bookkeeper.toml'
        self._log = logging.getLogger(self.logger_name)

    def create_dirs(self):  # pragma: no cover
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
        return os.path.join(self.user_data_dir, self.data_file_name)

    @property
    def user_config_fullpath(self):
        return os.path.join(self.user_config_dir, self.__user_toml)

    @property
    def user_app_config_fullpath(self):
        return os.path.join(self.user_config_dir, self.__app_toml)

    @property
    def user_log_fullpath(self):
        return os.path.join(self.user_log_dir, self.logfile_name)

    @property
    def cached_factory_dir(self):
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

    INVALID_PROP = 1      # Invalid property
    CANNOT_FIND_FILE = 2  # Cannot find file
    TOML_ERROR = 3        # TOML error
    ZERO_LENGTH_FILE = 4  # Zero length file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def panel_config(self):
        return self.SYS_FILES.get('panel_config')

    @panel_config.setter
    def panel_config(self, value):
        self.SYS_FILES['panel_config'] = value

    # def panel_field_names(self, panel, raw=False):
    #     """
    #     Get the field names for a specific panel.
    #     """
    #     widget_names = []

    #     for widget in self.panel_config[panel]['widgets'].values():
    #         w_type = widget[0]

    #         if w_type in ('RadioBox', 'StaticText'):
    #             args = find_dict(widget).get('args', [])
    #             name = args[2] if args else ''
    #             if not name: continue

    #             if not raw:
    #                 name = name.replace(' ', '_').replace(':', '').lower()

    #             widget_names.append(name)

    #     return widget_names

    @property
    def app_config(self):
        return self.SYS_FILES.get('app_config')

    @app_config.setter
    def app_config(self, value):
        self.SYS_FILES['app_config'] = value

    def parse_toml(self, file_list):
        """
        Parse the toml file.

        :param file_list: A tuple of files to parse.
        :type file_list: str
        :return: A list of errors if any exist. [fullpath, errmsg, errcode]
        :rtype: list
        """
        raw_doc = None
        errors = []

        for file_type in file_list:
            try:
                fname = getattr(self, file_type)
            except AttributeError as e:
                msg = f"Invalid property, {str(e)}"
                self._log.error(msg)
                errors.append((file_type, msg, self.INVALID_PROP))
            else:
                try:
                    with open(fname, 'r') as f:
                        raw_doc = f.read()
                except FileNotFoundError as e:
                    msg = f"Cannot find file {fname}, {str(e)}"
                    self._log.error(msg)
                    errors.append((file_type, msg, self.CANNOT_FIND_FILE))
                else:
                    if raw_doc != "":
                        try:
                            doc = tk.parse(raw_doc)
                        except tk.exceptions.TOMLKitError as e:
                            msg = f"TOML error: {str(e)}"
                            self._log.error(msg)
                            errors.append((file_type, msg, self.TOML_ERROR))
                        else:
                            if 'user_config' in file_type:
                                self.panel_config = doc
                            elif (self.panel_config is None
                                  and 'local_config' in file_type):
                                # Executed only on first run.
                                self.panel_config = doc
                            elif (self.app_config is None
                                  and 'user_app_config' in file_type):
                                self.app_config = doc
                    else:
                        msg = f"Cannot parse zero length file '{fname}'."
                        self._log.error(msg)
                        errors.append((file_type, msg, self.ZERO_LENGTH_FILE))

        return errors


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
        return getattr(self, font_type)


class TomlPanelConfig(BaseSystemData):
    """
    Read and write the TOML panel config file.
    """
    _shared_state = {}
    _FILE_LIST = ('user_config_fullpath', 'local_config_fullpath')

    def __init__(self, *args, **kwargs):
        self.__dict__ = self._shared_state
        super().__init__(*args, **kwargs)

    @property
    def is_valid(self):
        """
        Test the panel config file that it can be parsed and that it exists.
        This property can return True or False.
        """
        ret = True
        # The order of the tuple below is important.
        errors = self.parse_toml(self._FILE_LIST)

        for error in errors:
            if error[2] == self.INVALID_PROP:
                msg = f"Error: {error[1]}"
                self._log.critical(msg)
                ret = False
            elif error[0] == 'user_config_fullpath':
                # Backup bad file then over write the original with
                # the default.
                ufname = self.user_config_fullpath
                lfname = self.local_config_fullpath
                msg = "A critical error was encounted '{}' does not exist."

                if not os.path.exists(ufname):
                    msg = msg.format(ufname)
                    self._log.warning(msg)

                if not os.path.exists(lfname):
                    msg = msg.format(lfname)
                    self._log.critical(msg)
                    ret = False

                if ret:
                    if error[2] == self.CANNOT_FIND_FILE:
                        shutil.copy2(lfname, ufname)
                        self.parse_toml((ufname,))
                        msg = f"Warning {error[1]}"
                        self._log.warning(msg)
                    elif error[2] in (self.TOML_ERROR, self.ZERO_LENGTH_FILE):
                        bad_file = f'{ufname}.bad'
                        shutil.copy2(ufname, bad_file)
                        shutil.copy2(lfname, ufname)
                        msg = ("Found an invalid panel config file and "
                               "reverted to the default version. The original "
                               f"bad file has been backed up to {bad_file}, "
                               f"{error[1]}")
                        self._log.warning(msg)
            elif error[0] == 'local_config_fullpath':
                msg = f"Error: {error[2]}"
                self._log.critical(msg)
                ret = False

        return ret


class TomlAppConfig(BaseSystemData):
    """
    Read and write the TOML app config file.
    """
    _shared_state = {}
    _FILE_LIST = ('user_app_config_fullpath',)

    def __init__(self, *args, **kwargs):
        self.__dict__ = self._shared_state
        super().__init__(*args, **kwargs)

    @property
    def is_valid(self):
        """
        Test the app config file that it can be parsed and that it exists.
        This property always returns True.
        """
        ret = True
        run_num = 2

        while run_num:
            errors = self.parse_toml(self._FILE_LIST)
            run_num = run_num - 1 if errors else 0

            for error in errors:
                if error[2] == self.INVALID_PROP:
                    msg = f"Error: {error[1]}"
                    self._log.critical(msg)
                    ret = False
                elif error[0] == 'user_app_config_fullpath':
                    fname = self.user_app_config_fullpath

                    if error[2] in (self.TOML_ERROR, self.ZERO_LENGTH_FILE):
                        # Backup bad file then recreate the file.
                        bad_file = f'{fname}.bad'
                        shutil.move(fname, bad_file)
                        msg = ("Found an invalid app config file, a new one "
                               "will be created. The original bad file has "
                               f"been backed up to {bad_file}.")
                        self._log.warning(msg)
                        #self.parent.statusbar_warning = msg
                        # *** TODO *** This needs to be shown on the screen
                        #              if detected.
                    else:  # CANNOT_FIND_FILE
                        msg = (f"The file {getattr(self, error[0])} could "
                               "not be found. It will be created.")
                        self._log.warning(msg)
                        #self.parent.statusbar_warning = msg
                        # *** TODO *** This needs to be shown on the screen
                        #              if detected.

                    self.create_app_config()

        return ret

    def create_app_config(self):
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
        #self.parent.statusbar_warning = msg
        # *** TODO *** This needs to be shown on the screen if detected.
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
            #self.parent.statusbar_warning = msg
            # *** TODO *** This needs to be shown on the screen if detected.
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
    def field_names(self) -> list:
        """
        A list of field names not including title names.
        """
        assert self.__panel, (
            "There is no panel that is currently being worked on.")
        names = []

        for item in self.__panel.values():
            #print(item)
            list_ = find_dict(item).get('args', [])

            if len(list_) >= 3:
                names.append(list_[2])

        return [name for name in names if name and name.endswith(':')]

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

    # def undo_name(self, name):
    #     """
    #     Undo a removed field.

    #     :param name: The value name of the StaticText widget.
    #     :type name: str
    #     """
    #     ret = None

    #     if self._last_removed:
    #         old_key, name = self._last_removed
    #         self._create_hole(old_key+1)

    #         self.add_name(name, row_count)
    #         self._last_removed = None
    #         new_key = self._make_key(self._next_widget_num())

    #     return ret

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
        #print(key_num)

        if name:
            for value in self.__panel.value():
                dict_ = find_dict(value)

                if name in dict_['args']:
                    pos = dict_['pos']
                    break
                elif key_num is not None:
                    value = self.__panel.get(self._make_key(key_num), [])
                    #print(key_num, value)
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
