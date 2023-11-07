# -*- coding: utf-8 -*-
#
# test/fixtures.py
#
__docformat__ = "restructuredtext en"


## def _constructor_decorator(cls, **kwgs):
##     orig_init = cls.__init__

##     def new_init(self, *args, **kwargs):
##         orig_init(self, *args, **kwargs)

##         for key, value in kwgs.items():
##             setattr(self, key, eval(value)())

##     cls.__init__ = new_init
##     return cls


## def _method_closurer(orig_method, **kwgs):
##     def add_decorator_closure(func):
##         def add_decorator(self, *args, **kwargs):
##             result = func(self, *args, **kwargs)

##             for key, value in kwgs.items():
##                 print(value)
##                 setattr(self, key, eval(value)())

##             return result

##     decorated_method = add_decorator_closure(orig_method)
##     return decorated_method


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
