# -*- coding: utf-8 -*-
#
# src/bases.py
#
__docformat__ = "restructuredtext en"

import os
import re
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .utilities import StoreObjects


def find_dict(value: list) -> dict:
    """
    Fine the dict in the Toml data that is in the widget value list.

    :param value: A list that defines a widget from a TOML file.
    :type value: list
    :return: A dict with attributes that define a widget.
    :rtype: dict
    """
    for item in value:
        if isinstance(item, dict):
            break
        else:
            item = {}

    return item


def version() -> str:
    """
    Opens the 'include.mk' file and reads the version information. If the
    `PR_TAG` environment variable exists the pre-release candidate is added.

    :return: A formatted version number.
    :rtype: str
    """
    from .config import Settings
    regex = r'(?m)(^{}[\s]*=[\s]*(?P<ver>\d*)$)'

    with open(os.path.join(Settings.base_dir(), 'include.mk')) as f:
        ver = f.read()

    major = re.search(regex.format('MAJORVERSION'), ver).group('ver')
    minor = re.search(regex.format('MINORVERSION'), ver).group('ver')
    patch = re.search(regex.format('PATCHLEVEL'), ver).group('ver')
    # Look for a tag indicating a pre-release candidate. ex. rc1
    env_value = os.environ.get('PR_TAG', '')
    return f"{major}.{minor}.{patch}{env_value}"


class BasePanel:
    """
    This base class is used in the FieldEdit class in Tools and in the
    panels created by the PanelFactory.
    """
    def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
        super().__init__(parent, id=id, *args, **kwargs)
        self._dirty = False
        self._save = False
        self._cancel = False
        self._initializing = False
        self._selected = False

    @property
    def background_color(self) -> list:
        return self._bg_color

    def _find_dict(self, value):
        return find_dict(value)

    def set_dirty_flag(self, event):
        """
        Set a dirty flag when any editable widget is modified except when
        initializing widgets.
        """
        if hasattr(self, 'get_selection'):
            sel = self.selected
        else:
            sel = True

        if not self.initializing and sel:
            self.dirty = True

        event.Skip()

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    @property
    def initializing(self):
        return self._initializing

    @initializing.setter
    def initializing(self, value):
        self._initializing = value

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value


class BaseGenerated(BasePanel, ScrolledPanel):

    def __init__(self, parent, id=wx.ID_ANY, *args, **kwargs):
        super().__init__(parent, id=id, *args, **kwargs)
        kwargs["style"] = kwargs.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        super().__init__(parent, id=id, **kwargs)
        self.parent = parent
        self.frame = parent.GetParent()
        self._mf = StoreObjects().get_object('MainFrame')

    def locality_prefix(self, update, dirty_flag):
        """
        This is a closure for the 'do_event' callback.

        :param wx.Window update: The widget that is being updated.
        """
        def do_event(event):
            """
            This event callback updates the locality prefix TextCtrl and
            setting the dirty flag.

            :param event: This is a wx event.
            :type event: wx.Event
            """
            rb = event.GetEventObject()
            self._locality_prefix(rb, update)
            self.dirty = dirty_flag

        return do_event

    def _locality_prefix(self, rb, update):
        """
        Set value in the widget used for the community type. This method
        is used only when the Baha'i config file is used.

        :param wx.RadioButton rb: A RadioButton widget object.
        :param wx.Window update: The widget that is being updated.
        """
        selection = rb.GetStringSelection()
        text = self.locale_prefix[selection.lower()]
        prefix_widget = getattr(self, update)
        prefix_widget.SetValue(text)
