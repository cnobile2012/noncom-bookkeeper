# -*- coding: utf-8 -*-
#
# src/ledger_entry.py
#
__docformat__ = "restructuredtext en"

import re
import wx

from decimal import Decimal
from wx.dataview import DataViewListCtrl, DV_SINGLE
from wx.lib.scrolledpanel import ScrolledPanel

from .config import TomlMetaData, TomlCreatePanel
from .utilities import StoreObjects, MutuallyExclusiveWidgets, make_name
from .bases import BasePanel
from .custom_widgits import (BadiDatePickerCtrl, EVT_BADI_DATE_CHANGED,
                             FlatArrowButton, EVT_FLAT_ARROW)


class _CreateWidgets:
    _tmd = TomlMetaData()
    _tcp = TomlCreatePanel()

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
        self.gbs.Add(text, (pos, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)

        if btn:
            button = wx.Button(self, wx.ID_CLEAR, label='')
            button.SetBackgroundColour(self.w_fg_color)
            button.SetMinSize((48, 24))
            self.gbs.Add(button, (pos, 1), (1, 1),
                         wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
        else:
            button = None

        line = wx.StaticLine(self, wx.ID_ANY)
        line.SetBackgroundColour(self.w_fg_color)
        self.gbs.Add(line, (pos+1, 0), (1, span),
                     wx.EXPAND | wx.TOP | wx.BOTTOM, 4)
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
            except StopIteration:  # pragma: no cover
                pass

        return title, labels


class LedgerDataEntry(ScrolledPanel, BasePanel, _CreateWidgets,
                      MutuallyExclusiveWidgets):
    """
    Implements data entry into the ledger.
    """
    _BUTTON_OBJS = []

    def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
        super().__init__(parent, id, *args, **kwargs)
        BasePanel.__init__(self, *args, **kwargs)
        self.sd = None
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
        sizer.Add(self.gbs, 0, wx.CENTER | wx.ALL, 10)
        pos = 0

        widget_01 = wx.StaticText(self, wx.ID_ANY, "Transaction ID:")
        widget_01.SetForegroundColour(self.w_fg_color)
        widget_01.SetMinSize((-1, -1))
        self.gbs.Add(widget_01, (pos, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        widget_02 = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY,
                                name='')
        widget_02.Enable(False)
        widget_02.SetBackgroundColour(self.w1_bg_color)
        widget_02.SetForegroundColour(self.w_fg_color)
        widget_02.SetMinSize((self.tc_width+6, 26))
        widget_02.category = 'panel'
        self.gbs.Add(widget_02, (pos, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        pos += 1

        widget_03 = wx.StaticText(self, wx.ID_ANY, "Date:")
        widget_03.SetForegroundColour(self.w_fg_color)
        widget_03.SetMinSize((-1, -1))
        self.gbs.Add(widget_03, (pos, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        widget_04 = BadiDatePickerCtrl(self, wx.ID_ANY,
                                       bgcolor=self.w_bg_color)
        widget_04.SetBackgroundColour(self.w_bg_color)
        widget_04.SetForegroundColour(self.w_fg_color)
        widget_04.SetMinSize((self.tc_width+6, 28))
        widget_04.SetFocus()
        widget_04.Bind(EVT_BADI_DATE_CHANGED, self.set_dirty_flag)
        widget_04.mandatory = True
        widget_04.category = 'panel'
        self.gbs.Add(widget_04, (pos, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
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
                self._BUTTON_OBJS.append(button)

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
        self.gbs.Add(balance_text, (pos, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.balance_ctrl = wx.TextCtrl(self, wx.ID_ANY, "",
                                        style=wx.TE_READONLY, name='')
        self.balance_ctrl.SetBackgroundColour(self.w1_bg_color)
        self.balance_ctrl.SetForegroundColour(self.w_fg_color)
        self.balance_ctrl.SetMinSize((self.tc_width, 26))
        self.balance_ctrl.category = 'panel'
        self.balance_ctrl.financial = True
        self.gbs.Add(self.balance_ctrl, (pos, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
        self._de_labels['panel'] += [make_name(balance_text.GetLabel())]
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

        self._scroll_rate = (20, 40)
        self.SetupScrolling(rate_x=self._scroll_rate[0],
                            rate_y=self._scroll_rate[1])
        self.Hide()

    # def refresh_scrolling(self):
    #     """
    #     Recompute this panel's virtual scrolling size against its current
    #     real allocation. ScrolledPanel.SetupScrolling() is only accurate
    #     for whatever size the panel has *at the moment it's called* — since
    #     it originally runs during __init__ before the panel has been sized
    #     by its container's sizer, it must be re-run once the panel actually
    #     has a real, final size (i.e. when it's shown).
    #     """
    #     rate_x, rate_y = self._scroll_rate
    #     self.SetupScrolling(rate_x=rate_x, rate_y=rate_y)

    @property
    def ledger_labels(self) -> dict:
        """
        Flatten the expenses, but leave everything else alone.

        :returns: A flattened dict of all the editable fields.
        :rtype: dict
        """
        result = {}
        skip = []

        for key, value in self._de_labels.items():
            if not value:
                break

            skip.append(key)

        for key, fields in self._de_labels.items():
            if key in set(self._de_labels) - set(skip):
                result.setdefault("expenses", []).extend(fields)
            else:
                result[key] = fields

        return result

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
            self.reset_buttons()

        self._cancel = value

    def reset_buttons(self):
        for button in self._BUTTON_OBJS:
            event = wx.CommandEvent(wx.wxEVT_BUTTON, button.GetId())
            event.SetEventObject(button)
            button.GetEventHandler().ProcessEvent(event)

    def search_box(self, event) -> None:
        style = (wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU |
                 wx.FRAME_FLOAT_ON_PARENT | wx.FRAME_FLOAT_ON_PARENT)
        frame = wx.Frame(self, title="Search Ledger", style=style)
        frame.SetSize((400, 600))
        self.sd = SearchDialog(frame, bg_color=self.bg_color,
                               fg_color=self.w_fg_color)
        frame.Show(True)

    def on_expense_changed(self, event) -> None:
        if not self.initializing:
            self.dirty = True

        total = Decimal("0")

        for ctrl in self.expenses_ctrls:
            value = ctrl.GetValue().strip()

            if value:
                total += Decimal(value)

        self.balance_ctrl.SetValue(f"{total:.2f}")
        event.Skip()

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


class SearchDialog(ScrolledPanel, BasePanel, _CreateWidgets,
                   MutuallyExclusiveWidgets):
    """
    Create a search dialog for the ledger panel.
    """

    def __init__(self, parent, id=wx.ID_ANY, *args, bg_color=None,
                 fg_color=None, **kwargs):
        super().__init__(parent, id, *args, **kwargs)
        self.parent = parent
        self._so = StoreObjects()
        self.w_fg_color = wx.Colour(50, 50, 204)     # Dark Blue
        self.w_bg_color = wx.Colour(255, 253, 208)   # Cream
        self.w1_bg_color = wx.Colour(222, 237, 230)  # Gray
        w1_fg_color = wx.Colour(255, 0, 0)           # Red-ish
        title = "Search for Ledger Records"
        self.tc_width = 130
        self.SetBackgroundColour(bg_color)
        self.SetForegroundColour(fg_color)
        self.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_NORMAL, 0, ''))

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        message = wx.StaticText(self, wx.ID_ANY, title)
        message.SetBackgroundColour(bg_color)
        message.SetForegroundColour(fg_color)
        message.SetFont(title_font)
        sizer.Add(message, 0, wx.ALL | wx.CENTER, 10)

        self.gbs = wx.GridBagSizer(2, 2)
        sizer.Add(self.gbs, 1, wx.CENTER, 10)
        pos = 0

        trans_text = wx.StaticText(self, wx.ID_ANY, "Transaction ID:")
        trans_text.SetForegroundColour(fg_color)
        self.gbs.Add(trans_text, (pos, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        trans_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=0, name='')
        trans_ctrl.SetBackgroundColour(self.w_bg_color)
        trans_ctrl.SetForegroundColour(fg_color)
        trans_ctrl.SetMinSize((self.tc_width, 26))
        trans_ctrl.category = 'panel'
        self.gbs.Add(trans_ctrl, (pos, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        pos += 1

        # Search for specific date of item.
        srch_text = wx.StaticText(self, wx.ID_ANY, "Date:")
        srch_text.SetForegroundColour(fg_color)
        self.gbs.Add(srch_text, (pos, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        self.srch_ctrl = BadiDatePickerCtrl(self, wx.ID_ANY)
        self.srch_ctrl.SetBackgroundColour(self.w_bg_color)
        self.srch_ctrl.SetForegroundColour(fg_color)
        self.srch_ctrl.SetMinSize((130, 28))
        self.srch_ctrl.SetValue('')
        self.srch_ctrl.category = 'panel'
        self.gbs.Add(self.srch_ctrl, (pos, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        pos += 1

        memo_text = wx.StaticText(self, wx.ID_ANY, "Memo:")
        memo_text.SetForegroundColour(fg_color)
        self.gbs.Add(memo_text, (pos, 0), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)
        memo_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=0, name='')
        memo_ctrl.SetBackgroundColour(self.w_bg_color)
        memo_ctrl.SetForegroundColour(fg_color)
        memo_ctrl.SetMinSize((self.tc_width, 26))
        memo_ctrl.category = 'panel'
        self.gbs.Add(memo_ctrl, (pos, 1), (1, 1),
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 6)

        title_gen = self._title_generator()
        # The first label is the category name the rest are StaticText labels.
        label_gen = self._label_generator()
        title_data, labels = self._next_title_and_labels(title_gen, label_gen)
        pos += 2

        while None not in (title_data, labels):
            title, num_cb, num_txt, cb_pos, span, btn = title_data[:6]
            button, pos = self._make_heading(title, pos, span=span, btn=btn)
            pos = self.create_widgets(num_cb, num_txt, cb_pos, labels, pos,
                                      search=True)
            label = labels[0]

            if button:
                button.Bind(wx.EVT_BUTTON, self.reset_inputs_wrapper(label))

            # Next
            pos += 1
            title_data, labels = self._next_title_and_labels(
                title_gen, label_gen)

            # We do not want to search expenses.
            if title_data[0] == 'Expenses':
                break

        self.warn_text = wx.StaticText(self, wx.ID_ANY, label="",
                                       style=wx.ALIGN_CENTER_HORIZONTAL)
        self.warn_text.SetForegroundColour(w1_fg_color)
        self.warn_text.Hide()
        self.gbs.Add(self.warn_text, (pos, 0), (1, 2),
                     wx.ALIGN_CENTER | wx.ALL, 6)
        pos += 1

        panel_0 = wx.Panel(self)
        sizer_1 = wx.StdDialogButtonSizer()
        search_byn = wx.Button(panel_0, wx.ID_FORWARD, label='&Continue')
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
        self.gbs.Add(panel_0, (pos, 0), (1, 2), wx.EXPAND, 0)
        self.SetupScrolling(rate_x=20, rate_y=40)

    def button_search(self, event):
        db = self._so.get_object('Database')
        rows = db.ledger_search_panel(self)
        bg = self.parent.Parent.bg_color
        fgw = self.parent.Parent.w_fg_color
        msg = "Choose Search Results"
        cap = "Search Results"

        if rows:
            self._dlg = SearchResult(self.parent, msg, cap, rows=rows,
                                     bg_color=bg, fg_color=fgw)
            self.parent.Hide()
            self._dlg.ShowModal()
        else:
            msg = ("Found no results.")
            self.warn_text.SetLabel(msg)
            self.warn_text.Wrap(250)
            self.warn_text.Show()
            self.Layout()

        event.Skip()

    def button_cancel(self, event):
        self.parent.Parent.sd = None
        event.Skip()
        self.parent.Destroy()


class SearchResult(wx.Dialog):
    """
    Show the result of the search so one can be chosen to edit.
    """

    def __init__(self, parent, msg, cap, *, rows=[], bg_color=None,
                 fg_color=None):
        super().__init__(parent, wx.ID_ANY, cap,
                         style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self.parent = parent
        self.rows = rows
        self._so = StoreObjects()
        self.SetSize((1500, 600))
        self.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD, 0, ''))
        # Red-ish
        _bg_color = bg_color if bg_color else wx.Colour(220, 130, 143)
        # Blue-ish
        _fg_color = fg_color if fg_color else wx.Colour(50, 50, 204)
        self.SetBackgroundColour(_bg_color)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        message = wx.StaticText(self, wx.ID_ANY, msg)
        message.SetBackgroundColour(_bg_color)
        message.SetForegroundColour(_fg_color)
        message.Wrap(300)
        sizer.Add(message, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        line0 = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line0, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)

        self.list_ctrl = DataViewListCtrl(self, wx.ID_ANY, style=DV_SINGLE)
        self.list_ctrl.SetMinSize((1600, 200))
        headers = ["Trans ID", "Fiscal Year", "Date", "Memo", "Trans Type",
                   "Entry Ref", "Number", "Bank Type", "Bank Amount",
                   "CoH Type", "Coh Amount", "Income Type", "Income Amount"]
        dc = wx.ClientDC(self)
        width = max([[s for s in dc.GetTextExtent(fn)][0] for fn in headers])
        [self.list_ctrl.AppendTextColumn(fn, width=width) for fn in headers]
        trn_map = {None: None, 1: 'Contribution', 2: 'Distribution',
                   3: 'Expense', 4: 'Other'}
        ref_map = {None: None, 1: 'OCS', 2: 'Check', 3: 'Receipt',
                   4: 'Deposit'}
        bnk_map = {None: None, 1: 'Deposit', 2: 'Withdrawal'}
        coh_map = {None: None, 1: 'Replenishment', 2: 'Disbursement'}
        inc_map = {None: None, 1: 'Local Fund', 2: 'Contributed Expense',
                   3: 'Other'}

        for row in rows:
            display_row = []

            for idx, itm in enumerate(row[0][:-2]):  # Remove purge & ctime
                match idx:
                    case 4:
                        itm = trn_map[itm]
                    case 5:
                        itm = ref_map[itm]
                    case 7:
                        itm = bnk_map[itm]
                    case 9:
                        itm = coh_map[itm]
                    case 11:
                        itm = inc_map[itm]

                display_row.append(str(itm))

            self.list_ctrl.AppendItem(display_row)

        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        button_sizer = wx.StdDialogButtonSizer()
        sizer.Add(button_sizer, 0, wx.CENTER | wx.ALL, 6)
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.Bind(wx.EVT_BUTTON, self.btn_continue)
        button_sizer.AddButton(ok_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL)
        cancel_button.SetDefault()
        cancel_button.Bind(wx.EVT_BUTTON, self.btn_cancel)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        sizer.Fit(self)
        self.Layout()
        self.Fit()

    def btn_cancel(self, event):
        event.Skip()
        self.Destroy()

    def btn_continue(self, event):
        """
        Populate the data in the ledger panel.
        """
        display_row = self.list_ctrl.GetSelectedRow()
        db = self._so.get_object('Database')
        mf = self._so.get_object('MainFrame')
        row = self.rows[display_row]
        data = db.convert_db_to_panel(row)
        panel = mf.panels['ledger']
        panel.initializing = True
        db.clear_panel(mf.panels['ledger'])
        db.populate_panel_values('ledger', panel, data)
        panel.initializing = False
        event.Skip()
