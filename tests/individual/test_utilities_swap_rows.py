#!/usr/bin/env python
#
# Test GridBagSizer row swapping.
#

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

import wx

from src.utilities import GridBagSizer, EventStaticText


class MyFrame(wx.Frame):
    __previous_row = None
    __cl = None

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Create the sizer objects.
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        bg_color = wx.Colour(*(128, 128, 128))
        self.SetBackgroundColour(bg_color)

        button = wx.SpinCtrl(self, wx.ID_ANY, "")
        button.SetBackgroundColour(bg_color)
        sizer.Add(button, 0, wx.CENTER | wx.ALL, 0)

        grid_bag_sizer = GridBagSizer()
        sizer.Add(grid_bag_sizer, 0, wx.CENTER | wx.ALL, 6)
        self.Bind(wx.EVT_SPINCTRL,
                  self.swap_rows_closure(grid_bag_sizer, bg_color))

        # Add the widgets to the GridBagSizer.
        self.create_widgets(grid_bag_sizer, button, bg_color)
        button.SetRange(0, grid_bag_sizer.GetRows()-1)

        self.Show()

    def create_widgets(self, gbs, sb, bg_color):
        widget = EventStaticText(self, -1, "Two column wide text (move me).",
                                 style=0)
        widget.SetBackgroundColour(bg_color)
        gbs.Add(widget, (0, 0), (1, 2), wx.ALL, 6)
        self.Bind(widget.EVT_CLICK_POSITION,
                  self.event_click_closure(gbs, sb, bg_color),
                  id=widget.GetId())
        num_widgets = 13
        num = 0

        for idx in range(num_widgets):
            dec = idx % 3
            if not dec: num += 1
            label = f"Widget {num}.{dec}"
            widget = EventStaticText(self, -1, label, style=0)
            widget.SetBackgroundColour(bg_color)
            pos, span = (num, dec), (1, 1)
            gbs.Add(widget, pos, span, wx.ALIGN_CENTER | wx.ALL, 6)
            self.Bind(widget.EVT_CLICK_POSITION,
                      self.event_click_closure(gbs, sb, bg_color),
                      id=widget.GetId())

    def swap_rows_closure(self, gbs, orig_color):
        """
        Event to swap the two rows.
        """
        def swap_rows(event):
            if self.__previous_row is not None:
                row0 = self.__previous_row
                obj = event.GetEventObject()
                row1 = obj.GetValue()
                self.__previous_row = row1

                if row0 != row1:
                    self.stop_call_later()
                    gbs.swap_rows(row0, row1)
                    self.Layout()
                    self.__cl = wx.CallLater(4000, self.turn_off_highlight,
                                             gbs, orig_color)

        return swap_rows

    def event_click_closure(self, gbs, sb, orig_color=None, color='lightblue'):
        """
        Event to highlight the GBS row when a widget is clicked.
        """
        def event_click(event):
            self.stop_call_later()
            pos = event.get_value()
            row, col = pos
            gbs.highlight_row(self.__previous_row, orig_color)
            gbs.highlight_row(row, color)
            self.__previous_row = row
            sb.SetValue(row)
            self.__cl = wx.CallLater(4000, self.turn_off_highlight,
                                     gbs, orig_color)

        return event_click

    def turn_off_highlight(self, gbs, orig_color):
        for row in range(gbs.GetRows()):
            self.__previous_row = None
            gbs.highlight_row(row, orig_color)
            self.Layout()

    def stop_call_later(self):
        if self.__cl and self.__cl.IsRunning():
            self.__cl.Stop()
            self.__cl = None


if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None, title="Swap Widgets in a GridBagSizer")
    app.MainLoop()
