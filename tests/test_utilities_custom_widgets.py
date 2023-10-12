#!/usr/bin/env python
#
# Test custom widgets.
#

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import wx

from src.utilities import EventStaticText


class _TestFrame(wx.Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Create the sizer objects.
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        gbs = wx.GridBagSizer()
        sizer.Add(gbs, 0, wx.CENTER | wx.ALL, 6)

        widget1 = EventStaticText(self, wx.ID_ANY, "Widget 1")
        gbs.Add(widget1, (0, 0), (1, 1), wx.ALIGN_CENTER | wx.ALL, 6)
        self.Bind(widget1.EVT_CLICK_POSITION, self.test_event,
                  id=widget1.GetId())
        e_type_1 = widget1.new_event_type
        print(f"widget1 event type: {e_type_1}")

        widget2 = EventStaticText(self, wx.ID_ANY, "Widget 2")
        gbs.Add(widget2, (1, 0), (1, 1), wx.ALIGN_CENTER | wx.ALL, 6)
        self.Bind(widget2.EVT_CLICK_POSITION, self.test_event,
                  id=widget2.GetId())
        e_type_2 = widget2.new_event_type
        print(f"widget2 event type: {e_type_2}")

        widget3 = EventStaticText(self, wx.ID_ANY, "Widget 3")
        sizer.Add(widget3, 0, wx.CENTER | wx.ALL, 6)
        self.Bind(widget3.EVT_CLICK_POSITION, self.test_event,
                  id=widget3.GetId())
        e_type_3 = widget3.new_event_type
        print(f"widget3 event type: {e_type_3}")

        self.Show()
        assert e_type_1 == e_type_2, ("Both widgets must have the same number "
                                      f"found (e_type_1): {e_type_1} and "
                                      f"found (e_type_2): {e_type_2}")

    def test_event(self, event):
        print(f"Value: {event.get_value()}")


if __name__ == "__main__":
    app = wx.App()
    frame = _TestFrame(None, title="Test new widgets.")
    app.MainLoop()
