# -*- coding: utf-8 -*-
#
# test/fixtures.py
#
__docformat__ = "restructuredtext en"

import os
import wx

from src.bases import BaseGenerated
from src.custom_widgits import (
    ColorCheckBox, EVT_COLOR_CHECKBOX)
from src.config import Settings, TomlPanelConfig, TomlAppConfig
from src.panel_factory import PanelFactory

__all__ = ('FakeFrame', 'FakeMainFrame', 'FakeWidget', 'FakeEvent',
           'FakePanel')


class FakeMainFrame:

    def __init__(self, options=None, *args, **kwargs):
        settings = Settings()
        settings.testing = True
        settings.create_dirs()
        tpc = TomlPanelConfig()
        tpc.is_valid
        self.tac = TomlAppConfig()
        self.tac.is_valid
        super().__init__(*args, **kwargs)
        sf = PanelFactory()
        sf.parse()

        for panel in sf.class_name_keys:
            code = sf.get_panel_code(panel)

            if code:
                # Only used for debugging.
                if options.file_dump:  # Write the code files to the cache.
                    filename = f"{panel}.py"
                    dir = self.tac.cached_factory_dir
                    pathname = os.path.join(dir, filename)

                    with open(pathname, 'w') as f:
                        f.write(code)

                # Create the panels.
                exec(code, globals())
                class_name = sf.get_class_name(panel)
                self.__panel_classes[panel] = globals(
                    )[class_name](self, *args, **kwargs)


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
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        widget_00 = ColorCheckBox(self, wx.ID_ANY, label='', name='current')
        widget_00.SetBackgroundColour(wx.Colour(*[210, 190, 255]))
        widget_00.SetForegroundColour(wx.Colour(*[50, 50, 204]))
        widget_00.SetMinSize([80, 20])
        widget_00.Bind(EVT_COLOR_CHECKBOX, self.set_dirty_flag)
        widget_00.Enable(False)
        self.sizer.Add(widget_00, 0, wx.CENTER | wx.ALL, 10)

    def _on_popup_date_selected(self, new_bdate):
        self.SetValue(new_bdate)
        wx.PostEvent(self, BadiDateChangedEvent(new_bdate))
