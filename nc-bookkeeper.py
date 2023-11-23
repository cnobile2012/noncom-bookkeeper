#!/usr/bin/env python
#
# nc-bookkeeper.py
#

import os

from src.main_frame import MainFrame
from src.ncb import CheckPanelConfig, CheckAppConfig
from src.config import Settings

import wx


if __name__ == "__main__":
    import sys

    cpd = CheckPanelConfig()
    cad = CheckAppConfig()
    status = 0

    if not cpd.has_valid_data:
        status = 1
        print(f"Invalid data, see log file, exit status {status}")

    cad.has_valid_data

    if status == 0:
        # Try to run display.
        app = wx.App()
        mf = MainFrame()
        icon_path = os.path.join(Settings.base_dir(), 'images',
                                 'bookkeeper-48x48.ico')
        mf.SetIcon(wx.Icon(icon_path))
        mf.Show(True)
        app.MainLoop()

    sys.exit(status)
