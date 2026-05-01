# -*- coding: utf-8 -*-
#
# src/utilities.py
#
__docformat__ = "restructuredtext en"

import re
import wx
import asyncio
import threading

from collections import OrderedDict

from .custom_widgits import ColorCheckBox, EVT_COLOR_CHECKBOX


def make_name(name: str):
    name = re.sub(r"[&*\(\):\"'/\\]+", '', name)
    name = re.sub(r"[- \s]+", '_', name).strip('_')
    return re.sub(r"_+", "_", name).lower()


class Borg:
    """
    We have Central state + synchronized instance views + class fallback. This
    allows the updating of future instances with the data from the previous
    instances. Without this, new instances would not have all the data.
    _state        → source of truth
    __dict__      → cached mirror for each instance
    class attrs   → defaults
    """
    _state = {}
    _instances = []
    _lock = threading.RLock()

    @classmethod
    def _root(cls):
        # Find the class that actually defines _state
        for base in cls.__mro__:
            if '_state' in base.__dict__:
                return base

        return cls

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        root = cls._root()

        with root._lock:
            root._instances.append(instance)

            # ALWAYS hydrate from state
            for k, v in root._state.items():
                instance.__dict__[k] = v

        return instance

    def __getattribute__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)

        cls = type(self)
        root = cls._root()

        with root._lock:
            if name in root._state:
                return root._state[name]

        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        cls = type(self)
        root = cls._root()

        # Protect real internals only
        if name in {'_state', '_instances', '_lock'} or name.startswith('__'):
            object.__setattr__(self, name, value)
            return

        # Let descriptors (properties) handle themselves FIRST
        attr = getattr(cls, name, None)

        if hasattr(attr, '__set__'):
            attr.__set__(self, value)
            return

        with root._lock:
            root._state[name] = value

            for inst in root._instances:
                inst.__dict__[name] = value

    def clear_state(self):
        cls = type(self)
        root = cls._root()

        with root._lock:
            root._state.clear()

            for inst in root._instances:
                keys = [k for k in inst.__dict__ if not k.startswith('_')]
                for k in keys:
                    del inst.__dict__[k]

            root._instances.clear()


class StoreObjects(Borg):
    _object_store = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_object(self, key, value):
        self._object_store[key] = value

    def get_object(self, key):
        return self._object_store.get(key)


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

    def __init__(self, parent, msg, cap, *, bg_color=None, fg_color=None):
        super().__init__(parent, wx.ID_ANY, cap,
                         style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self._parent = parent
        self.SetSize((300, 150))

        self._bg_color = bg_color if bg_color else (220, 130, 143)  # Red-ish
        self._fg_color = fg_color if fg_color else (50, 50, 204)    # Blue-ish
        self.SetBackgroundColour(wx.Colour(*self._bg_color))

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        message = wx.StaticText(self, wx.ID_ANY, msg)
        message.SetBackgroundColour(wx.Colour(*self._bg_color))
        message.SetForegroundColour(wx.Colour(*self._fg_color))
        message.Wrap(300)
        sizer.Add(message, 0, wx.ALL | wx.CENTER, 10)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)

        button_sizer = wx.StdDialogButtonSizer()
        sizer.Add(button_sizer, 0, wx.CENTER | wx.ALL, 6)

        ok_button = wx.Button(self, wx.ID_OK)
        button_sizer.AddButton(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL)
        cancel_button.SetDefault()
        button_sizer.AddButton(cancel_button)

        button_sizer.Realize()
        sizer.Fit(self)

    def show(self):  # pragma: no cover
        self.CenterOnParent()
        value = self.ShowModal()

        if value == wx.ID_OK:
            ret = True
        else:
            ret = False

        self.Destroy()
        return ret


class _ClickPosition(Borg):
    """
    A borg pattern to hold new widget type IDs.
    """

    def __init__(self, *args, **kwargs):
        self._new_types = {}

    def get_new_event_type(self, w_name):
        return self._new_types.setdefault(w_name, wx.NewEventType())

    def get_click_position(self, w_name):
        assert w_name in self._new_types, (
            "The 'get_new_event_type' method must be called first.")
        return wx.PyEventBinder(self._new_types[w_name], 1)


class WidgetEvent(wx.PyCommandEvent):
    """
    For some reason wx.PyCommandEvent screws up the use of properties,
    bummer so I needed to use actual getter and setter methods.
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

    def __init__(self, parent=None, id=wx.ID_ANY, label="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, name=wx.StaticTextNameStr):
        super().__init__(parent=parent, id=id, label=label, pos=pos,
                         size=size, style=style, name=name)
        self._cp = _ClickPosition()
        self._type_id = self._cp.get_new_event_type(self.__type_name)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

    @property
    def new_event_type(self):
        return self._cp.get_new_event_type(self.__type_name)

    @property
    def EVT_CLICK_POSITION(self):
        """
        Returns the new event type.

        :return: New event Type.
        :rtype: wx.core.PyEventBinder
        """
        return self._cp.get_click_position(self.__type_name)

    def on_left_down(self, event):  # pragma: no cover
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


class MutuallyExclusiveWidgets:
    """
    Implements mutually exclusive widgets, but can also be non-mutually
    exclusive.

    Requires colors to have been globally accessible from a parent class.

       1. self.w_bg_color = Widget background enabled color
       2. self.w_fg_color = Widget foreground enabled color
       3. self.w1_bg_color = Widget background disable color
    """
    _CAT_LABEL_1ST = '!$&'
    _CAT_LABEL_ALOW = "áí'a-z_"
    _WGT_LABEL_1ST = '*@%'
    _WGT_LABEL_ALOW = "áí'a-zA-Z-:() "
    _CHECKBOXES = {}
    _TEXTCTRLES = {}

    def create_widgets(self, num_cb: int=0, num_txt: int=0, cb_pos: str='top',
                       labels: tuple=(), pos_idx: int=0) -> int:
        """
        Create ColorCheckBox and TextCtrl widgets that can be mutually
        exclusive or part of the mutually exclusive group.

        .. note::

           1. The fist label is the category indicator and must be lowercase.
              The first character can be (!, $, &) not MEG (Mutually Exclusive
              Group) indicators, see 2 below.

              a. If the first character of the category (the first label in
                 the labels list) is an exclamation point (!) then all the
                 ColorCheckBoxes are not in the MEG.
              b. If the first character is a dollar sign ($) then all the
                 TextCtrls are not in the MEG.
              c. If the first character is an ampersand (&) then all the
                 ColorCheckBoxes and TextCtrls are not in the MEG.

           2. Labels 2 - n are the labels of the StaticText widgets. The
              first character can be (*, @, %), see 4 for descriptions.

              a. If the fist character of a label is an asterisk (*) this
                 indicates that the ColorCheckBoxes or TextCtrls are not part
                 of the MEG and is read only.
              b. If the first character is an at-sign (@) then the text in
                 TextCtrl is right aligned.
              c. If the fist character is a percent sign (%) then the
                 TextCtrl is not part of the MEG, and the text is right
                 aligned and not editable.

        :param int, num_cb: The number of ColorCheckBoxes.
        :param int num_txt: The number of TextCtrls.
        :param str cb_pos: If `top` the ColorCheckBoxes are on the top and
                           the TextCtrls are on the bottom. If `bottom` the
                           inverse will happen.
        :param tuple labels: A list of labels used in the StaticText widgets.
        :param int pos_idx: The position y index for the GridBagSizer.
        :returns: Position of the next available position.
        :rtype: int
        """
        assert (len(labels) - 1) == (num_cb + num_txt), (
            f"The number of labels '{len(labels) - 1}' are not equal to the "
            f"number of ColorCheckBoxes and TextCtrls '{num_cb + num_txt}'.")
        assert self.is_valid_label(
            labels[0], self._CAT_LABEL_1ST, self._CAT_LABEL_ALOW), (
                f"Invalid category label {labels[0]}.")
        assert all(self.is_valid_label(
            lb, self._WGT_LABEL_1ST, self._WGT_LABEL_ALOW)
                   for lb in labels[1:]), f"Invalid label(s) in {labels[1:]}."

        start_pos = pos_idx
        label = labels[0]
        cb_list = self._CHECKBOXES.setdefault(label, [])
        tc_list = self._TEXTCTRLES.setdefault(label, [])

        if cb_pos == 'top':  # CheckBoxs are on the top
            pos_idx = self._create_ccbs(cb_list, num_cb, labels[1:], pos_idx)
            self._create_ctrls(tc_list, num_txt, labels[1+num_cb:], pos_idx)
        else:  # CheckBoxs are on the bottom
            pos_idx = self._create_ctrls(tc_list, num_txt, labels[1:], pos_idx)
            self._create_ccbs(cb_list, num_cb, labels[1+num_txt:], pos_idx)

        if label[0] not in ('!', '&'):
            for cb in cb_list:
                cb.Bind(EVT_COLOR_CHECKBOX,
                        self.on_checkbox_selected_wrapper(labels[0]))

        if label[0] not in ('$', '&'):
            for tc in tc_list:
                tc.Bind(wx.EVT_SET_FOCUS,
                        self.on_text_focus_wrapper(labels[0]))

        return start_pos + num_cb + num_txt

    def _create_ccbs(self, cb_list, num_cb, labels, pos_idx):
        for num in range(num_cb):
            label = labels[num]

            # An asterisk as the 1st char indicates non-editable.
            if label[0] == '*':
                label = label[1:]
                read_only = True
            else:
                read_only = False

            st = wx.StaticText(self, wx.ID_ANY, label)
            st.SetForegroundColour(self.w_fg_color)
            self.gbs.Add(st, (pos_idx, 0), (1, 1),
                         wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
            cb = ColorCheckBox(self, wx.ID_ANY, bb_color=self.w_fg_color,
                               cb_color=self.w_bg_color, name=make_name(label))
            cb.SetForegroundColour(self.w_fg_color)  # Dark Blue
            cb.SetMinSize((16, 16))
            if read_only: cb.SetReadOnly()
            self.gbs.Add(cb, (pos_idx, 1), (1, 1),
                         wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
            cb_list.append(cb)
            pos_idx += 1

        return pos_idx

    def _create_ctrls(self, tc_list, num_txt, labels, pos_idx):
        for num in range(num_txt):
            label = labels[num]

            if label[0] == '*':  # An asterisk indicates non-editable
                label = label[1:]
                style = wx.TE_READONLY
            elif label[0] == '@':  # In the MEG and Right aligned
                label = label[1:]
                style = wx.TE_RIGHT
            elif label[0] == '%':  # Not in MEG and right aligned
                label = label[1:]
                style = wx.TE_READONLY | wx.TE_RIGHT
            else:
                style = 0

            st = wx.StaticText(self, wx.ID_ANY, label)
            st.SetForegroundColour(self.w_fg_color)
            self.gbs.Add(st, (pos_idx, 0), (1, 1),
                         wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
            tc = wx.TextCtrl(self, wx.ID_ANY, "", style=style,
                             name=make_name(label))

            if style in (wx.TE_READONLY, wx.TE_READONLY | wx.TE_RIGHT):
                tc.Enable(False)
                tc.SetBackgroundColour(self.w1_bg_color)  # Gray
            else:
                tc.SetBackgroundColour(self.w_bg_color)  # Cream

            tc.SetForegroundColour(self.w_fg_color)
            tc.SetMinSize([self.tc_width, 26])
            tc.financial = False if style == 0 else True
            self.gbs.Add(tc, (pos_idx, 1), (1, 1),
                         wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
            tc_list.append(tc)
            pos_idx += 1

        return pos_idx

    def on_checkbox_selected_wrapper(self, category_name):
        cb_list = self._CHECKBOXES[category_name]
        tc_list = self._TEXTCTRLES[category_name]

        def on_checkbox_selected(event):
            selected_cb = event.GetEventObject()

            for cb in cb_list:
                if cb.IsEditable():
                    cb.Enable(cb == selected_cb)
                    cb.SetValue(cb == selected_cb)

            for tc in tc_list:
                if category_name[0] != '$' and tc.IsEditable():
                    tc.Enable(False)
                    tc.SetValue("")
                    tc.SetBackgroundColour(self.w1_bg_color)

        return on_checkbox_selected

    def on_text_focus_wrapper(self, category_name):
        cb_list = self._CHECKBOXES[category_name]
        tc_list = self._TEXTCTRLES[category_name]

        def on_text_focus(event):
            selected_tc = event.GetEventObject()

            # Disable all checkboxes
            for cb in cb_list:
                if category_name[0] != '!' and cb.IsEditable():
                    cb.SetValue(False)
                    cb.Enable(False)

            # Disable all TextCtrls except the selected one.
            for tc in tc_list:
                if tc.IsEditable():
                    if tc == selected_tc:
                        tc.SetBackgroundColour(self.w_bg_color)
                        tc.Enable(True)
                    else:
                        tc.Enable(False)
                        tc.SetBackgroundColour(self.w1_bg_color)

                    tc.SetValue("")

            event.Skip()

        return on_text_focus

    def reset_inputs_wrapper(self, category_name):
        cb_list = self._CHECKBOXES[category_name]
        tc_list = self._TEXTCTRLES[category_name]

        def reset_inputs(event):
            for cb in cb_list:
                if cb.IsEditable():
                    cb.Enable(True)
                    cb.SetValue(False)

            for tc in tc_list:
                if tc.IsEditable():
                    tc.Enable(True)
                    tc.SetValue("")
                    tc.SetBackgroundColour(self.w_bg_color)

        return reset_inputs

    def is_valid_label(self, s, chars, regex):
        if re.match(rf'^[{chars}]?[{regex}]+$', s):
            return all(c not in s[1:] for c in chars)

        return False


class AsyncDataNavigator:
    def __init__(self, fetch_func, step_func, async_runner, cache_size=40,
                 prefetch=1):
        """
        fetch_func(key) -> async function
        async_runner -> your AsyncRunner instance
        """
        self.fetch_func = fetch_func
        self.step_func = step_func
        self.runner = async_runner
        self.cache_size = cache_size
        self.prefetch = prefetch
        self.cache = OrderedDict()
        self.loading = {}

    def seed(self, key, data):
        self.cache[key] = data
        self.cache.move_to_end(key)

    def get(self, key, callback, prefetch_keys=None):
        if key in self.cache and self.cache[key]:
            wx.CallAfter(callback, self.cache[key])
            return

        if key in self.loading:
            self.loading[key].append(callback)
            return

        self.loading[key] = [callback]

        def done(data):
            self.cache[key] = data
            self.cache.move_to_end(key)
            self._trim_cache()
            callbacks = self.loading.pop(key, [])

            for cb in callbacks:
                wx.CallAfter(cb, data)

            self._auto_prefetch(key)

        self.runner.run(self.fetch_func(*key), done)

    def _auto_prefetch(self, key):
        for direction in ("LEFT", "RIGHT"):
            current = key

            for _ in range(self.prefetch):
                current = self.step_func(direction, *current)

                if not current:
                    break

                self._prefetch(current)

    def _prefetch(self, key):
        if key in self.cache or key in self.loading:
            return

        self.loading[key] = []

        def done(data):
            self.loading.pop(key, None)
            self.cache[key] = data
            self.cache.move_to_end(key)
            self._trim_cache()

        self.runner.run(self.fetch_func(*key), done)

    def _trim_cache(self):
        while len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)


class AsyncRunner:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro, callback=None):
        """
        Schedule coroutine.

        callback(result) runs in wx main thread.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)

        if callback:
            def done(f):
                try:
                    result = f.result()
                except Exception as e:
                    print("ASYNC ERROR:", e)   # <-- you'll see the real problem
                    result = []               # safe fallback

                wx.CallAfter(callback, result)

            future.add_done_callback(done)

        return future

