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
        title_widget = wx.StaticText(self, wx.ID_ANY, self.title)
        title_widget.SetFont(title_font)
        title_widget.SetForegroundColour(self.w_fg_color)
        sizer.Add(title_widget, 0, wx.CENTER, 0)

        # Search for specific date of item.
        srch_text = wx.StaticText(self, wx.ID_ANY, "Search:")
        srch_text.SetForegroundColour(self.w_fg_color)
        srch_widget = BadiDatePickerCtrl(self, wx.ID_ANY)
        srch_widget.SetBackgroundColour(self.w_bg_color)
        srch_widget.SetForegroundColour(self.w_fg_color)
        srch_widget.SetMinSize((130, 28))
        srch_widget.Bind(EVT_BADI_DATE_CHANGED, self.search_event)
        srch_sizer = wx.BoxSizer(wx.HORIZONTAL)
        srch_sizer.AddStretchSpacer()
        srch_sizer.Add(srch_text, 0, wx.ALL, 6)
        srch_sizer.Add(srch_widget, 0, wx.ALL, 6)
        srch_sizer.AddStretchSpacer()
        sizer.Add(srch_sizer, 0, wx.CENTER, 0)

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
        pos = 0

        widget_01 = wx.StaticText(self, wx.ID_ANY, "Date:")
        widget_01.SetForegroundColour(self.w_fg_color)
        widget_01.SetMinSize((-1, -1))
        self.gbs.Add(widget_01, (pos, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        widget_02 = BadiDatePickerCtrl(self, wx.ID_ANY)
        widget_02.SetBackgroundColour(self.w_bg_color)
        widget_02.SetForegroundColour(self.w_fg_color)
        widget_02.SetMinSize((130, 28))
        widget_02.SetFocus()
        #widget_02.Bind(EVT_BADI_DATE_CHANGED, self.set_dirty_flag)
        self.gbs.Add(widget_02, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.ALL, 6)

        self._checkboxes = {}
        self._textctrles = {}
        title_gen = self._title_generator()
        # The first label is the category name the rest are the StaticText
        # labels.
        label_gen = self._label_generator()
        title_data, labels = self._next_title_and_labels(title_gen, label_gen)
        pos += 2

        while title_data is not None and labels is not None:
            title = title_data[0]
            num_cb = title_data[1]
            num_txt = title_data[2]
            cb_pos = title_data[3]
            span = title_data[4]
            btn = title_data[5]
            button, pos = self._make_heading(title, pos, span=span, btn=btn)
            pos = self.create_widgets(num_cb, num_txt, cb_pos, labels, pos)

            if button:
                # We need to bind after the method call above, because the
                # two dicts above are not updated until the method is called.
                button.Bind(wx.EVT_BUTTON,
                            self.reset_inputs_wrapper(labels[0]))

            # Next
            pos += 1
            title_data, labels = self._next_title_and_labels(title_gen,
                                                             label_gen)

        self.SetupScrolling(rate_x=20, rate_y=40)
        self.Hide()

    def _title_generator(self):
        return (title_data for title_data in self._tmd.data_entry_title_data)

    def _label_generator(self):
        entry_labels = self._tmd.data_entry_labels
        items = self._tmd.panel_config.get('budget', {}).get('widgets', {})
        self._tcp.current_panel = items
        exp = 'Expenses'
        expense_title = ''

        for title, labels in self._tcp.field_names_by_category.items():
            if title == exp:
                expense_title = title
                labels = []

            if expense_title != exp:
                continue

            labels = [f'@{n}' for n in labels]
            labels.insert(0, f"&{make_name(title)}")
            entry_labels.append(labels)

        return (item for item in entry_labels)

    def _make_heading(self, title: str, pos: int, *, span: int=2,
                      btn: bool=True) -> int:
        text = wx.StaticText(self, wx.ID_ANY, title)
        text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ''))
        text.SetForegroundColour(self.w_fg_color)
        text.SetMinSize((-1, -1))
        self.gbs.Add(text, (pos, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)

        if btn:
            button = wx.Button(self, wx.ID_CLEAR, label='')
            button.SetBackgroundColour(self.w_fg_color)
            button.SetMinSize((48, 24))
            self.gbs.Add(button, (pos, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                        | wx.LEFT, 6)
        else:
            button = None

        line = wx.StaticLine(self, wx.ID_ANY)
        line.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(line, (pos+1, 0), (1, span), wx.EXPAND | wx.TOP
                     | wx.BOTTOM, 4)
        return button, pos + 2

    def _next_title_and_labels(self, title_gen, label_gen):
        try:
            title = next(title_gen)
        except StopIteration:
            title = None
            labels = None
        else:
            try:
                labels = next(label_gen)
            except StopIteration:
                pass

        return title, labels

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
