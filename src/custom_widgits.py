# -*- coding: utf-8 -*-
#
# src/custom_widgits.py
#
__docformat__ = "restructuredtext en"

import os
import re
import wx
import wx.adv
import badidatetime
from .config import Settings


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


class CustomTextCtrl(wx.Control):
    def __init__(self, parent, value="", style=0, **kwargs):
        super().__init__(parent, style=wx.BORDER_NONE, **kwargs)
        self.text = value
        self.style = style
        self.has_focus = False
        self.cursor_pos = len(self.text)

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize((100, 28))

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        rect = self.GetClientRect()
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255, 128),
                                  wx.BRUSHSTYLE_TRANSPARENT))
        dc.Clear()

        # Border
        if (self.style & wx.BORDER_NONE) != wx.BORDER_NONE:
            border_color = (wx.Colour(30, 144, 255) if self.has_focus
                            else wx.Colour(200, 200, 200))
            dc.SetPen(wx.Pen(border_color, 2))
            dc.DrawRectangle(rect)

        # Text
        dc.SetTextForeground(wx.BLACK)
        text_width, text_height = dc.GetTextExtent(self.text)
        # Calculate the vertical position to center the text
        y = (rect.height - text_height) // 2
        # Calculate the horizontal position to center the text (optional)
        x = (rect.width - text_width) // 2
        # Draw the text
        dc.DrawText(self.text, x, y)

        # Cursor
        if self.has_focus:
            tw, th = dc.GetTextExtent(self.text[:self.cursor_pos])
            dc.SetPen(wx.Pen(wx.BLACK, 1))
            dc.DrawLine(6 + tw, 4, 6 + tw, 4 + th)

    def on_click(self, event):
        self.SetFocus()
        event.Skip()

    def on_focus(self, event):
        self.has_focus = True
        self.Refresh()
        event.Skip()

    def on_kill_focus(self, event):
        self.has_focus = False
        self.Refresh()
        event.Skip()

    def on_char(self, event):
        key = event.GetKeyCode()

        if key == wx.WXK_TAB:
            if event.ShiftDown():
                self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                self.Navigate(wx.NavigationKeyEvent.IsForward)
        elif key == wx.WXK_BACK:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos - 1] + self.text[
                    self.cursor_pos:]
                self.cursor_pos -= 1
        elif 32 <= key < 127:
            self.text = self.text[:self.cursor_pos] + chr(key) + self.text[
                self.cursor_pos:]
            self.cursor_pos += 1
        elif key == wx.WXK_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == wx.WXK_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        else:
            event.Skip()  # Important for other keys (e.g., Shift+Tab)

        self.Refresh()

    def GetValue(self):
        return self.text

    def SetValue(self, val):
        self.text = val
        self.cursor_pos = len(val)
        self.Refresh()


# Custom Badi date event
wxEVT_BADI_DATE_CHANGED_TYPE = wx.NewEventType()
EVT_BADI_DATE_CHANGED = wx.PyEventBinder(wxEVT_BADI_DATE_CHANGED_TYPE, 1)


class BadiDateChangedEvent(wx.PyCommandEvent):
    def __init__(self, source, bdate):
        super().__init__(wxEVT_BADI_DATE_CHANGED_TYPE, source.GetId())
        self._bdate = bdate

    def GetBadiDate(self):
        return self._bdate


class BadiCalendarPopup(wx.PopupTransientWindow):
    """
    https://symbl.cc/en/emoji/symbols/
    https://www.freepik.com/icons/bitmap
    https://www.flaticon.com/free-icons/bitmap
    """
    def __init__(self, parent: wx.Window, flags=wx.BORDER_NONE,
                 bdate: badidatetime.date=None, name: str=""):
        super().__init__(parent, wx.BORDER_SIMPLE)
        self.bdate = bdate
        self.SetName(name)
        self.panel = wx.Panel(self)
        bg_color = wx.Colour(255, 253, 208)
        self.panel.SetBackgroundColour(bg_color)
        fg_color = wx.Colour(0, 0, 0)
        self.panel.SetForegroundColour(fg_color)
        self.panel.Bind(wx.EVT_PAINT, self.on_paint_border)
        self.on_date_selected = None  # callback

        vbox = wx.BoxSizer(wx.VERTICAL)
        # Navigation header
        nav_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create nav buttons
        def make_button(image):
            path = os.path.join(Settings.base_dir(), 'images', image)
            bitmap = wx.Bitmap(path, wx.BITMAP_TYPE_BMP)
            button = wx.BitmapButton(self.panel, bitmap=bitmap, size=size,
                                     style=wx.BORDER_NONE)
            button.SetBackgroundColour(bg_color)
            return button

        size = self.FromDIP((30, 36))
        prev_year = make_button('rewind-30x36.bmp')
        prev_month = make_button('reverse-30x36.bmp')
        next_month = make_button('play-30x36.bmp')
        next_year = make_button('foward-30x36.bmp')
        # Bind nav buttons
        prev_year.Bind(wx.EVT_BUTTON, self.on_prev_year)
        prev_month.Bind(wx.EVT_BUTTON, self.on_prev_month)
        next_month.Bind(wx.EVT_BUTTON, self.on_next_month)
        next_year.Bind(wx.EVT_BUTTON, self.on_next_year)
        # Header label
        self.header = wx.StaticText(
            self.panel, label="",  # updated later
            style=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        font = self.header.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(font.GetPointSize() - 2)  # reduce by 2pt
        self.header.SetFont(font)
        # Layout buttons and header
        nav_sizer.Add(prev_year, 0, wx.RIGHT, self.FromDIP(4))
        nav_sizer.Add(prev_month, 0, wx.RIGHT, self.FromDIP(8))
        nav_sizer.Add(self.header, 1, wx.ALL | wx.EXPAND)
        nav_sizer.Add(next_month, 0, wx.LEFT, self.FromDIP(8))
        nav_sizer.Add(next_year, 0, wx.LEFT, self.FromDIP(4))

        vbox.Add(nav_sizer, 0, wx.ALL | wx.EXPAND, self.FromDIP(5))

        # Grid of days
        self.grid_sizer = wx.GridSizer(rows=4, cols=5, hgap=self.FromDIP(5),
                                       vgap=self.FromDIP(5))
        vbox.Add(self.grid_sizer, 0, wx.ALL | wx.ALIGN_CENTER, self.FromDIP(5))
        self._populate_days()

        self.panel.SetSizerAndFit(vbox)
        self.update_header()

    def on_paint_border(self, event):
        dc = wx.PaintDC(self.panel)
        size = self.panel.GetSize()
        dc.SetPen(wx.Pen(wx.Colour(100, 100, 100)))  # gray border
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(0, 0, size.width - 1, size.height - 1)

    def _populate_days(self):
        self.grid_sizer.Clear(delete_windows=True)
        max_day = self._max_days_in_month(self.bdate.year, self.bdate.month)
        today = badidatetime.date.today(short=True)
        size = self.FromDIP((32, 32))

        for day in range(1, max_day + 1):
            btn = wx.Button(self.panel, label=str(day), size=size)

            # Set today to a different color.
            if (day == today.day and self.bdate.month == today.month
                and self.bdate.year == today.year):
                btn.SetBackgroundColour(wx.Colour(230, 240, 255))
                btn.SetForegroundColour(wx.Colour(0, 70, 160))
            else:
                btn.SetForegroundColour(wx.Colour(0, 0, 0))
                btn.SetBackgroundColour(wx.Colour(180, 180, 180))

            btn.SetWindowStyle(wx.BORDER_NONE | wx.BU_EXACTFIT)
            btn.Bind(wx.EVT_BUTTON, self._on_day_clicked)
            btn.day = day
            self.grid_sizer.Add(btn, 0, wx.ALL, self.FromDIP(2))

    def update_header(self):
        label = ordered_month()[self.bdate.month]
        self.header.SetLabel(f"{label} {self.bdate.year}")
        self.header.Wrap(self.FromDIP(150))  # Prevent clipping if name is long
        self._populate_days()
        self.Layout()
        self.panel.Layout()
        self.Fit()

    def _max_days_in_month(self, year, month):
        return 4 + self.bdate._is_leap_year(year) if month == 0 else 19

    def _on_day_clicked(self, event):
        day = event.GetEventObject().day
        new_date = badidatetime.date(self.bdate.year, self.bdate.month, day)

        if self.on_date_selected:
            self.on_date_selected(new_date)

        self.Dismiss()

    def on_prev_year(self, event):
        self.bdate = badidatetime.date(self.bdate.year - 1,
                                       self.bdate.month, 1)
        self.update_header()

    def on_next_year(self, event):
        self.bdate = badidatetime.date(self.bdate.year + 1,
                                       self.bdate.month, 1)
        self.update_header()

    MONTH_ORDER = list(ordered_month().keys())  # [1..18, 0, 19]

    def _shift_month(self, direction):
        idx = self.MONTH_ORDER.index(self.bdate.month)
        new_idx = (idx + direction) % len(self.MONTH_ORDER)
        new_month = self.MONTH_ORDER[new_idx]
        year = self.bdate.year

        if direction == 1 and self.bdate.month == 19:
            year += 1
        elif direction == -1 and self.bdate.month == 1:
            year -= 1

        self.bdate = badidatetime.date(year, new_month, 1)
        self.update_header()

    def on_prev_month(self, event):
        self._shift_month(-1)

    def on_next_month(self, event):
        self._shift_month(1)


class BadiDatePickerCtrl(wx.Panel):
    """
    Customized Badí' date widget.
    """
    _DATE_RANGES = {0: (1, 4), 1: (2, 2), 2: (2, 2)}

    def __init__(self, parent: wx.Window, id: int=wx.ID_ANY,
                 dt: badidatetime.date=None, pos=wx.DefaultPosition,
                 style=wx.adv.DP_DEFAULT | wx.adv.DP_SHOWCENTURY,
                 validator=wx.DefaultValidator, name: str="") -> None:
        super().__init__(parent)
        self.SetName(name)
        w_bg_color = wx.Colour(222, 237, 230)  # Gray
        # Default date
        self.bdate = dt or badidatetime.date.today(short=True)

        self.text_ctrl = CustomTextCtrl(self, style=wx.BORDER_NONE)
        #self.text_ctrl = wx.TextCtrl(self, style=wx.BORDER_NONE)
        self.text_ctrl.SetValue(self.bdate.isoformat())
        self.text_ctrl.SetBackgroundColour(w_bg_color)
        self.text_ctrl.SetForegroundColour(wx.BLACK)
        self.text_ctrl.Bind(wx.EVT_TEXT, self.on_change)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_BUTTON, (16, 16))
        self.calendar_btn = wx.BitmapButton(self, bitmap=bmp,
                                            style=wx.BU_AUTODRAW)
        self.calendar_btn.Bind(wx.EVT_BUTTON, self.show_popup_calendar)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 2)
        self.text_ctrl.SetMinSize((90, -1))  # Set the minimum size
        self.SetMinSize((1, 28))
        sizer.AddStretchSpacer()
        sizer.Add(self.calendar_btn, 1, wx.EXPAND | wx.ALL, 2)

        self.SetSizer(sizer)

    def _max_days_in_month(self, year, month):
        return 4 + self.bdate._is_leap_year(year) if month == 0 else 19

    def on_change(self, event):
        text = self.text_ctrl.GetValue()
        parts = re.split(r'[-/.]', text)
        res = [self._DATE_RANGES[i][0] <= len(p) <= self._DATE_RANGES[i][1]
               for i, p in enumerate(parts)]

        if len(parts) == 3 and all(res):
            date = [int(p) for p in parts]
            self.bdate = badidatetime.date(*date)
            wx.PostEvent(self, BadiDateChangedEvent(self, self.bdate))

    def show_popup_calendar(self, event):
        popup = BadiCalendarPopup(self, bdate=self.bdate)
        popup.on_date_selected = self._on_popup_date_selected
        btn_pos = self.ClientToScreen(self.calendar_btn.GetPosition())
        btn_size = self.calendar_btn.GetSize()
        popup.Position(btn_pos, (0, btn_size.height))
        popup.Popup()

    def _on_popup_date_selected(self, new_bdate):
        self.SetValue(new_bdate)
        wx.PostEvent(self, BadiDateChangedEvent(self, new_bdate))

    def GetValue(self):
        return self.bdate

    def SetValue(self, bdate: badidatetime.date):
        self.bdate = bdate
        self.text_ctrl.SetValue(bdate.isoformat())


# Custom event
wxEVT_COLOR_CHECKBOX = wx.NewEventType()
EVT_COLOR_CHECKBOX = wx.PyEventBinder(wxEVT_COLOR_CHECKBOX, 1)


class ColorCheckBoxEvent(wx.PyCommandEvent):
    def __init__(self, source, state):
        super().__init__(wxEVT_COLOR_CHECKBOX, source.GetId())
        self._state = state

    def GetColorCheckBoxState(self):
        return self._state


class ColorCheckBox(wx.Panel):
    """
    A custom checkbox.

    .. note::

       1. If the panel is bigger that the chekbox itself then
          SetBackgroundColour() and SetForegroundColour() will affect
          their color.
       2. The forground color of the checkbox itself is affected by
          SetForegroundColour(), but the background color defaults to white
          unless a different color is passed to the constructor argument
          cb_color.
       3. The border of the chekbox itself defaults to Black
    """
    def __init__(self, parent: wx.Window, id: int=wx.ID_ANY, label: str="",
                 name: str="", label_position="right", checked: bool=False,
                 bb_color=wx.BLACK, cb_color=wx.WHITE,
                 check_color=wx.Colour(0, 120, 215),  # Dark Blue
                 disabled_color=wx.Colour(160, 160, 160)):  # Gray
        super().__init__(parent)
        self.checked = checked
        self.enabled = True
        self.read_only = False
        self.label = label
        self.label_position = label_position  # 'right' (default) or 'left'
        self.SetName(name)
        self.bb_color = bb_color  # Box border color
        self.cb_color = cb_color
        self.check_color = check_color
        self.disabled_color = disabled_color

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.SetSize()

    def OnClick(self, event):
        if self.enabled:
            self.checked = not self.checked
            self.Refresh()
            evt = wx.CommandEvent(EVT_COLOR_CHECKBOX.typeId, self.GetId())
            evt.SetEventObject(self)
            evt.SetInt(int(self.checked))
            wx.PostEvent(self, evt)

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.Clear()

        size = self.GetSize()
        box_size = min(size.height, 16)  # 16 is max box size.
        margin = 6

        # Get label size
        text_width, text_height = dc.GetTextExtent(self.label)

        if self.label_position == "left":
            text_x = 0
            box_x = text_width + margin
        else:
            box_x = 0
            text_x = box_size + margin

        box_y = (size.height - box_size) // 2
        text_y = (size.height - text_height) // 2

        # Background based on enabled state
        bg_color = self.GetBackgroundColour()
        fg_color = (self.GetForegroundColour() if self.enabled
                    else wx.Colour(120, 120, 120))
        box_border_color = (self.bb_color if self.enabled
                            else self.disabled_color)

        dc.SetBrush(wx.Brush(bg_color))
        dc.SetPen(wx.Pen(bg_color))
        dc.DrawRectangle(0, 0, size.width, size.height)

        # Checkbox box
        dc.SetBrush(wx.Brush(
            self.cb_color if self.enabled else wx.Colour(230, 230, 230)))
        dc.SetPen(wx.Pen(box_border_color))
        dc.DrawRectangle(box_x, box_y, box_size, box_size)

        # Check mark
        if self.checked:
            dc.SetPen(wx.Pen(fg_color, 2))
            dc.DrawLine(box_x + 3,
                        box_y + box_size // 2,
                        box_x + box_size // 3,
                        box_y + box_size - 3)
            dc.DrawLine(box_x + box_size // 3,
                        box_y + box_size - 3,
                        box_x + box_size - 3,
                        box_y + 3)

        # Draw label
        dc.SetTextForeground(fg_color)
        dc.DrawText(self.label, text_x, text_y)

    def GetValue(self):
        return self.checked

    def SetValue(self, value: bool):
        if not self.read_only:
            self.checked = bool(value)
            self.Refresh()

    def SetReadOnly(self, value=True):
        self.read_only = value
        self.Enable(False)

    def IsEditable(self):
        return not self.read_only

    def Enable(self, enable: bool=True):
        self.enabled = enable
        self.Refresh()

    def IsEnabled(self):
        return self.enabled

    def SetSize(self, size=(120, 24)):
        self.SetMinSize(size)
