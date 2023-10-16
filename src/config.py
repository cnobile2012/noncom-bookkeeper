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

from .bases import find_dict
from .exceptions import InvalidTomlException

import tomlkit as tk


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

    def __init__(self, *args, **kwargs):
        super().__init__(appname=self.app_name,
                         appauthor=self.primary_developer)
        # The two lines below read an environment variable which is used
        # during the app build process. The default is to use the Baha'i
        # configuration.
        value = os.environ.get('NCB_TYPE', 'bahai')
        self.__user_toml = self._CONFIG_FILES['user'][value]
        self.__local_toml = self._CONFIG_FILES['local'][value]
        self.__app_toml = 'nc-bookkeeper.toml'

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
    def user_app_config_fullpath(self):
        return os.path.join(self.user_config_dir, self.__app_toml)

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
    SYS_FILES = {'data': None, 'panel_config': None, 'app_config': None}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger(self.logger_name)

    ## @property
    ## def data(self):
    ##     return self.SYS_FILES.get('data')

    ## @data.setter
    ## def data(self, value):
    ##     self.SYS_FILES['data'] = value

    @property
    def panel_config(self):
        return self.SYS_FILES.get('panel_config')

    @panel_config.setter
    def panel_config(self, value):
        self.SYS_FILES['panel_config'] = value

    @property
    def app_config(self):
        return self.SYS_FILES.get('app_config')

    @app_config.setter
    def app_config(self, value):
        self.SYS_FILES['app_config'] = value

    def parse_toml(self, file_list):
        raw_doc = None
        errors = []

        for file_type in file_list:
            fname = getattr(self, file_type)

            try:
                with open(fname, 'r') as f:
                    raw_doc = f.read()
            except FileNotFoundError as e:
                errors.append(file_type)
                self._log.error("Error: cannot find file '%s'.", fname)
            else:
                try:
                    doc = tk.parse(raw_doc)
                except tk.exceptions.TOMLKitError as e:
                    self._log.error("TOML error: %s", str(e))
                    errors.append(file_type)
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
        file_list = ('user_config_fullpath',
                      'local_config_fullpath')
        errors = self.parse_toml(file_list)

        for error in errors:
            if error == 'user_config_fullpath':
                # Backup bad file then over write the original with the default.
                fname = self.user_config_fullpath
                bad_file = f'{fname}.bad'
                shutil.copy2(fname, bad_file)
                shutil.copy2(self.local_config_fullpath, fname)
                msg = ("Found an invalid panel config file and reverted "
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


class TomlAppConfig(BaseSystemData):
    """
    Read and write the TOML app config file.
    """
    _shared_state = {}

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
        file_list = ('user_app_config_fullpath',)
        errors = self.parse_toml(file_list)

        for error in errors:
            if error == 'user_app_config_fullpath':
                fname = self.user_app_config_fullpath

                if os.path.exists(fname):
                    # Backup bad file then recreate the file.
                    bad_file = f'{fname}.bad'
                    shutil.move(fname, bad_file)
                    msg = ("Found an invalid app config file, a new one "
                       "will be created. The original bad file has "
                       f"been backed up to {bad_file}.")
                    self._log.warning(msg)
                    # *** TODO *** This needs to be shown on the screen
                    #              if detected.
                else:
                    msg = (f"The file {getattr(self, error)} could not be "
                           f"found. It will be created.")
                    self._log.warning(msg)
                    # *** TODO *** This needs to be shown on the screen
                    #              if detected.

                self.create_app_config()
                self.parse_toml(file_list)

        return ret

    def create_app_config(self):
        doc = tk.document()
        # Create header
        doc.add(tk.comment(""))
        doc.add(
            tk.comment("Noncommercial Bookkeeper application config file."))
        doc.add(tk.comment(""))
        doc.add(tk.comment(f"Date Created: {datetime.now()}"))
        doc.add(tk.comment(""))
        doc.add(tk.nl())
        # Create app size
        app_size = tk.table()
        app_size.add('default', [530, 830])
        app_size.add('size', [530, 830])
        doc.add('app_size', app_size)
        self._write_file(tk.dumps(doc))

    def get_value(self, table, key):
        doc = self.app_config
        item_table = doc.get(table)

        if item_table:
            item_key = item_table.get(key)

            if item_key:
                return doc[table][key]

        self._log.error("Could not find the table '%s' or key: %s in %s.",
                        table, key, self.user_app_config_fullpath)

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
        except Exception as e:
            msg = (f"Could not create the {self.user_app_config_fullpath} "
                   f"file, {str(s)}")
            self._log.critical(msg)
            # *** TODO *** This needs to be shown on the screen if detected.


class TomlCreatePanel(BaseSystemData):
    """
    Create an updated panel Toml file.
    """
    _KEY_NUM = re.compile(r"^.*_(?P<count>\d+)$")
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

        :param current: The current panel's Toml doc.
        :type current: Toml doc
        """
        self.__panel = current.copy()

    @property
    def field_names(self):
        """
        A list of field names not including title names.
        """
        assert self.__panel, "Current panel not set."
        names = []

        for item in self.__panel.values():
            list_ = find_dict(item).get('args', [])

            if len(list_) >= 3:
                names.append(list_[2])

        return [name for name in names if name and name.endswith(':')]

    def add_name(self, name, row_count):
        """
        Add the named StaticText and it companion the TextCtrl to the
        Toml file.

        :param name: The value name of the StaticText widget.
        :type name: str
        :param row_count: The current number of rows in the GridBagSizer.
        :type row_count: int
        """
        assert self.__panel, "Current panel not set."
        key_num = self._next_widget_num
        key = self._make_key(key_num)
        self.__panel[key] = [
            'StaticText', 'w_fg_color_1',
            {'args': ['self', 'ID_ANY', name],
             'min': [-1, -1],
             'add': [0, 'ALIGN_BOTTOM | LEFT | RIGHT | TOP', 6],
             'pos': [row_count, 0],
             'span': [1, 1]}]
        key = self._make_key(key_num+1)
        self.__panel[key] = [
            'TextCtrl', 'w_bg_color_1', 'w_fg_color_1',
            {'args': ['self', 'ID_ANY', ''], 'style': 'TE_RIGHT',
             'min': [-1, -1],
             'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP', 6],
             'pos': [row_count, 1],
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
        #self.__panel = self._reorder(self.__panel)

    def _remove_two_consecutive_keys(self, key):
        """
        Remove two consecutive keys using the first key as a starting
        point. This works because we are removing the StaticText widgit
        by name then the TextCtrl that will be right agter it.

        :param key: The Toml key.
        :type key: str
        """
        sre = self._KEY_NUM.search(key)
        assert sre is not None, f"There was an invalid key: {key}."
        key_num = int(sre.group('count'))
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

    @property
    def _next_widget_num(self):
        """
        Get the next widget key to be used when adding a new widget.

        :return: The next widget number.
        :rtype: int
        """
        last_key = list(self.__panel.keys())[-1]
        sre = self._KEY_NUM.search(last_key)
        assert sre is not None, f"There was an invalid key: {last_key}."
        return int(sre.group('count')) + 1

    def _make_key(self, key_num):
        return f"widget_{key_num:>02}"


class Database(BaseSystemData):
    pass
