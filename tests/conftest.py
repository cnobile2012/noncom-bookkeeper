# -*- coding: utf-8 -*-
#
# tests/conftest.py
#

import os
import pytest
from src.config import Settings

s = Settings()
s.testing = True
s.create_dirs()
_TMP_USER_CONFIG_FILE = s.user_config_fullpath
_TMP_USER_APP_CONFIG_FILE = s.user_app_config_fullpath
_TMP_LOCAL_CONFIG_FILE = os.path.join(s._testing_data_dir,
                                      'default_bahai.toml')
