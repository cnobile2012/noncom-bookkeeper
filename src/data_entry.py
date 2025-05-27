# -*- coding: utf-8 -*-
#
# src/data_entry.py
#
__docformat__ = "restructuredtext en"

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .bases import BasePanel
from .custom_widgits import (BadiDatePickerCtrl, EVT_BADI_DATE_CHANGED,
                             ColorCheckBox, EVT_COLOR_CHECKBOX)


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
        self._bg_color = (200, 255, 170)  # Green
        self.w_bg_color = (222, 237, 230)
        self.w_fg_color = (50, 50, 204)  # Dark Blue
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
        self.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_NORMAL, 0, ''))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        widget_00 = wx.StaticText(self, wx.ID_ANY, self.title)
        widget_00.SetFont(title_font)
        widget_00.SetForegroundColour(wx.Colour(*self.w_fg_color))
        sizer.Add(widget_00, 0, wx.CENTER, 0)

        self.gbs = wx.GridBagSizer(2, 2)
        sizer.Add(self.gbs, 1, wx.CENTER, 10)

        widget_01 = wx.StaticText(self, wx.ID_ANY, "Date:")
        widget_01.SetForegroundColour(wx.Colour(*self.w_fg_color))
        widget_01.SetMinSize((-1, -1))
        self.gbs.Add(widget_01, (0, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        widget_02 = BadiDatePickerCtrl(self, wx.ID_ANY)
        widget_02.SetBackgroundColour(wx.Colour(*self._bg_color))
        widget_02.SetForegroundColour(wx.Colour(*self.w_fg_color))
        widget_02.SetMinSize((130, 30))
        widget_02.SetFocus()
        #widget_02.Bind(EVT_BADI_DATE_CHANGED, self.set_dirty_flag)
        self.gbs.Add(widget_02, (0, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        widget_03 = wx.StaticText(self, wx.ID_ANY, "Description")
        widget_03.SetForegroundColour(wx.Colour(*self.w_fg_color))
        widget_03.SetMinSize((-1, -1))
        self.gbs.Add(widget_03, (1, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)
        widget_04 = wx.Button(self, wx.ID_CLEAR, label='')
        widget_04.SetBackgroundColour(wx.Colour(*self.w_fg_color))
        widget_04.SetMinSize((48, 24))
        self.gbs.Add(widget_04, (1, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)

        widget_05 = wx.StaticLine(self, wx.ID_ANY)
        widget_05.SetBackgroundColour(wx.Colour(*self.w_fg_color))
        self.gbs.Add(widget_05, (2, 0), (1, 2), wx.EXPAND, 0)

        self._checkboxes = {}
        self._textctrles = {}
        # 1st is the category name the rest are the StaticText labels.
        labels = ("description", "Contribution", "Distribution", "Expense",
                  "Other")
        self._mutually_exclusive_entries(3, 1, 'top', labels, 3)
        # We need to bind after the method call above, because the two
        # dicts above are not updated until method is called.
        widget_04.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(labels[0]))

        widget_05 = wx.StaticText(self, wx.ID_ANY, "Entry Type")
        widget_05.SetForegroundColour(wx.Colour(*self.w_fg_color))
        widget_05.SetMinSize((-1, -1))
        self.gbs.Add(widget_05, (8, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)
        widget_06 = wx.Button(self, wx.ID_CLEAR, label='')
        widget_06.SetBackgroundColour(wx.Colour(*self.w_fg_color))
        widget_06.SetMinSize((48, 24))
        self.gbs.Add(widget_06, (8, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)

        widget_07 = wx.StaticLine(self, wx.ID_ANY)
        widget_07.SetBackgroundColour(wx.Colour(*self.w_fg_color))
        self.gbs.Add(widget_07, (9, 0), (1, 2), wx.EXPAND, 0)

        # 1st is the category name the rest are the StaticText labels.
        labels = ("entry_type", "Check", "Recept", "Debit", "OCS")
        self._mutually_exclusive_entries(3, 1, 'bottom', labels, 10)
        # We need to bind after the method call above, because the two
        # dicts above are not updated until method is called.
        widget_06.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(labels[0]))

        self.SetupScrolling(rate_x=20, rate_y=40)
        self.Hide()

    def _mutually_exclusive_entries(self, num_cb: int=0, num_txt: int=0,
                                    cb_pos: str='top', labels: tuple=(),
                                    pos_idx: int=0) -> None:
        assert (len(labels) - 1) == (num_cb + num_txt), (
            "The number of labels are not equal to the number of "
            "checkboxes and test controls.")
        cb_list = self._checkboxes.setdefault(labels[0], [])
        tc_list = self._textctrles.setdefault(labels[0], [])

        def create_ccbs(num_cb, labels, pos_idx):
            for num in range(num_cb):
                label = labels[num]
                st = wx.StaticText(self, wx.ID_ANY, label)
                st.SetForegroundColour(wx.Colour(*self.w_fg_color))
                self.gbs.Add(st, (pos_idx, 0), (1, 1),
                             wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
                ccb = ColorCheckBox(self, wx.ID_ANY,
                                    name=self._make_name(label))
                ccb.SetBackgroundColour(wx.Colour(*self._bg_color))
                ccb.SetForegroundColour(wx.Colour(*self.w_fg_color))
                ccb.SetMinSize((20, 20))
                self.gbs.Add(ccb, (pos_idx, 1), (1, 1),
                             wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
                cb_list.append(ccb)
                pos_idx += 1

            return pos_idx

        def create_ctrls(num_txt, labels, pos_idx):
            for num in range(num_txt):
                label = labels[num]
                st = wx.StaticText(self, wx.ID_ANY, label)
                st.SetForegroundColour(wx.Colour(*self.w_fg_color))
                self.gbs.Add(st, (pos_idx, 0), (1, 1),
                             wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
                tc = wx.TextCtrl(self, wx.ID_ANY, "", style=0,
                                 name=self._make_name(label))
                tc.SetBackgroundColour(wx.Colour(*self.w_bg_color))
                tc.SetForegroundColour(wx.Colour(*self.w_fg_color))
                tc.SetMinSize([260, -1])
                self.gbs.Add(tc, (pos_idx, 1), (1, 1),
                             wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
                tc_list.append(tc)
                pos_idx += 1

            return pos_idx

        if cb_pos == 'top':
            pos_idx = create_ccbs(num_cb, labels[1:], pos_idx)
            create_ctrls(num_txt, labels[1+num_cb:], pos_idx)

            for cb in cb_list:
                cb.Bind(EVT_COLOR_CHECKBOX,
                        self.on_checkbox_selected_wrapper(labels[0]))

            for tc in tc_list:
                tc.Bind(wx.EVT_SET_FOCUS,
                        self.on_text_focus_wrapper(labels[0]))
        else:
            pos_idx = create_ctrls(num_txt, labels[1:], pos_idx)
            create_ccbs(num_cb, labels[1+num_txt:], pos_idx)

            for cb in cb_list:
                cb.Bind(EVT_COLOR_CHECKBOX,
                        self.on_checkbox_selected_wrapper(labels[0]))

            for tc in tc_list:
                self._handling_text_event = False
                tc.Bind(wx.EVT_SET_FOCUS,
                        self.on_text_focus_wrapper(labels[0]))

    def on_checkbox_selected_wrapper(self, category_name):
        cb_list = self._checkboxes[category_name]
        tc_list = self._textctrles[category_name]

        def on_checkbox_selected(event):
            selected_cb = event.GetEventObject()

            for cb in cb_list:
                cb.Enable(cb == selected_cb)
                cb.SetValue(cb == selected_cb)

            for tc in tc_list:
                tc.Enable(False)
                tc.SetValue("")

        return on_checkbox_selected

    def on_text_focus_wrapper(self, category_name):
        cb_list = self._checkboxes[category_name]
        tc_list = self._textctrles[category_name]

        def on_text_focus(event):
            # Disable all checkboxes
            for cb in cb_list:
                cb.SetValue(False)
                cb.Enable(False)

            for tc in tc_list:
                tc.Enable(True)
                tc.SetValue("")

            event.Skip()

        return on_text_focus

    def reset_inputs_wrapper(self, category_name):
        cb_list = self._checkboxes[category_name]
        tc_list = self._textctrles[category_name]

        def reset_inputs(event):
            for cb in cb_list:
                cb.Enable(True)
                cb.SetValue(False)

            for tc in tc_list:
                tc.Enable(True)
                tc.SetValue("")

        return reset_inputs

    def _make_name(self, name: str):
        name = name.replace('(', '').replace(')', '').replace('"', '')
        return name.replace(' ', '_').replace(':', '').lower()

    @property
    def background_color(self):
        """
        This is for the ShortCuts panel.
        """
        return self._bg_color
