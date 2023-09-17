# -*- coding: utf-8 -*-
#
# src/bases.py
#
__docformat__ = "restructuredtext en"

import wx
from wx.lib.scrolledpanel import ScrolledPanel


class BasePanel:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def background_color(self):
        return self._bg_color

    def _setup_sizer_height_correctly(self, sizer):
        """
        Add the height of the status bar to the GridBagSizer height
        so that the call to SetupScrolling creates the correct virtual
        window size.
        """
        width, height = sizer.GetMinSize()
        height += self.parent.statusbar_size[1]
        sizer.SetMinSize((width, height))


class BaseGenerated(BasePanel, ScrolledPanel):

    def __init__(self, parent, id=wx.ID_ANY, **kwargs):
        kwargs["style"] = kwargs.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        super().__init__(parent, id=id, **kwargs)
        self.parent = parent

    def locality_prefix(self, update):
        def do_event(event):
            rb = event.GetEventObject()
            self._locality_prefix(rb, update)

        return do_event

    def _locality_prefix(self, rb, update):
        selection = rb.GetStringSelection()
        text = self.locale_prefix[selection.lower()]
        prefix_widget = getattr(self, update)
        prefix_widget.SetValue(text)
