#!/usr/bin/env python

from src.main_frame import MainFrame
from src.ncb import CheckAppData

import wx


if __name__ == "__main__":
    import sys

    cad = CheckAppData()
    status = 0

    if not cad.has_valid_data:
        status = 1
        print(f"Invalid data, see log file, exit status {status}")
    else:
        # Try to run display.
        app = wx.App()
        mf = MainFrame()
        mf.Show(True)
        app.MainLoop()

    sys.exit(status)
