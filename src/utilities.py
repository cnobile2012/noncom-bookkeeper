# -*- coding: utf-8 -*-
#
# src/utilities.py
#
__docformat__ = "restructuredtext en"

from collections import OrderedDict
from itertools import chain
import wx


class GBSRowSwapping:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def gbs_swap_rows(self, gbs, row0, row1):
        """
        Swap any two rows in a GridBagSizer keeping most parameters.
        """
        rows = gbs.GetRows()
        cols = gbs.GetCols()
        assert row0 != row1, (f"row0 ({row0}) and row1 ({row1}) cannot "
                              "be the same.")
        assert -1 < row0 < rows, ("The row0 value is invalid can only be "
                                  f"between 0 and {rows-1}, found {row0}")
        assert -1 < row1 < rows, ("The row1 value is invalid can only be "
                                  f"between 0 and {rows-1}, found {row1}")
        assert -1 < cols, f"The number of columns must be >= 0, found {cols}."
        # Get GBS positions.
        positions = [[(r, c) for c in range(cols)] for r in (row0, row1)]
        # Remove the GBSizerItem in both rows.
        sizer_items = []

        for idx, row in enumerate(positions):
            sizer_items.append(OrderedDict())

            for rc in row:
                sizer_items[idx][gbs.FindItemAtPosition(rc)] = None

        sizer_items = [[item for item in row.keys()] for row in sizer_items]
        # Get list of windows (widgets).
        windows = [[(item.GetWindow(), item.GetSpan(),
                     item.GetFlag(), item.GetBorder())
                    for item in row if item] for row in sizer_items]
        # Remove GBSizerItem in both rows.
        [gbs.Remove(self.get_sizer_item_index(gbs, item))
         for item in list(chain(*sizer_items)) if item]
        # Add the widget objects to the GridBagSizer with swapped positions.
        [[gbs.Add(item[0], rpos[idx], item[1], flag=item[2], border=item[3])
          for idx, item in enumerate(windows[row])]
         for row, rpos in enumerate(reversed(positions))]

    def get_sizer_item_index(self, sizer, item):
        """
        Determines the index of an item in a sizer.

        :params sizer: The sizer to search.
        :type sizer: wx.Sizer
        :param item: The item to find.
        :type item: wx.SizerItem
        :returns: The index of the item in the sizer, or -1 if the item
                  is not in the sizer.
        :rtype: int
        """
        index = -1

        for idx, child in enumerate(sizer.GetChildren()):
            if child == item:
                index = idx
                break

        return index

    def highlight_row(self, gbs, row, color=None):
        if row is not None and color:
            positions = [(row, c) for c in range(gbs.GetCols())]

            for w in [gbs.FindItemAtPosition(pos).GetWindow()
                      for pos in positions if gbs.FindItemAtPosition(pos)]:
                w.SetBackgroundColour(color)
                w.Refresh()


class _ClickPosition:
    """
    A borg pattern to hold new widget type IDs.
    """
    _shared_state = {}
    _new_types = {}

    def __init__(self):
        self.__dict__ = self._shared_state

    def get_new_event_type(self, w_name):
        return self._new_types.setdefault(w_name, wx.NewEventType())

    def get_click_position(self, w_name):
        assert w_name in self._new_types, ("The 'get_new_event_type' must "
                                           "be called first.")
        return wx.PyEventBinder(self._new_types[w_name], 1)


class WidgetEvent(wx.PyCommandEvent):
    """
    For some reason wx.PyCommandEvent screws up the use of properties,
    bummer.
    """

    def __init__(self, evt_type, id):
        super().__init__(evt_type, id)
        self.__value = None
        self.__window = None

    def get_value(self):
        return self.__value

    def set_value(self, value):
        self.__value = value

    def get_window(self):
        return self.__window

    def set_window(self, win):
        self.__window = win


class EventStaticText(wx.StaticText):
    __type_name = 'event_static_text'
    _cp = _ClickPosition()
    _type_id = _cp.get_new_event_type(__type_name)

    def __init__(self, parent=None, id=wx.ID_ANY, label="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, name=wx.StaticTextNameStr):
        super().__init__(parent=parent, id=id, label=label, pos=pos,
                         size=size, style=style, name=name)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

    @property
    def new_event_type(self):
        return self._cp.get_new_event_type(self.__type_name)

    @property
    def EVT_CLICK_POSITION(self):
        return self._cp.get_click_position(self.__type_name)

    def on_left_down(self, event):
        obj = event.GetEventObject()
        sizer = obj.GetContainingSizer()
        pos = None

        if isinstance(sizer, wx.GridBagSizer):
            item = sizer.FindItem(obj)
            pos = item.GetPos()
        elif isinstance(sizer, wx.BoxSizer):
            item = sizer.GetItem(obj)
            pos = item.GetPosition()

        evt = WidgetEvent(self._type_id, self.GetId())
        evt.set_value(pos)
        evt.set_window(obj)
        self.GetEventHandler().ProcessEvent(evt)
        event.Skip()
