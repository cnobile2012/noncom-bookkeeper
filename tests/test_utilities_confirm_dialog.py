#!/usr/bin/env python
#
# Test confirmation dialog.
#

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import wx

from src.utilities import ConfirmationDialog


class _TestFrame(wx.Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        w_fg_color_0 = (50, 50, 204)
        msg = "Test message."
        cap = "Removal Confirmation"

        dlg = ConfirmationDialog(self, msg, cap, (220, 130, 143), # Red-ish
                                 w_fg_color_0)
        print(dlg.show())
        wx.Exit()


if __name__ == "__main__":
    app = wx.App()
    frame = _TestFrame(None, title="Test confirmation dialog..")
    app.MainLoop()
