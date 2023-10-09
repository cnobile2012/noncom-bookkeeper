# -*- coding: utf-8 -*-
#
# src/bases.py
#
__docformat__ = "restructuredtext en"

import wx
from wx.lib.scrolledpanel import ScrolledPanel



def find_dict(value):
    """
    Fine the dict in the Toml data that is in the widget value list.
    """
    for item in value:
        if isinstance(item, dict):
            break
        else:
            item = {}

    return item


class BasePanel:
    """
    This base class is used in the FieldEdit class in Tools and the
    panels created by the PanelFactory.
    """

    @property
    def background_color(self):
        return self._bg_color

    def _setup_sizer_height_correctly(self, sizer, swidth=None):
        """
        Add the height of the status bar to the Sizer height so that the
        call to SetupScrolling creates the correct virtual window size.
        """
        width, height = sizer.GetMinSize()
        width = swidth if swidth else width
        height += self.parent.statusbar_size[1]
        sizer.SetMinSize((width, height))

    def _find_dict(self, value):
        return find_dict(value)


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
