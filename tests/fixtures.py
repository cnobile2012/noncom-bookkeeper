# -*- coding: utf-8 -*-
#
# test/fixtures.py
#
__docformat__ = "restructuredtext en"

import wx

from src.bases import BaseGenerated
from src.custom_widgits import (
    ColorCheckBox, EVT_COLOR_CHECKBOX)

__all__ = ('FakeFrame', 'FakeWidget', 'FakeEvent', 'FakePanel')


class FakeFrame(wx.Frame):

    def __init__(self, parent=None, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL, *args,
                 **kwargs):
        super().__init__(parent, id=id, pos=pos, style=style, *args, **kwargs)


class FakeWidget:

    def __init__(self, selection='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selection = selection
        self._value = ""

    @property
    def value(self):
        return self._value

    def SetValue(self, value):
        self._value = value

    def GetStringSelection(self):
        return self._selection


class FakeEvent:

    def __init__(self, event_object=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_object = event_object

    def GetEventObject(self):
        return self.event_object


class FakePanel(BaseGenerated):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        sizer = wx.BoxSizer(wx.VERTICAL)
        widget_00 = ColorCheckBox(self, wx.ID_ANY, label='', name='current')
        widget_00.SetBackgroundColour(wx.Colour(*[210, 190, 255]))
        widget_00.SetForegroundColour(wx.Colour(*[50, 50, 204]))
        widget_00.SetMinSize([80, 20])
        widget_00.Bind(EVT_COLOR_CHECKBOX, self.set_dirty_flag)
        widget_00.Enable(False)
        sizer.Add(widget_00, 0, wx.CENTER, 6)

    def _on_popup_date_selected(self, new_bdate):
        self.SetValue(new_bdate)
        wx.PostEvent(self, BadiDateChangedEvent(self, new_bdate))
