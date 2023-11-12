# -*- coding: utf-8 -*-
#
# src/utilities.py
#
__docformat__ = "restructuredtext en"

import wx


class GridBagSizer(wx.GridBagSizer):

    def swap_rows(self, row0, row1):
        """
        Swap any two rows in a GridBagSizer keeping most parameters.

        Some code here contributed by:
          Georg Klingenberg @ https://discuss.wxpython.org/u/da-dada
        """
        rows = self.GetRows()
        cols = self.GetCols()
        assert row0 != row1, (f"row0 ({row0}) and row1 ({row1}) cannot "
                              "be the same.")
        assert -1 < row0 < rows, ("The row0 value is invalid can only be "
                                  f"between 0 and {rows-1}, found {row0}")
        assert -1 < row1 < rows, ("The row1 value is invalid can only be "
                                  f"between 0 and {rows-1}, found {row1}")
        assert -1 < cols, f"The number of columns must be >= 0, found {cols}."
        w0 = []
        w1 = []

        # Save all widgets in row0 to w0 and all widgets in row1 to w1.
        # The row0 widgets also have a few attributes saved.
        for idx, item in enumerate(self.GetChildren()):
            if (y := item.GetPos()[0]) == row0:
                w = item.GetWindow()
                w0.append((w, item.GetPos(), item.GetSpan(),
                           item.GetFlag(), item.GetBorder(), idx))
            elif y == row1:
                w1.append(item.GetWindow())

        # Remove only row0 widgets from the GridBagSizer.
        [self.Remove(w_list[5]) for w_list in reversed(w0)]

        # Reposition all row1 widgets in the row0 positions.
        for w in w1:
            pos = self.GetItemPosition(w)
            pos.SetRow(row0)
            self.SetItemPosition(w, pos)

        # Re-add all the original row0 widgets in the row1 positions.
        for w_list in w0:
            w_list[1].SetRow(row1)
            self.Add(w_list[0], w_list[1], w_list[2],
                     flag=w_list[3], border=w_list[4])

    def highlight_row(self, row, color):
        if row is not None:
            for item in self.GetChildren():
                if item.GetPos()[0] == row:
                    w = item.GetWindow()
                    w.SetBackgroundColour(color)
                    w.Refresh()


class ConfirmationDialog(wx.Dialog):
    """
    Create a generic dialog box.
    """

    def __init__(self, parent, msg, cap, bg_color=(220, 130, 143), # Red-ish
                 fg_color=None):
        super().__init__(parent, wx.ID_ANY, cap,
                         style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self._parent = parent
        self.SetSize((300, 150))

        self._bg_color = bg_color
        self._fg_color = fg_color
        if bg_color: self.SetBackgroundColour(wx.Colour(*bg_color))

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        message = wx.StaticText(self, wx.ID_ANY, msg)
        if fg_color: message.SetForegroundColour(wx.Colour(*fg_color))
        message.Wrap(300)
        sizer.Add(message, 0, wx.ALL | wx.CENTER, 10)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)

        button_sizer = wx.StdDialogButtonSizer()
        sizer.Add(button_sizer, 0, wx.CENTER | wx.ALL, 6)

        ok_button = wx.Button(self, wx.ID_OK)
        #ok_button.SetDefault()
        button_sizer.AddButton(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL)
        cancel_button.SetDefault()
        button_sizer.AddButton(cancel_button)

        button_sizer.Realize()
        sizer.Fit(self)

    def show(self):
        self.CenterOnParent()
        value = self.ShowModal()

        if value == wx.ID_OK:
            ret = True
        else:
            ret = False

        self.Destroy()
        return ret


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
