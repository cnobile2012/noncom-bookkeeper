#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test confirmation dialog.
#
__docformat__ = "restructuredtext en"

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

import wx

from src.utilities import ConfirmationDialog


class _TestFrame(wx.Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        msg = "Test message."
        cap = "Removal Confirmation"

        dlg = ConfirmationDialog(self, msg, cap)
        print(dlg.show())
        wx.Exit()


if __name__ == "__main__":
    app = wx.App()
    frame = _TestFrame(None, title="Test confirmation dialog..")
    app.MainLoop()
