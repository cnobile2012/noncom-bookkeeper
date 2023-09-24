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
        Add the height of the status bar to the Sizer height so that the
        call to SetupScrolling creates the correct virtual window size.
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


class BaseSwap(BasePanel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def gbs_swap_rows(self, gbs, row0, row1, flags=0):
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
        positions = []
        old_sizer_items = []
        windows = []

        # Find and store the GBSizerItem objects.
        for idx, r in enumerate((row0, row1)):
            old_sizer_items.append([])
            positions.append([])

            for c in range(cols):
                positions[idx].append((r, c))
                old_sizer_items[idx].append(gbs.FindItemAtPosition((r, c)))

        # Remove GBSizerItem in both rows.
        for idx, row in enumerate(old_sizer_items):
            windows.append([])

            for item in row:
                if item:
                    windows[idx].append([item.GetWindow(), item.GetSpan()])
                    gbs.Remove(self.get_sizer_item_index(gbs, item))

        # Add the new GBSizerItem objects into the GridBagSizer.
        for row, rpos in enumerate(reversed(positions)):
            for idx, item in enumerate(windows[row]):
                gbs.Add(item[0], rpos[idx], item[1], flags=flags)
