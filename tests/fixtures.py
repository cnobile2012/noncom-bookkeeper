# -*- coding: utf-8 -*-
#
# test/fixtures.py
#
__docformat__ = "restructuredtext en"

import wx


class FakeFrame(wx.Frame):

    def __init__(self, parent=None, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL, **kwargs):
        super().__init__(parent, id=id, pos=pos, style=style)


class FakeWidget:

    def __init__(self, selection=''):
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

    def __init__(self, event_object=None):
        self.event_object = event_object

    def GetEventObject(self):
        return self.event_object
