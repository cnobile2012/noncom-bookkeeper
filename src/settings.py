# -*- coding: utf-8 -*-
#
# src/settings.py
#
__docformat__ = "restructuredtext en"

import wx

from .config import Settings
from .custom_widgits import ColorCheckBox, EVT_COLOR_CHECKBOX


class FiscalSettings(wx.Panel):
    """
    Display all the settings for the Fiscal Year Panel.
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.frame = parent.GetParent()
        self.create_display()
        self.dirty = False

    def create_display(self):
        self.title = "Fiscal Year Settings"
        self._bg_color = (210, 190, 255)
        w_fg_color = wx.Colour(50, 50, 204)    # Dark Blue
        w_bg_color = wx.Colour(255, 253, 208)  # Cream
        col_1_wrap = 310
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        widget_00 = wx.StaticText(self, wx.ID_ANY, self.title)
        widget_00.SetFont(title_font)
        widget_00.SetForegroundColour(w_fg_color)
        sizer.Add(widget_00, 0, wx.CENTER | wx.ALL, 6)

        grid_sizer = wx.FlexGridSizer(1, 2, 0, 2)  # rows, cols, vgap, hgap
        sizer.Add(grid_sizer, 0, wx.CENTER | wx.ALL, 10)

        w1_label = ('Enables the "Current Fiscal Year" checkbox on the '
                    '"Fiscal Year" page and should only be enabled for '
                    'for the current year.')
        widget_01 = wx.StaticText(self, wx.ID_ANY, w1_label)
        widget_01.Wrap(col_1_wrap)
        widget_01.SetForegroundColour(w_fg_color)
        widget_01.SetMinSize((-1, -1))
        grid_sizer.Add(widget_01, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_02 = ColorCheckBox(self, wx.ID_ANY, bb_color=w_fg_color,
                                  cb_color=w_bg_color, name='current_state')
        widget_02.SetSize((16, 16))
        widget_02.SetForegroundColour(w_fg_color)
        widget_02.Bind(EVT_COLOR_CHECKBOX, self.enable_current)
        grid_sizer.Add(widget_02, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        #grid_sizer.Add((0, 0), 1, wx.EXPAND, 6)
        self.Hide()

    def enable_current(self, event):
        fiscal_panel = self.frame.panels.get('fiscal')
        current_widget = fiscal_panel.FindWindowByName('current')
        state = current_widget.IsEnabled()
        current_widget.Enable(False if state else True)

    @property
    def background_color(self):
        """
        This is for the ShortCuts panel.
        """
        return self._bg_color


class Paths(wx.Panel):
    """
    Display all the paths used by the application.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.dirty = False
        self.sg = Settings()
        self.create_display()

    def create_display(self):
        self.title = "Application Paths"
        self._bg_color = wx.Colour(178, 181, 185)
        w_bg_color = wx.Colour(222, 237, 230)
        w_fg_color = wx.Colour(50, 50, 204)
        self.SetBackgroundColour(self._bg_color)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        widget_00 = wx.StaticText(self, wx.ID_ANY, self.title)
        widget_00.SetFont(title_font)
        widget_00.SetForegroundColour(w_fg_color)
        sizer.Add(widget_00, 0, wx.CENTER, 0)

        grid_sizer = wx.FlexGridSizer(4, 2, 0, 2)  # rows, cols, vgap, hgap
        sizer.Add(grid_sizer, 0, wx.CENTER | wx.ALL, 10)

        widget_01 = wx.StaticText(self, wx.ID_ANY, "Data Path:")
        widget_01.SetForegroundColour(w_fg_color)
        widget_01.SetMinSize((-1, -1))
        grid_sizer.Add(widget_01, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_02 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_data_fullpath,
                                style=wx.TE_READONLY)
        widget_02.SetBackgroundColour(w_bg_color)
        widget_02.SetForegroundColour(w_fg_color)
        widget_02.SetMinSize((440, -1))
        grid_sizer.Add(widget_02, 0, wx.EXPAND | wx.ALL, 6)

        widget_03 = wx.StaticText(self, wx.ID_ANY, "Panel Path:")
        widget_03.SetForegroundColour(w_fg_color)
        widget_03.SetMinSize((-1, -1))
        grid_sizer.Add(widget_03, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_04 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_config_fullpath,
                                style=wx.TE_READONLY)
        widget_04.SetBackgroundColour(w_bg_color)
        widget_04.SetForegroundColour(w_fg_color)
        widget_04.SetMinSize((440, -1))
        grid_sizer.Add(widget_04, 0, wx.EXPAND | wx.ALL, 6)

        widget_05 = wx.StaticText(self, wx.ID_ANY, "Config Path:")
        widget_05.SetForegroundColour(w_fg_color)
        widget_05.SetMinSize((-1, -1))
        grid_sizer.Add(widget_05, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_06 = wx.TextCtrl(self, wx.ID_ANY,
                                self.sg.user_app_config_fullpath,
                                style=wx.TE_READONLY)
        widget_06.SetBackgroundColour(w_bg_color)
        widget_06.SetForegroundColour(w_fg_color)
        widget_06.SetMinSize((440, -1))
        grid_sizer.Add(widget_06, 0, wx.EXPAND | wx.ALL, 6)

        widget_07 = wx.StaticText(self, wx.ID_ANY, "Log Path:")
        widget_07.SetForegroundColour(w_fg_color)
        widget_07.SetMinSize((-1, -1))
        grid_sizer.Add(widget_07, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_08 = wx.TextCtrl(self, wx.ID_ANY, self.sg.user_log_fullpath,
                                style=wx.TE_READONLY)
        widget_08.SetBackgroundColour(w_bg_color)
        widget_08.SetForegroundColour(w_fg_color)
        widget_08.SetMinSize((440, -1))
        grid_sizer.Add(widget_08, 0, wx.EXPAND | wx.ALL, 6)
        self.Hide()

    @property
    def background_color(self):
        """
        This is for the ShortCuts panel.
        """
        return self._bg_color
