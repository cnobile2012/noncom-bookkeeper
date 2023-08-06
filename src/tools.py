# -*- coding: utf-8 -*-
#
# src/tools.py
#
__docformat__ = "restructuredtext en"

import re

import wx


class ShortCuts(wx.Dialog):
    """
    This dialog displayes the list of short cuts used in the menu bar.
    """
    REGEX = re.compile(r"^&(?P<name>\w+)\t(?P<sc>\w+\+\w)$")

    def __init__(self, parent, title="Short Cuts"):
        super().__init__(parent, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = ""

        for item, item_help in parent.menu_items.items():
            print(f"POOP: {item}--{item_help}")
            sre = self.REGEX.search(item)
            print(sre)

            if sre:
                name = sre.group('name')
                sc = sre.group('sc').replace('+', ' ')
                text += f"{name}:\t{sc}\t{item_help}\n"

        short_cut_text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        short_cut_text.WriteText(text)
        sizer.Add(short_cut_text, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer)
        self.Show()
