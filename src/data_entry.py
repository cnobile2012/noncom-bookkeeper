# -*- coding: utf-8 -*-
#
# src/data_entry.py
#
__docformat__ = "restructuredtext en"

import re
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .config import TomlMetaData, TomlCreatePanel
from .utilities import MutuallyExclusiveWidgets, make_name
from .bases import BasePanel
from .custom_widgits import (
    BadiDatePickerCtrl, EVT_BADI_DATE_CHANGED, FlatArrowButton, EVT_FLAT_ARROW)


class LedgerDataEntry(ScrolledPanel, BasePanel, MutuallyExclusiveWidgets):
    """
    Implements data entry into the ledger.
    """
    _tmd = TomlMetaData()
    _tcp = TomlCreatePanel()

    def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
        super().__init__(parent, id=id, *args, **kwargs)
        self.frame = parent.GetParent()
        self.create_display()
        self.dirty = False

    def create_display(self):
        self.title = "Ledger Data Entry"
        self.bg_color = wx.Colour(200, 255, 170)     # Green
        self.w_bg_color = wx.Colour(255, 253, 208)   # Cream
        self.w_fg_color = wx.Colour(50, 50, 204)     # Dark Blue
        self.w1_bg_color = wx.Colour(222, 237, 230)  # Gray
        self.tc_width = 120
        self.SetBackgroundColour(self.bg_color)
        self.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_NORMAL, 0, ''))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        widget_00 = wx.StaticText(self, wx.ID_ANY, self.title)
        widget_00.SetFont(title_font)
        widget_00.SetForegroundColour(self.w_fg_color)
        sizer.Add(widget_00, 0, wx.CENTER, 0)

        # Search for specific date of item.
        srch_widget = BadiDatePickerCtrl(self, wx.ID_ANY)
        srch_widget.SetBackgroundColour(self.w_bg_color)
        srch_widget.SetForegroundColour(self.w_fg_color)
        srch_widget.SetMinSize((130, 28))
        srch_widget.Bind(EVT_BADI_DATE_CHANGED, self.search_event)
        sizer.Add(srch_widget, 0, wx.CENTER | wx.ALL, 6)

        # View previous and next item.
        left = FlatArrowButton(self, label="←", direction='left',
                               tooltip="Previous Item")
        right = FlatArrowButton(self, label="→", direction='right',
                                tooltip="Next Item")
        left.Bind(EVT_FLAT_ARROW, self.on_arrow)
        right.Bind(EVT_FLAT_ARROW, self.on_arrow)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(left, 0, wx.ALL, 10)
        btn_sizer.Add(right, 0, wx.ALL, 10)
        btn_sizer.AddStretchSpacer()
        sizer.Add(btn_sizer, 0, wx.CENTER, 0)

        self.gbs = wx.GridBagSizer(2, 2)
        sizer.Add(self.gbs, 1, wx.CENTER, 10)

        widget_01 = wx.StaticText(self, wx.ID_ANY, "Date:")
        widget_01.SetForegroundColour(self.w_fg_color)
        widget_01.SetMinSize((-1, -1))
        self.gbs.Add(widget_01, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        widget_02 = BadiDatePickerCtrl(self, wx.ID_ANY)
        widget_02.SetBackgroundColour(self.w_bg_color)
        widget_02.SetForegroundColour(self.w_fg_color)
        widget_02.SetMinSize((130, 28))
        widget_02.SetFocus()
        #widget_02.Bind(EVT_BADI_DATE_CHANGED, self.set_dirty_flag)
        self.gbs.Add(widget_02, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.ALL, 6)

        widget_03 = wx.StaticText(self, wx.ID_ANY, "Description")
        widget_03.SetForegroundColour(self.w_fg_color)
        widget_03.SetMinSize((-1, -1))
        self.gbs.Add(widget_03, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        widget_04 = wx.Button(self, wx.ID_CLEAR, label='')
        widget_04.SetBackgroundColour(self.w_fg_color)
        widget_04.SetMinSize((48, 24))
        self.gbs.Add(widget_04, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.LEFT, 6)

        widget_05 = wx.StaticLine(self, wx.ID_ANY)
        widget_05.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(widget_05, (2, 0), (1, 2), wx.EXPAND | wx.TOP
                     | wx.BOTTOM, 4)

        self._checkboxes = {}
        self._textctrles = {}
        # 1st is the category name the rest are the StaticText labels.
        labels = ("description", "Contribution:", "Distribution:", "Expense:",
                  "Other:")
        self.create_widgets(3, 1, 'top', labels, 3)
        # We need to bind after the method call above, because the two
        # dicts above are not updated until method is called.
        widget_04.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(labels[0]))

        widget_05 = wx.StaticText(self, wx.ID_ANY, "Entry Type")
        widget_05.SetForegroundColour(self.w_fg_color)
        widget_05.SetMinSize((-1, -1))
        self.gbs.Add(widget_05, (8, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        widget_06 = wx.Button(self, wx.ID_CLEAR, label='')
        widget_06.SetBackgroundColour(self.w_fg_color)
        widget_06.SetMinSize((48, 24))
        self.gbs.Add(widget_06, (8, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.LEFT, 6)

        widget_07 = wx.StaticLine(self, wx.ID_ANY)
        widget_07.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(widget_07, (9, 0), (1, 2), wx.EXPAND | wx.TOP
                     | wx.BOTTOM, 4)

        # 1st is the category name the rest are the StaticText labels.
        labels = ("entry_type", "Check Number:", "Receipt Number:", "Debit:",
                  "OCS:")
        self.create_widgets(2, 2, 'bottom', labels, 10)
        # We need to bind after the method call above, because the two
        # dicts above are not updated until method is called.
        widget_06.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(labels[0]))

        widget_08 = wx.StaticText(self, wx.ID_ANY, "Cash in Bank")
        widget_08.SetForegroundColour(self.w_fg_color)
        widget_08.SetMinSize((-1, -1))
        self.gbs.Add(widget_08, (15, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        widget_09 = wx.Button(self, wx.ID_CLEAR, label='')
        widget_09.SetBackgroundColour(self.w_fg_color)
        widget_09.SetMinSize((48, 24))
        self.gbs.Add(widget_09, (15, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.LEFT, 6)

        widget_10 = wx.StaticLine(self, wx.ID_ANY)
        widget_10.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(widget_10, (16, 0), (1, 2), wx.EXPAND | wx.TOP
                     | wx.BOTTOM, 4)

        # 1st is the category name the rest are the StaticText labels.
        labels = ("bank", "@Deposit Amount:", "@Check Amount:",
                  "@Dedit Amount:", "@OCS Amount:", "%Balance:")
        self.create_widgets(0, 5, 'top', labels, 17)
        # We need to bind after the method call above, because the two
        # dicts above are not updated until method is called.
        widget_09.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(labels[0]))

        widget_11 = wx.StaticText(self, wx.ID_ANY, "Income")
        widget_11.SetForegroundColour(self.w_fg_color)
        widget_11.SetMinSize((-1, -1))
        self.gbs.Add(widget_11, (23, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        widget_12 = wx.Button(self, wx.ID_CLEAR, label='')
        widget_12.SetBackgroundColour(self.w_fg_color)
        widget_12.SetMinSize((48, 24))
        self.gbs.Add(widget_12, (23, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.LEFT, 6)

        widget_13 = wx.StaticLine(self, wx.ID_ANY)
        widget_13.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(widget_13, (24, 0), (1, 2), wx.EXPAND | wx.TOP
                     | wx.BOTTOM, 4)

        # 1st is the category name the rest are the StaticText labels.
        labels = ("income", "@Local Fund:", "@Contributed Expense:", "@Misc:")
        self.create_widgets(0, 3, 'bottom', labels, 25)
        # We need to bind after the method call above, because the two
        # dicts above are not updated until method is called.
        widget_12.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(labels[0]))

        widget_14 = wx.StaticText(self, wx.ID_ANY, "Expenses")
        widget_14.SetForegroundColour(self.w_fg_color)
        widget_14.SetMinSize((-1, -1))
        self.gbs.Add(widget_14, (29, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        widget_15 = wx.StaticLine(self, wx.ID_ANY)
        widget_15.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(widget_15, (30, 0), (1, 2), wx.EXPAND | wx.TOP
                     | wx.BOTTOM, 4)
        items = self._tmd.panel_config.get('budget', {}).get('widgets', {})
        self._tcp.current_panel = items
        labels = [f"@{n}"
                  for n in self._tcp.field_names_by_category['Expenses']]
        labels.insert(0, '&expenses')
        self.create_widgets(0, len(labels)-1, 'top', labels, 31)

        self.SetupScrolling(rate_x=20, rate_y=40)
        self.Hide()

    def search_event(self, event):
        print("Initiated a search event.")

    def on_arrow(self, event):
        direction = event.GetDirection()
        print(f"{direction.capitalize()} arrow clicked")
        event.Skip()

    @property
    def background_color(self):
        """
        This is for the ShortCuts panel.
        """
        return self.bg_color
