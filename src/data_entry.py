# -*- coding: utf-8 -*-
#
# src/data_entry.py
#
__docformat__ = "restructuredtext en"

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .bases import BasePanel
from .custom_widgits import BadiDatePickerCtrl, EVT_BADI_DATE_CHANGED


class LedgerDataEntry(BasePanel, ScrolledPanel):
    """
    Implements data entry into the ledger.
    """

    def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
        super().__init__(parent, id=id, *args, **kwargs)
        self.frame = parent.GetParent()
        self.create_display()
        self.dirty = False

    def create_display(self):
        self.title = "Ledger Data Entry"
        self._bg_color = (200, 255, 170)
        w_fg_color = (50, 50, 204)
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
        self.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_NORMAL, 0, ''))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        widget_00 = wx.StaticText(self, wx.ID_ANY, self.title)
        widget_00.SetFont(title_font)
        widget_00.SetForegroundColour(wx.Colour(*w_fg_color))
        sizer.Add(widget_00, 0, wx.CENTER, 0)

        grid_sizer = wx.FlexGridSizer(1, 2, 0, 2)  # rows, cols, vgap, hgap
        sizer.Add(grid_sizer, 0, wx.CENTER, 0)

        widget_01 = wx.StaticText(self, wx.ID_ANY, "Date")
        widget_01.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_01.SetMinSize([-1, -1])
        grid_sizer.Add(widget_01, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_02 = BadiDatePickerCtrl(self, wx.ID_ANY)
        widget_02.SetBackgroundColour(wx.Colour(*self._bg_color))
        widget_02.SetForegroundColour(wx.Colour(*w_fg_color))
        widget_02.SetMinSize([130, 30])
        widget_02.SetFocus()
        #widget_02.Bind(EVT_BADI_DATE_CHANGED, self.set_dirty_flag)
        grid_sizer.Add(widget_02, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        self.SetupScrolling(rate_x=20, rate_y=40)
        self.Hide()

    @property
    def background_color(self):
        """
        This is for the ShortCuts panel.
        """
        return self._bg_color
