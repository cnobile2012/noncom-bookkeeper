# -*- coding: utf-8 -*-
#
# tests/conftest.py
#
__docformat__ = "restructuredtext en"

import os
from src.config import Settings
import time
import tracemalloc
tracemalloc.start()

start = time.perf_counter()


def pytest_sessionfinish(session, exitstatus):
    total = time.perf_counter() - start
    print(f"\n[PROFILE] Total test duration: {total:.2f} seconds.")


s = Settings()
s.testing = True
s.create_dirs()
_TMP_USER_CONFIG_FILE = s.user_config_fullpath
_TMP_USER_APP_CONFIG_FILE = s.user_app_config_fullpath
_TMP_LOCAL_CONFIG_FILE = os.path.join(s._testing_data_dir,
                                      'default_bahai.toml')
