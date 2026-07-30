# -*- coding: utf-8 -*-
#
# src/data_entry.py
#
__docformat__ = "restructuredtext en"

import re
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .config import TomlMetaData, TomlCreatePanel
from .utilities import StoreObjects, MutuallyExclusiveWidgets, make_name
from .bases import BasePanel
from .custom_widgits import (BadiDatePickerCtrl, EVT_BADI_DATE_CHANGED,
                             FlatArrowButton, EVT_FLAT_ARROW)


class LedgerDataEntry(ScrolledPanel, BasePanel, MutuallyExclusiveWidgets):
    """
    Implements data entry into the ledger.
    """
    _tmd = TomlMetaData()
    _tcp = TomlCreatePanel()

    def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
        super().__init__(parent, id=id, *args, **kwargs)
        BasePanel.__init__(self, *args, **kwargs)
        self._so = StoreObjects()
        self.frame = parent.GetParent()
        self.dirty = False
        self.create_display()

    def create_display(self):
        self.title = "Ledger Data Entry"
        self.bg_color = wx.Colour(200, 255, 170)     # Green
        self.w_bg_color = wx.Colour(255, 253, 208)   # Cream
        self.w_fg_color = wx.Colour(50, 50, 204)     # Dark Blue
        self.w1_bg_color = wx.Colour(222, 237, 230)  # Gray
        self.tc_width = 130
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
        search = wx.Button(self, wx.BU_EXACTFIT, label='Search')
        search.SetMinSize((-1, 26))
        search.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_NORMAL, 0, ''))
        search.SetBackgroundColour(self.w1_bg_color)
        search.SetForegroundColour(self.w_fg_color)
        search.Bind(wx.EVT_BUTTON, self.search_box)
        sizer.Add(search, 0, wx.CENTER | wx.TOP, 6)

        # View previous and next item
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

        widget_01 = wx.StaticText(self, wx.ID_ANY, "Transaction ID:")
        widget_01.SetForegroundColour(self.w_fg_color)
        widget_01.SetMinSize((-1, -1))
        self.gbs.Add(widget_01, (pos, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        widget_02 = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY,
                                name='')
        widget_02.Enable(False)
        widget_02.SetBackgroundColour(self.w1_bg_color)
        widget_02.SetForegroundColour(self.w_fg_color)
        widget_02.SetMinSize((self.tc_width+6, 26))
        widget_02.category = 'panel'
        self.gbs.Add(widget_02, (pos, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        pos += 1

        widget_03 = wx.StaticText(self, wx.ID_ANY, "Date:")
        widget_03.SetForegroundColour(self.w_fg_color)
        widget_03.SetMinSize((-1, -1))
        self.gbs.Add(widget_03, (pos, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        widget_04 = BadiDatePickerCtrl(self, wx.ID_ANY,
                                       bgcolor=self.w_bg_color)
        widget_04.SetBackgroundColour(self.w_bg_color)
        widget_04.SetForegroundColour(self.w_fg_color)
        widget_04.SetMinSize((self.tc_width+6, 28))
        widget_04.SetFocus()
        widget_04.Bind(EVT_BADI_DATE_CHANGED, self.set_dirty_flag)
        widget_04.mandatory = True
        widget_04.category = 'panel'
        self.gbs.Add(widget_04, (pos, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        pos += 1

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        widget_05 = wx.StaticText(self, wx.ID_ANY, "Memo:")
        widget_05.SetForegroundColour(self.w_fg_color)
        widget_05.SetMinSize((-1, -1))
        sizer_1.Add(widget_05, 0, wx.RIGHT | wx.TOP, 6)
        widget_06 = wx.TextCtrl(self, wx.ID_ANY, "", style=0, name='')
        widget_06.SetBackgroundColour(self.w_bg_color)
        widget_06.SetForegroundColour(self.w_fg_color)
        widget_06.SetMinSize((470, 26))
        widget_06.category = 'panel'
        sizer_1.Add(widget_06, 0, wx.EXPAND | wx.TOP, 4)
        self.gbs.Add(sizer_1, (pos, 0), (1, 2), wx.EXPAND, 0)

        title_gen = self._title_generator()
        # The first label is the category name the rest are StaticText labels.
        label_gen = self._label_generator()
        title_data, labels = self._next_title_and_labels(title_gen, label_gen)
        pos += 2
        self._de_labels = {'panel': [make_name(widget_01.GetLabel()),
                                     make_name(widget_03.GetLabel()),
                                     make_name(widget_05.GetLabel())]}

        while title_data is not None and labels is not None:
            title, num_cb, num_txt, cb_pos, span, btn = title_data[:6]
            button, pos = self._make_heading(title, pos, span=span, btn=btn)
            pos = self.create_widgets(num_cb, num_txt, cb_pos, labels, pos)
            label = labels[0]
            self._de_labels[make_name(label)] = [make_name(lbl)
                                                 for lbl in labels[1:]]

            if button:
                # We need to bind after the method call above, because the
                # two dicts above are not updated until the method is called.
                button.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(label))

            # Next
            pos += 1
            title_data, labels = self._next_title_and_labels(
                title_gen, label_gen)

        line = wx.StaticLine(self, wx.ID_ANY)
        line.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(line, (pos, 0), (1, 1), wx.EXPAND | wx.TOP | wx.BOTTOM, 4)
        pos += 1

        balance_text = wx.StaticText(self, wx.ID_ANY, "Total Expenses:")
        balance_text.SetForegroundColour(self.w_fg_color)
        balance_text.SetMinSize((-1, -1))
        self.gbs.Add(balance_text, (pos, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT, 6)
        balance_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY,
                                   name='')
        balance_ctrl.SetBackgroundColour(self.w1_bg_color)
        balance_ctrl.SetForegroundColour(self.w_fg_color)
        balance_ctrl.SetMinSize((self.tc_width, 26))
        balance_ctrl.category = 'expenses'
        self.gbs.Add(balance_ctrl, (pos, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.LEFT, 6)
        pos += 1

        line = wx.StaticLine(self, wx.ID_ANY)
        line.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(line, (pos, 0), (1, 2), wx.EXPAND | wx.TOP | wx.BOTTOM, 4)
        pos += 1

        panel_0 = wx.Panel(self)
        sizer_1 = wx.StdDialogButtonSizer()
        save_wgt = wx.Button(panel_0, wx.ID_FORWARD, label='&Save')
        save_wgt.SetMinSize((-1, -1))
        save_wgt.SetBackgroundColour(wx.Colour(50, 50, 204))
        save_wgt.Bind(wx.EVT_BUTTON, self.button_save)
        cancel_wgt = wx.Button(panel_0, wx.ID_CANCEL, label='')
        cancel_wgt.SetMinSize((-1, -1))
        cancel_wgt.SetBackgroundColour(wx.Colour(50, 50, 204))
        sizer_1.AddButton(save_wgt)
        cancel_wgt.Bind(wx.EVT_BUTTON, self.button_cancel)
        sizer_1.AddButton(cancel_wgt)
        sizer_1.Realize()
        panel_0.SetSizer(sizer_1)
        self.gbs.Add(panel_0, (pos, 0), (1, 1), wx.EXPAND, 0)

        self.SetupScrolling(rate_x=20, rate_y=40)
        self.Hide()

    @property
    def ledger_labels(self) -> dict:
        skip = []

        for key, value in self._de_labels.items():
            if not value:
                skip.append(key)
                break

            skip.append(key)

        tmp = {key: self._de_labels[key] for key in skip}
        tmp[skip[-1]] = {k: v for k, v in self._de_labels.items()
                         if k not in skip}
        return tmp

    def button_save(self, event):
        self.save = True
        event.Skip()

    @property
    def save(self):
        return self._save

    @save.setter
    def save(self, value):
        if self.dirty:
            mf = self._so.get_object('MainFrame')
            mf.statusbar_message = 'Saving data.'

        self._save = value

    def button_cancel(self, event):
        self.cancel = True
        event.Skip()

    @property
    def cancel(self):
        return self._cancel

    @cancel.setter
    def cancel(self, value):
        if self.dirty:
            mf = self._so.get_object('MainFrame')
            mf.statusbar_message = 'Restoring data.'

        self._cancel = value

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
                      btn: bool=True) -> tuple:
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

    def _next_title_and_labels(self, title_gen, label_gen) -> tuple:
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

    def search_box(self, event) -> None:
        dlg = SearchDialog(self, self.bg_color, self.w_fg_color)
        dlg.ShowModal()

    def on_arrow(self, event) -> None:
        direction = event.GetDirection()
        print(f"{direction.capitalize()} arrow clicked")
        event.Skip()

    @property
    def background_color(self) -> wx.Colour:
        """
        This is for the ShortCuts panel.
        """
        return self.bg_color


class SearchDialog(wx.Dialog):
    """
    Create a search dialog for the ledger panel.
    """

    def __init__(self, parent, bg_color, fg_color):
        super().__init__(parent, wx.ID_ANY, "Search Ledger",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self._parent = parent
        self._so = StoreObjects()
        title = "Search for Ledger Records"
        w_bg_color = wx.Colour(255, 253, 208)  # Cream
        w_fg_color = wx.Colour(255, 0, 0)      # Red-ish
        self.SetSize((350, 375))
        self.SetBackgroundColour(bg_color)
        self.SetForegroundColour(fg_color)
        self.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_NORMAL, 0, ''))

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        message = wx.StaticText(self, wx.ID_ANY, title)
        message.SetBackgroundColour(wx.Colour(bg_color))
        message.SetForegroundColour(wx.Colour(fg_color))
        message.SetFont(title_font)
        sizer.Add(message, 0, wx.ALL | wx.CENTER, 10)

        self.gbs = wx.GridBagSizer(2, 2)
        sizer.Add(self.gbs, 1, wx.CENTER, 10)

        # Search for specific date of item.
        srch_text = wx.StaticText(self, wx.ID_ANY, "Date:")
        srch_text.SetForegroundColour(fg_color)
        self.gbs.Add(srch_text, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        self.srch_ctrl = BadiDatePickerCtrl(self, wx.ID_ANY)
        self.srch_ctrl.SetBackgroundColour(w_bg_color)
        self.srch_ctrl.SetForegroundColour(fg_color)
        self.srch_ctrl.SetMinSize((130, 28))
        self.srch_ctrl.SetValue('')
        self.gbs.Add(self.srch_ctrl, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)

        trans_text = wx.StaticText(self, wx.ID_ANY, "Transaction ID:")
        trans_text.SetForegroundColour(fg_color)
        self.gbs.Add(trans_text, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        trans_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=0, name='')
        trans_ctrl.SetBackgroundColour(w_bg_color)
        trans_ctrl.SetForegroundColour(fg_color)
        trans_ctrl.SetMinSize((parent.tc_width, 26))
        self.gbs.Add(trans_ctrl, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)

        check_text = wx.StaticText(self, wx.ID_ANY, "Check Number:")
        check_text.SetForegroundColour(fg_color)
        self.gbs.Add(check_text, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        check_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=0, name='')
        check_ctrl.SetBackgroundColour(w_bg_color)
        check_ctrl.SetForegroundColour(fg_color)
        check_ctrl.SetMinSize((parent.tc_width, 26))
        self.gbs.Add(check_ctrl, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)

        rcpt_text = wx.StaticText(self, wx.ID_ANY, "Receipt Number:")
        rcpt_text.SetForegroundColour(fg_color)
        self.gbs.Add(rcpt_text, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        rcpt_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=0, name='')
        rcpt_ctrl.SetBackgroundColour(w_bg_color)
        rcpt_ctrl.SetForegroundColour(fg_color)
        rcpt_ctrl.SetMinSize((parent.tc_width, 26))
        self.gbs.Add(rcpt_ctrl, (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)

        memo_text = wx.StaticText(self, wx.ID_ANY, "Memo:")
        memo_text.SetForegroundColour(fg_color)
        self.gbs.Add(memo_text, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)
        memo_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=0, name='')
        memo_ctrl.SetBackgroundColour(w_bg_color)
        memo_ctrl.SetForegroundColour(fg_color)
        memo_ctrl.SetMinSize((parent.tc_width, 26))
        self.gbs.Add(memo_ctrl, (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL
                     | wx.RIGHT | wx.BOTTOM, 6)

        self.warn_text = wx.StaticText(self, wx.ID_ANY, label="",
                                       style=wx.ALIGN_CENTER_HORIZONTAL)
        self.warn_text.SetForegroundColour(w_fg_color)
        self.warn_text.Hide()
        self.gbs.Add(self.warn_text, (5, 0), (1, 2),
                     wx.ALIGN_CENTER | wx.ALL, 6)

        panel_0 = wx.Panel(self)
        sizer_1 = wx.StdDialogButtonSizer()
        search_byn = wx.Button(panel_0, wx.ID_FORWARD, label='&Search')
        search_byn.SetMinSize((-1, -1))
        search_byn.SetBackgroundColour(wx.Colour(50, 50, 204))
        search_byn.Bind(wx.EVT_BUTTON, self.button_search)
        sizer_1.AddButton(search_byn)
        cancel_byn = wx.Button(panel_0, wx.ID_CANCEL, label='')
        cancel_byn.SetMinSize((-1, -1))
        cancel_byn.SetBackgroundColour(wx.Colour(*(50, 50, 204)))
        cancel_byn.Bind(wx.EVT_BUTTON, self.button_cancel)
        sizer_1.AddButton(cancel_byn)
        sizer_1.Realize()
        panel_0.SetSizer(sizer_1)
        self.gbs.Add(panel_0, (6, 0), (1, 2), wx.EXPAND, 0)

    def button_search(self, event):
        db = self._so.get_object('Database')
        valid = db.ledger_search_panel(self)

        if valid:
            self.Destroy()
        else:
            msg = ("Can only search for one item at a time. Please click "
                   "Cancel and try again.")
            self.warn_text.SetLabel(msg)
            self.warn_text.Wrap(250)
            self.warn_text.Show()
            self.Layout()

    def button_cancel(self, event):
        self.Destroy()
