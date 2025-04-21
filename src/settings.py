# -*- coding: utf-8 -*-
#
# src/settings.py
#
__docformat__ = "restructuredtext en"

import wx

from .config import Settings


class Paths(wx.Panel):
    """
    Display all the paths used by the application.
    """
    sg = Settings()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.create_display()
        self.dirty = False

    def create_display(self):
        self.title = '''Application Paths'''
        self._bg_color = (178, 181, 185)
        w_bg_color = (222, 237, 230)
        w_fg_color = (50, 50, 204)
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        grid_sizer = wx.FlexGridSizer(4, 2, 0, 2)  # rows, cols, vgap, hgap
        sizer.Add(grid_sizer, 0, wx.CENTER, 0)

        widget_00 = wx.StaticText(self, wx.ID_ANY, "Data Path:")
        widget_00.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_00.SetMinSize([-1, -1])
        grid_sizer.Add(widget_00, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_01 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_data_fullpath,
                               style=wx.TE_READONLY)
        widget_01.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_01.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_01.SetMinSize([400, -1])
        grid_sizer.Add(widget_01, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_02 = wx.StaticText(self, wx.ID_ANY, "Panel Path:")
        widget_02.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_02.SetMinSize([-1, -1])
        grid_sizer.Add(widget_02, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_03 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_config_fullpath,
                               style=wx.TE_READONLY)
        widget_03.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_03.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_03.SetMinSize([400, -1])
        grid_sizer.Add(widget_03, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_04 = wx.StaticText(self, wx.ID_ANY, "Config Path:")
        widget_04.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_04.SetMinSize([-1, -1])
        grid_sizer.Add(widget_04, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_05 = wx.TextCtrl(self, wx.ID_ANY,
                               self.sg.user_app_config_fullpath,
                               style=wx.TE_READONLY)
        widget_05.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_05.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_05.SetMinSize([400, -1])
        grid_sizer.Add(widget_05, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_06 = wx.StaticText(self, wx.ID_ANY, "Log Path:")
        widget_06.SetForegroundColour(wx.Colour(50, 50, 204))
        widget_06.SetMinSize([-1, -1])
        grid_sizer.Add(widget_06, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_07 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_log_fullpath,
                               style=wx.TE_READONLY)
        widget_07.SetBackgroundColour(wx.Colour(*w_bg_color))
        widget_07.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_07.SetMinSize([400, -1])
        grid_sizer.Add(widget_07, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

    @property
    def background_color(self):
        return self._bg_color
