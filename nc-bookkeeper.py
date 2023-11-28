#!/usr/bin/env python
#
# nc-bookkeeper.py
#

import os
import sys

from src.main_frame import MainFrame
from src.ncb import CheckPanelConfig, CheckAppConfig
from src.config import Settings

import wx


if __name__ == "__main__":
    cpc = CheckPanelConfig()
    cac = CheckAppConfig()
    status = 0

    if not cpc.has_valid_data:
        status = 1
        print(f"Invalid data, see log file, exit status {status}")

    if status == 0 and cac.has_valid_data:
        # Try to run display.
        app = wx.App()
        mf = MainFrame()
        icon_path = os.path.join(Settings.base_dir(), 'images',
                                 'bookkeeper-48x48.ico')
        mf.SetIcon(wx.Icon(icon_path))
        mf.Show(True)
        app.MainLoop()
    else:
        status = 2
        print(f"Programming error, see log file, exit status {status}")

    sys.exit(status)
