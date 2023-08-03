# -*- coding: utf-8 -*-
#
# Noncommercial Bookkeeping System
#
__docformat__ = "restructuredtext en"

import os
import logging
import shutil

from . import Logger
from .config import Settings, TomlConfig


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


class CheckAppData(Settings):
    """
    Check that all the .config, .cache/../log directories are created
    and have valid files in them where necessary.
    """

    ## print(
    ##     f"appname: {dirs.appname}\nappauthor: {dirs.appauthor}\n"
    ##     f"user_data_dir: {dirs.user_data_dir}\n"
    ##     f"user_config_dir: {dirs.user_config_dir}\n"
    ##     f"user_cache_dir: {dirs.user_cache_dir}\n"
    ##     f"user_log_dir: {dirs.user_log_dir}\n"
    ##     #f"dir: {dir(dirs)}\n"
    ##     )

    def __init__(self, *args, level=logging.WARNING, **kwargs):
        super().__init__()
        self._log = logging.getLogger(self.logger_name)

    @property
    def has_valid_data(self):
        """
        Does the static data exist and is the data valid?
        """
        uc_type = self.check_config_files()
        ud_type = self.check_data_files()
        return ud_type and uc_type

    def check_config_files(self):
        """
        Config files will be TOML files.
        """
        fname = self.user_config_fullpath

        if not os.path.exists(fname):
            shutil.copy2(self.local_config_fullpath, fname)

        tc = TomlConfig()
        return tc.is_valid

    def check_data_files(self):
        """
        Data will be database files.
        """

        return True # For now until I've written the DB code.
