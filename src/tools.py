# -*- coding: utf-8 -*-
#
# src/tools.py
#
__docformat__ = "restructuredtext en"

import re

import wx


class ShortCuts(wx.Frame):
    """
    This dialog displayes the list of short cuts used in the menu bar.
    """
    REGEX = re.compile(r"^&(?P<name>[\w ]+)\t(?P<sc>\w+\+\w)$")

    def __init__(self, parent, title="Short Cuts"):
        super().__init__(parent, title=title)
        old_style = self.GetWindowStyle()
        self.SetWindowStyle(old_style | wx.STAY_ON_TOP)
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = self.create_list(parent)
        short_cut_text = wx.StaticText(self, wx.TE_MULTILINE, text)
        short_cut_text.SetFont(wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL, 0, "Courier Prime"))
        sizer.Add(short_cut_text, 1, wx.ALL|wx.EXPAND|wx.LEFT|wx.RIGHT, 6)
        dismiss = wx.Button(self, id=wx.ID_OK, label="&Dismiss")
        dismiss.Bind(wx.EVT_BUTTON, self.close_frame)
        sizer.Add(dismiss, 0, wx.ALL|wx.ALIGN_CENTER,5)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.CenterOnParent(dir=wx.BOTH)
        self.Show()

    def close_frame(self, event):
        self.Destroy()

    def create_list(self, parent):
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

        return text.strip()
