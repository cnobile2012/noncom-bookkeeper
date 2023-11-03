# -*- coding: utf-8 -*-
#
# test/fixtures.py
#
__docformat__ = "restructuredtext en"


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
