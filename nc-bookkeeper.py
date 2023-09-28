#!/usr/bin/env python
#
# nc-bookkeeper.py
#

from src.main_frame import MainFrame
from src.ncb import CheckPanelConfig, CheckAppConfig

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
        mf.Show(True)
        app.MainLoop()

    sys.exit(status)
