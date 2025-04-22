# -*- coding: utf-8 -*-
#
# src/custom_widgits.py
#
__docformat__ = "restructuredtext en"

import re
import wx
import wx.adv
import badidatetime


def ordered_month():
    """
    Numerically order Badí' months in a dict.

    :returns: A list of tuples in the form of [(<month name>, <order>), ...]]
    :rtype: list
    """
    numbers = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
               12, 13, 14, 15, 16, 17, 18, 0, 19)
    return dict([(numbers[idx], month)
                 for idx, month in enumerate(badidatetime.MONTHNAMES)])


# Custom event
wxEVT_BADI_DATE_CHANGED_TYPE = wx.NewEventType()
EVT_BADI_DATE_CHANGED = wx.PyEventBinder(wxEVT_BADI_DATE_CHANGED_TYPE, 1)


class BadiDateChangedEvent(wx.PyCommandEvent):
    def __init__(self, source, bdate):
        super().__init__(wxEVT_BADI_DATE_CHANGED_TYPE, source.GetId())
        self._bdate = bdate

    def GetBadiDate(self):
        return self._bdate


class BadiCalendarPopup(wx.PopupTransientWindow):
    def __init__(self, parent, bdate: badidatetime.date):
        super().__init__(parent, wx.BORDER_SIMPLE)
        self.panel = wx.Panel(self)
        self.bdate = bdate
        self.on_date_selected = None  # callback

        self.grid_sizer = wx.GridSizer(rows=4, cols=5, hgap=5, vgap=5)
        self._populate_days()

        vbox = wx.BoxSizer(wx.VERTICAL)
        label = ordered_month()[bdate.month]
        header = wx.StaticText(self.panel, label=label)
        font = header.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(font)

        vbox.Add(header, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        vbox.Add(self.grid_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        self.panel.SetSizer(vbox)
        self.Fit()

    def _populate_days(self):
        self.grid_sizer.Clear(delete_windows=True)
        max_day = self._max_days_in_month(self.bdate.year, self.bdate.month)

        for day in range(1, max_day + 1):
            btn = wx.Button(self.panel, label=str(day), size=(32, 32))
            btn.Bind(wx.EVT_BUTTON, self._on_day_clicked)
            btn.day = day
            self.grid_sizer.Add(btn, 0, wx.ALL, 2)

    def _max_days_in_month(self, year, month):
        return 4 + self.bdate._is_leap_year(year) if month == 0 else 19

    def _on_day_clicked(self, event):
        day = event.GetEventObject().day
        new_date = badidatetime.date(self.bdate.year, self.bdate.month, day)

        if self.on_date_selected:
            self.on_date_selected(new_date)

        self.Dismiss()


class BadiDatePickerCtrl(wx.Panel):
    """
    Customized Badí' date widget.
    """
    def __init__(self, parent: wx.Window, id: int=wx.ID_ANY,
                 dt: badidatetime.date=None, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.adv.DP_DEFAULT | wx.adv.DP_SHOWCENTURY,
                 validator=wx.DefaultValidator, name: str="badidatectrl"
                 ) -> None:
        super().__init__(parent)
        #self.SetSize(260, 20)
        # Default date
        self.bdate = dt or badidatetime.date.today(short=True)

        self.text_ctrl = wx.TextCtrl(self, style=wx.BORDER_NONE)
        self.text_ctrl.SetValue(self.bdate.isoformat())
        self.text_ctrl.SetBackgroundColour(wx.Colour(222, 237, 230))
        self.text_ctrl.SetForegroundColour(wx.Colour(0, 0, 0))
        self.text_ctrl.Bind(wx.EVT_TEXT, self.on_change)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_BUTTON, (16, 16))
        self.calendar_btn = wx.BitmapButton(self, bitmap=bmp,
                                            style=wx.BU_AUTODRAW)
        self.calendar_btn.Bind(wx.EVT_BUTTON, self.show_popup_calendar)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.text_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
        self.text_ctrl.SetMinSize((90, -1))  # Set the minimum size
        self.SetMinSize((130, -1))
        sizer.AddStretchSpacer()
        sizer.Add(self.calendar_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(sizer)

    def _max_days_in_month(self, year, month):
        return 4 + self.bdate._is_leap_year(year) if month == 0 else 19

    def on_change(self, event):
        text = self.text_ctrl.GetValue()
        parts = re.split(r'[-/.]', text)

        if len(parts) == 3:
            date = [int(p) for p in parts]
            self.bdate = badidatetime.date(*date)
            wx.PostEvent(self, BadiDateChangedEvent(self, self.bdate))

    def show_popup_calendar(self, event):
        popup = BadiCalendarPopup(self, self.bdate)
        popup.on_date_selected = self._on_popup_date_selected
        btn_pos = self.ClientToScreen(self.calendar_btn.GetPosition())
        btn_size = self.calendar_btn.GetSize()
        popup.Position(btn_pos, (0, btn_size.height))
        popup.Popup()

    def _on_popup_date_selected(self, new_bdate):
        self.SetValue(new_bdate)
        evt = BadiDateChangedEvent(self, new_bdate)
        wx.PostEvent(self, evt)

    def GetValue(self):
        return self.bdate

    def SetValue(self, b_date: badidatetime.date):
        self.bdate = b_date
        self.year_spin.SetValue(b_date.year)
        self.month_choice.SetSelection(b_date.month)
        self.day_spin.SetRange(
            1, self._max_days_in_month(b_date.year, b_date.month))
        self.day_spin.SetValue(b_date.day)
