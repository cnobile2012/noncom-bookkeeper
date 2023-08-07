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
    REGEX = re.compile(r"^&(?P<name>[\w ]+)\t(?P<sc>\w+\+\w)$")

    def __init__(self, parent, title="Short Cuts"):
        super().__init__(parent, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = ""

        for drop in parent.menu_items:
            name, sc, obj, inner = parent.menu_items[drop]
            text += f"\n{name.replace('&', '')}:\t{sc}\n"
            text += "-------------\n"

            for key in inner:
                if 'separator' in key: continue
                id, item, help, cb, flag = inner[key]

                if flag:
                    sre = self.REGEX.search(item)

                    if sre:
                        name = sre.group('name') + ':'
                        sc = sre.group('sc')
                        text += f"\t{name:<15}{sc}\t{help}\n"

            text.strip()

        short_cut_text = wx.StaticText(self, wx.TE_MULTILINE, text)
        short_cut_text.SetFont(wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL, 0, "Courier Prime"))
        sizer.Add(short_cut_text, 1, wx.ALL|wx.EXPAND|wx.LEFT|wx.RIGHT, 6)
        but_sizer = self.CreateSeparatedButtonSizer(wx.OK)
        sizer.Add(but_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM, 6)
        self.SetSizer(sizer)
        sizer.Fit(self)
