# -*- coding: utf-8 -*-
#
# src/settings.py
#
__docformat__ = "restructuredtext en"

import logging
from pprint import pprint

import wx

from .config import Settings, TomlMetaData


class Paths(wx.Panel):
    """
    Display all the paths used by the application.
    """
    sg = Settings()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title = '''Application Paths'''
        self._bg_color = [178, 181, 185]
        w_bg_color = [222, 237, 230]
        w_fg_color = [50, 50, 204]
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        grid_sizer = wx.FlexGridSizer(4, 2, 0, 2) # rows, cols, vgap, hgap
        sizer.Add(grid_sizer, 0, wx.CENTER, 0)

        widget_0 = wx.StaticText(self, wx.ID_ANY, "Data Path:")
        widget_0.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_0.SetMinSize([-1, -1])
        grid_sizer.Add(widget_0, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_1 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_data_fullpath,
                               style=wx.TE_READONLY)
        widget_1.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_1.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_1.SetMinSize([400, -1])
        grid_sizer.Add(widget_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_2 = wx.StaticText(self, wx.ID_ANY, "Panel Path:")
        widget_2.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_2.SetMinSize([-1, -1])
        grid_sizer.Add(widget_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_3 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_config_fullpath,
                               style=wx.TE_READONLY)
        widget_3.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_3.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_3.SetMinSize([400, -1])
        grid_sizer.Add(widget_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_4 = wx.StaticText(self, wx.ID_ANY, "Config Path:")
        widget_4.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_4.SetMinSize([-1, -1])
        grid_sizer.Add(widget_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_5 = wx.TextCtrl(self, wx.ID_ANY,
                               self.sg.user_app_config_fullpath,
                               style=wx.TE_READONLY)
        widget_5.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_5.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_5.SetMinSize([400, -1])
        grid_sizer.Add(widget_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_6 = wx.StaticText(self, wx.ID_ANY, "Log Path:")
        widget_6.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_6.SetMinSize([-1, -1])
        grid_sizer.Add(widget_6, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_7 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_log_fullpath,
                               style=wx.TE_READONLY)
        widget_7.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_7.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_7.SetMinSize([400, -1])
        grid_sizer.Add(widget_7, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

    @property
    def background_color(self):
        return self._bg_color


class FieldEdit(wx.Panel):
    """
    Add or remove fields in various panels.
    """
    tmd = TomlMetaData()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.title = '''Add/Remove Fields'''
        self._bg_color = [178, 181, 185]
        w_bg_color = [222, 237, 230]
        w_fg_color = [50, 50, 204]
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        grid_sizer = wx.FlexGridSizer(4, 2, 0, 2) # rows, cols, vgap, hgap
        sizer.Add(grid_sizer, 0, wx.CENTER, 0)

        #pprint(self._edit_names)
        #pprint(self.tmd.panels)




    @property
    def _edit_names(self):
        item_list = self.parent.menu_items.get('edit', [])
        item_names = []

        if item_list: # Just incase the list is empty.

            for item in item_list[-1].values():
                if item: # Just incase we find a separator.
                    name, tab, key = item[1].partition('\t')
                    if "Close All" in name: continue
                    item_names.append(name.lstrip('&'))

        return item_names

    @property
    def background_color(self):
        return self._bg_color
