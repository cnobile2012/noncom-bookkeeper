# -*- coding: utf-8 -*-
#
# Noncommercial Bookkeeping System
#
__docformat__ = "restructuredtext en"

import os
import logging
import shutil

from . import Logger
from .config import TomlPanelConfig, TomlAppConfig


# appname: NC-Bookkeeper
# appauthor: Carl J. Nobile
# user_data_dir: /home/cnobile/.local/share/NC-Bookkeeper
# user_config_dir: /home/cnobile/.config/NC-Bookkeeper
# user_cache_dir: /home/cnobile/.cache/NC-Bookkeeper
# user_log_dir: /home/cnobile/.cache/NC-Bookkeeper/log

# 1 -- Has app been run before?
# 1.1 -- If no, create data, config, cache, and logging directories.
# 1.1.1 -- Open Config Page.
# 1.2 -- Has Budget Information been entered?
# 1.2.1 -- If no, open Budget Information page.
# 1.2.2 -- If yes, open General Ledger.


class CheckPanelConfig(TomlPanelConfig):
    """
    Check that the panel config file has valid data. Copy the default
    config to the user directory id necessary.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def has_valid_data(self):
        """
        Does the static data exist and is the data valid?
        """
        return self.check_config_files()

    def check_config_files(self):
        """
        Config files will be TOML files.
        """
        fname = self.user_config_fullpath

        if not os.path.exists(fname):
            shutil.copy2(self.local_config_fullpath, fname)

        return self.is_valid


class CheckAppConfig(TomlAppConfig):
    """
    Check that the app config file has valid data. Create a new one
    if necessary.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def has_valid_data(self):
        """
        Does the static data exist and is the data valid?
        """
        return self.is_valid
