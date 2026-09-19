# -*- coding: utf-8 -*-
#
# src/tools.py
#
__docformat__ = "restructuredtext en"

from io import StringIO

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .config import TomlMetaData, TomlCreatePanel
from .bases import BasePanel
from .utilities import (AsyncEventLoop, StoreObjects, GridBagSizer,
                        ConfirmationDialog, EventStaticText, make_name)
from .ledger_transaction import LedgerTransaction


class ShortCuts(wx.Frame):
    """
    This dialog displayes the list of short cuts used in the menu bar.
    """
    short_cut_text = None

    def __init__(self, parent, title="Short Cuts"):
        super().__init__(parent, title=title)
        w_fg_color_0 = wx.Colour(50, 50, 204)
        old_style = self.GetWindowStyle()
        self.SetWindowStyle(old_style | wx.STAY_ON_TOP)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.short_cut_text = wx.StaticText(self, wx.TE_MULTILINE, "")
        self.short_cut_text.SetForegroundColour(w_fg_color_0)
        self.short_cut_text.SetFont(wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL, 0, "Courier Prime"))
        self.sizer.Add(self.short_cut_text, 1, wx.EXPAND | wx.ALL, 10)
        dismiss = wx.Button(self, id=wx.ID_OK, label="&Dismiss")
        dismiss.Bind(wx.EVT_BUTTON, self.close_frame)
        self.sizer.Add(dismiss, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        self.SetSizer(self.sizer)
        self.CenterOnParent(dir=wx.BOTH)
        self.Show()

    def close_frame(self, event):
        self.Destroy()

    def create_list(self, parent):
        buff = StringIO()
        self.__recurse_menu(parent.menu_items, buff)
        text = buff.getvalue()
        buff.close()
        return text.strip()

    def __recurse_menu(self, map_, buff, indent=''):
        for item in map_:
            values = map_[item]
            if len(values) == 0: continue  # seperator
            id, nk, disc, cb, mo, tf, od = values
            if not tf: continue
            name, tab, key = nk.partition('\t')
            name = name.replace('&', '') + ':'

            if not id and nk and not cb and mo and tf and od:
                buff.write(f"\n{name:<11}{key:<7}{disc}\n")
                buff.write("--------------\n")
                self.__recurse_menu(od, buff)
            elif id and nk and cb and not mo and tf and not od:
                buff.write(f"\t{indent}{name:<20}{key:<7}{disc}\n")
            elif id and nk and not cb and mo and tf and od:
                buff.write(f"\t{name:<20}{key:<7}{disc}\n")
                buff.write("\t--------------\n")
                self.__recurse_menu(od, buff, indent='\t')

    def set_text(self, parent):
        text = self.create_list(parent)
        self.short_cut_text.SetLabel(text)
        self.Fit()


class FieldEdit(BasePanel, wx.Panel):
    """
    Add or remove fields in various panels.
    """
    _tmd = TomlMetaData()
    _tcp = TomlCreatePanel()
    __previous_row = None
    __cl = None
    _LAST_MOVED = None
    _NEW_FIELDS = []

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._ael = AsyncEventLoop()
        self._db = StoreObjects().get_object('Database')
        self.frame = parent.GetParent()
        self.parent = parent
        self.title = "Add/Hide Fields"
        self._bg_color = wx.Colour(232, 213, 149)
        w_bg_color = wx.Colour(255, 253, 208)   # Cream
        w_fg_color_0 = wx.Colour(50, 50, 204)   # Dark Blue
        w_fg_color_1 = wx.Colour(197, 75, 108)
        self.SetBackgroundColour(self._bg_color)
        # Setup sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        # Setup panels.
        arg_dict = {'parent_sizer': sizer, 'bg_color': self._bg_color,
                    'w_bg_color': w_bg_color, 'w_fg_color_0': w_fg_color_0,
                    'w_fg_color_1': w_fg_color_1}
        panel_top = self._panel_top(arg_dict)
        arg_dict['panel_top'] = panel_top
        sizer.Add(panel_top, 0, wx.EXPAND | wx.ALL, 6)
        # Fix panel size on resize.
        self.__resized = False
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle_closure(arg_dict))
        self.dirty = False

    def on_size(self, event):
        self.__resized = True
        event.Skip()

    def on_idle_closure(self, arg_dict):
        def on_idle(event):
            if self.__resized:
                self.__resized = False
                size = self.parent.GetSize()
                self.SetSize(size)
                # Fix the bottom panel if it exists yet.
                panel_top = arg_dict.get('panel_top')
                panel_bot = arg_dict.get('panel')
                top_grid_sizer = arg_dict.get('top_grid_sizer')

                if panel_top and panel_bot and top_grid_sizer:
                    width, height = self.parent.GetSize()
                    tgs_w, tgs_h = top_grid_sizer.GetMinSize()
                    tw, th = panel_top.GetSize()
                    height = height - th + self.frame.statusbar_size[1]
                    panel_bot.SetSizeHints((tgs_w, height))
                    self.parent.Layout()

        return on_idle

    def _panel_top(self, arg_dict):
        w_bg_color = arg_dict['w_bg_color']
        w_fg_color_0 = arg_dict['w_fg_color_0']
        w_fg_color_1 = arg_dict['w_fg_color_1']
        static_text_flags = (wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.BOTTOM
                             | wx.TOP)
        ctrl_btn_flags = wx.LEFT | wx. BOTTOM | wx.TOP
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        grid_sizer = wx.GridBagSizer(vgap=2, hgap=2)
        sizer.Add(grid_sizer, 0, wx.CENTER | wx.TOP | wx.LEFT | wx.RIGHT, 6)
        title = wx.StaticText(panel, wx.ID_ANY, "Field Editor", style=0)
        title.SetForegroundColour(w_fg_color_1)
        title.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(title, (0, 0), (1, 3), wx.ALIGN_CENTER | wx.ALL, 6)

        desc = wx.StaticText(panel, wx.ID_ANY, self._description, style=0)
        desc.Wrap(450)
        desc.SetForegroundColour(w_fg_color_1)
        desc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(desc, (1, 0), (1, 3), wx.ALIGN_CENTER | wx.ALL, 6)

        # We only want the editable panels.
        edit_names = [panel[0] for panel in self._tmd.panels if panel[2]]
        edit_names.insert(0, 'Choose the Page to Edit')
        combo_box = wx.ComboBox(panel, wx.ID_ANY, value=edit_names[0],
                                choices=edit_names, style=wx.TE_READONLY)
        combo_box.SetBackgroundColour(w_bg_color)
        combo_box.SetForegroundColour(w_fg_color_0)
        combo_box.SetMinSize((200, 32))
        self.Bind(wx.EVT_COMBOBOX, self.selection_closure(arg_dict), combo_box)
        grid_sizer.Add(combo_box, (2, 0), (1, 1), static_text_flags, 6)

        field_desc = wx.StaticText(panel, wx.ID_ANY, "Enter a new field name:",
                                   style=0)
        field_desc.SetForegroundColour(w_fg_color_0)
        field_desc.SetFont(
            wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(field_desc, (3, 0), (1, 1), static_text_flags, 4)

        field_name = wx.TextCtrl(panel,  wx.ID_ANY, "", style=wx.TE_LEFT)
        field_name.SetBackgroundColour(w_bg_color)
        field_name.SetForegroundColour(w_fg_color_0)
        field_name.SetMinSize((266, 32))
        grid_sizer.Add(field_name, (3, 1), (1, 1), ctrl_btn_flags, 4)

        embed_sizer = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer.Add(embed_sizer, (4, 1), (1, 1), ctrl_btn_flags, 4)
        but_flags = wx.RIGHT

        add_button = wx.Button(panel,  wx.ID_ANY, "Add Field")
        add_button.SetMinSize((77, 32))
        add_button.SetBackgroundColour(w_bg_color)
        add_button.SetForegroundColour(w_fg_color_0)
        embed_sizer.Add(add_button, 0, but_flags, 6)

        hide_button = wx.Button(panel,  wx.ID_ANY, "Hide/Unhide")
        hide_button.SetMinSize((77, 32))
        hide_button.SetBackgroundColour(w_bg_color)
        hide_button.SetForegroundColour(w_fg_color_0)
        embed_sizer.Add(hide_button, 0, but_flags, 6)

        update_button = wx.Button(panel,  wx.ID_ANY, "Rename")
        update_button.SetMinSize((77, 32))
        update_button.SetBackgroundColour(w_bg_color)
        update_button.SetForegroundColour(w_fg_color_0)
        embed_sizer.Add(update_button, 0, but_flags, 6)

        undo_button = wx.Button(panel,  wx.ID_ANY, "Undo Last")
        undo_button.SetMinSize((77, 32))
        undo_button.SetBackgroundColour(w_bg_color)
        undo_button.SetForegroundColour(w_fg_color_0)
        embed_sizer.Add(undo_button, 0, but_flags, 6)

        spin_desc = wx.StaticText(
            panel, wx.ID_ANY, "Click field then move it:", style=0)
        spin_desc.SetForegroundColour(w_fg_color_0)
        spin_desc.SetFont(wx.Font(
            12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(spin_desc, (5, 0), (1, 1), static_text_flags, 4)
        spin_ctrl = wx.SpinCtrl(panel, wx.ID_ANY, name="")
        spin_ctrl.SetMinSize((-1, 32))
        spin_ctrl.SetBackgroundColour(w_bg_color)
        spin_ctrl.SetForegroundColour(w_fg_color_0)
        grid_sizer.Add(spin_ctrl, (5, 1), (1, 1), ctrl_btn_flags, 4)

        arg_dict['top_grid_sizer'] = grid_sizer
        arg_dict['spin_ctrl'] = spin_ctrl
        arg_dict['new_field_name'] = field_name
        arg_dict['add_button'] = add_button
        arg_dict['update_button'] = update_button
        arg_dict['hide_button'] = hide_button
        arg_dict['undo_buttom'] = undo_button
        return panel

    def _panel_bot(self, arg_dict):
        w_bg_color = arg_dict['w_bg_color']
        spin_ctrl = arg_dict['spin_ctrl']
        spin_ctrl.SetValue("")
        panel = ScrolledPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        grid_sizer = GridBagSizer(vgap=2, hgap=2)
        panel.SetBackgroundColour(w_bg_color)
        sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 6)
        widget_labels = arg_dict['widget_labels']
        arg_dict['panel'] = panel
        arg_dict['bot_grid_sizer'] = grid_sizer

        for row, (label, hidable) in enumerate(widget_labels):
            if label.endswith(':'):
                span = 1
                fs = 12
                wh = (-1, -1)
                weight = wx.FONTWEIGHT_NORMAL
            else:
                span = 2
                fs = 12
                width = 448
                wh = (width, 50 if len(label) > width/8 else -1)
                weight = wx.FONTWEIGHT_BOLD

            self._create_static_text(arg_dict, label, row, span=span, fs=fs,
                                     wh=wh, weight=weight, hidable=hidable)

        self.bind_events(arg_dict)
        return panel

    def bind_events(self, arg_dict):
        w_bg_color = arg_dict['w_bg_color']
        add_button = arg_dict['add_button']
        update_button = arg_dict['update_button']
        hide_button = arg_dict['hide_button']
        undo_button = arg_dict['undo_buttom']

        #evt_b = add_button.Unbind(wx.EVT_BUTTON)
        add_button.Bind(wx.EVT_BUTTON, self.add_closuer(arg_dict))

        #evt_r = hide_button.Unbind(wx.EVT_BUTTON)
        hide_button.Bind(wx.EVT_BUTTON, self.hide_closuer(arg_dict))

        #evt_u = update_button.Unbind(wx.EVT_BUTTON)
        update_button.Bind(wx.EVT_BUTTON, self.rename_closuer(arg_dict))

        #evt_d = undo_button.Unbind(wx.EVT_BUTTON)
        undo_button.Bind(wx.EVT_BUTTON, self.undo_closuer(arg_dict))

        #evt_s = self.Unbind(wx.EVT_SPINCTRL)
        self.Bind(wx.EVT_SPINCTRL, self.swap_rows_closure(
            arg_dict, w_bg_color))

    def selection_closure(self, arg_dict):
        def get_selection(event):
            edit_names = {m_name: name for m_name, name, _ in self._tmd.panels}
            chosen = edit_names.get(event.GetString())
            widget_labels = []

            if chosen:
                items = self._tmd.panel_config.get(
                    chosen, {}).get('widgets', {})
                self._tcp.current_panel = items

                for value in items.values():
                    if (isinstance(value, list) and value[0] == 'StaticText'):
                        args = self._find_dict(value).get('args', [])
                        hidable = self._find_dict(value).get('hidable', True)
                        widget_labels.append((args[2], hidable))

                arg_dict['widget_labels'] = widget_labels
                self._create_widgets(arg_dict)
            else:
                self._destroy_panel(arg_dict.get('panel'),
                                    arg_dict.get('parent_sizer'))

        return get_selection

    def event_click_closure(self, arg_dict: dict, orig_color=None,
                            color='lightblue'):
        """
        Event to highlight the GBS row when a widget is clicked.
        """
        hide_button = arg_dict['hide_button']

        def event_click(event):
            self._stop_call_later()
            gbs = arg_dict.get('bot_grid_sizer')
            spin_ctrl = arg_dict['spin_ctrl']
            field_name = arg_dict['new_field_name']
            widget = event.get_window()
            arg_dict['current_widget'] = widget

            if widget.hidable:
                hide_button.Show()
            else:
                hide_button.Hide()

            field_name.SetValue(widget.GetLabel())
            row, col = event.get_value()
            gbs.highlight_row(self.__previous_row, orig_color)
            gbs.highlight_row(row, color)
            self.__previous_row = row
            spin_ctrl.SetValue(row)
            spin_ctrl.SetRange(0, gbs.GetRows() - 1)

        return event_click

    def swap_rows_closure(self, arg_dict: dict, orig_color):
        """
        Event to swap two rows.
        """
        def swap_rows(event):
            if self.__previous_row is not None:
                row0 = self.__previous_row
                obj = event.GetEventObject()
                row1 = obj.GetValue()
                self.__previous_row = row1

                if row0 != row1:
                    gbs = arg_dict.get('bot_grid_sizer')
                    self._stop_call_later()
                    gbs.swap_rows(row0, row1)
                    self.Layout()
                    self.__cl = wx.CallLater(
                        7000, self._turn_off_highlight, arg_dict, orig_color)

        return swap_rows

    def _create_widgets(self, arg_dict: dict):
        parent_sizer = arg_dict['parent_sizer']
        panel = arg_dict.get('panel')
        # Destroy previous panel if it exists.
        self._destroy_panel(panel, parent_sizer)
        # Create new panel.
        panel = self._panel_bot(arg_dict)
        parent_sizer.Add(panel, 0, wx.CENTER | wx.ALL, 6)
        width, height = arg_dict['top_grid_sizer'].GetMinSize()
        self._update_screen_size(arg_dict)

    def _destroy_panel(self, panel, parent_sizer):
        if panel and parent_sizer:
            parent_sizer.Remove(1)
            panel.Destroy()
            parent_sizer.Layout()

    def add_closuer(self, arg_dict: dict):
        def add_button(event):
            fn_widget = arg_dict['new_field_name']
            name = fn_widget.GetValue()

            if name:
                new_name = name if name.endswith(':') else name + ':'

                if (name not in self._tcp.all_field_names
                    and new_name not in self._tcp.field_names):
                    gbs = arg_dict.get('bot_grid_sizer')
                    rows = gbs.GetRows()
                    self._create_static_text(arg_dict, new_name, rows)
                    self._tcp.add_name(name)
                    self._update_screen_size(arg_dict)
                    self._LAST_MOVED = (new_name, None, 'add')
                else:
                    msg = f"Duplicate field name '{name}' found."
                    self.frame.statusbar_warning = msg

                fn_widget.SetValue("")

        return add_button

    def hide_closuer(self, arg_dict: dict):
        def hide_button(event):
            name = arg_dict['new_field_name'].GetValue()

            if name.endswith(':'):
                w_fg_color_0 = arg_dict['w_fg_color_0']
                year = self._db.cache.year
                lt = LedgerTransaction(self._db)
                field_name = make_name(name)
                data = self._ael.run_async(lt.select_expenses(
                    year=year, field_name=field_name))

                if data:
                    cap = "Data Found"
                    msg = (f"Data found for the field '{name}' so it "
                           "cannot be hidden.")
                    w_fg_color = wx.Colour(w_fg_color_0)
                    dlg = ConfirmationDialog(self, msg, cap, enable=False,
                                             fg_color=w_fg_color)
                    dlg.show()
                else:
                    gbs = arg_dict.get('bot_grid_sizer')
                    rows = gbs.GetRows()
                    # Row to hide
                    spin_ctrl = arg_dict['spin_ctrl']
                    row = spin_ctrl.GetValue()

                    if row >= 0:
                        spin_ctrl.SetValue("")

                        for count in range(rows-row-1):
                            gbs.swap_rows(count+row, count+row+1)

                        windows = [(item.GetWindow())
                                   for item in gbs.GetChildren()
                                   if item and item.GetPos()[0] == rows-1]

                        for window in windows:
                            window.Unbind(window.EVT_CLICK_POSITION)
                            window.Destroy()

                        self._tcp.hide_widget(name)
                        gbs.Layout()
                        arg_dict['panel'].Layout()
                        spin_ctrl = arg_dict['spin_ctrl']
                        self._LAST_MOVED = (name, row, 'hide')
            elif name:
                self.frame.statusbar_warning = "Cannot hide title fields."

            arg_dict['new_field_name'].SetValue('')

        return hide_button

    def rename_closuer(self, arg_dict: dict):
        def rename_button(event):
            name = arg_dict['new_field_name'].GetValue()

            if name.endswith(':'):
                if name not in self._tcp.field_names:
                    widget = arg_dict['current_widget']
                    old_name = widget.GetLabel()
                    widget.SetLabel(name)
                    self._tcp.rename_label(old_name, name)
                else:
                    msg = f"Duplicate field name '{name}' found."
                    self.frame.statusbar_warning = msg
            elif name:
                arg_dict['current_widget'].SetLabel(name)

            arg_dict['new_field_name'].SetValue("")

        return rename_button

    def undo_closuer(self, arg_dict: dict):
        def undo_button(event):
            last = self._tcp.last_changed

            if last:
                type_ = last[-1]
                self._tcp.undo_change()
                # The property self._tcp.last_changed is None at this point.

                if type_ == 'add' and self._LAST_MOVED[-1] == 'add':
                    label, _ = self._LAST_MOVED[:2]
                    row = self._find_widget_row(arg_dict, label)
                    gbs = arg_dict.get('bot_grid_sizer')
                    rows = gbs.GetRows()

                    for count in range(row, rows):
                        if (count + 1) < rows:
                            gbs.swap_rows(count, count + 1)

                    self._remove_by_position(arg_dict, count, 0)
                    self._LAST_MOVED = None
                elif type_ == 'hide' and self._LAST_MOVED[-1] == 'hide':
                    name, row = self._LAST_MOVED[:2]
                    gbs = arg_dict.get('bot_grid_sizer')
                    rows = gbs.GetRows()
                    self._create_static_text(arg_dict, name, rows)

                    if row >= 0:
                        for count in reversed(range(row, rows)):
                            gbs.swap_rows(count+1, count)

                    self._LAST_MOVED = None
                elif type_ == 'rename':
                    widget = arg_dict['current_widget']
                    widget.SetLabel(last[0])
                    self._LAST_MOVED = None

        return undo_button

    def _create_static_text(self, arg_dict: dict, label: str, row: int, *,
                            span: int=1, fs: int=12, wh: tuple=(-1, -1),
                            weight: int=wx.FONTWEIGHT_NORMAL,
                            hidable: bool=True) -> None:
        """
        Create the custom EventStaticText widget.

        :param dict arg_dict: Internal dict that containes needed values
                              and objects.
        :param str label: The widget label.
        :param int row: The row in the sizer.
        :param int span: The span arg for the sizer.
        :param int fs: The font size.
        :param tuple wh: The width and height of the widget.
        :param int weight: The font weight.
        :param bool hidable: If the widget can be hidden.
        """
        panel = arg_dict['panel']
        grid_sizer = arg_dict.get('bot_grid_sizer')
        w_bg_color = arg_dict['w_bg_color']
        w_fg_color_0 = arg_dict['w_fg_color_0']
        widget = EventStaticText(panel, wx.ID_ANY, label)
        widget.SetFont(wx.Font(fs, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                               weight, 0, ''))
        widget.SetForegroundColour(w_fg_color_0)
        widget.SetMinSize(wh)
        widget.hidable = hidable
        grid_sizer.Add(widget, (row, 0), (1, span), wx.ALIGN_CENTER_VERTICAL
                       | wx.LEFT | wx.RIGHT | wx.TOP, 6)
        grid_sizer.Layout()
        self.Bind(widget.EVT_CLICK_POSITION, self.event_click_closure(
            arg_dict, orig_color=w_bg_color), id=widget.GetId())

    def _find_widget_row(self, arg_dict: dict, label: str) -> int:
        """
        Finf the row in the sizer of the widget.

        :param dict arg_dict: Internal dict that containes needed values
                              and objects.
        :param str label: The label of the widget.
        :returns: The pistion of the widget.
        :rtype: int
        """
        gbs = arg_dict.get('bot_grid_sizer')
        row = None

        for item in gbs.GetChildren():
            window = item.GetWindow()

            if window:
                tgt = window.GetLabel() if hasattr(window, 'GetLabel') else ""

                if tgt == label:
                    row = item.GetPos().GetRow()
                    break

        return row

    def _remove_by_position(self, arg_dict: dict, row: int, col: int) -> bool:
        """
        Finds and removes the item at a specific (row, col).

        :param dict arg_dict: Internal dict that containes needed values
                              and objects.
        :param int row: The row in the sizer.
        :param int col: The column in the sizer.
        :returns: If `True` the removal happened else if `False` it didn't.
        :rtype: bool
        """
        ret = False
        gbs = arg_dict['bot_grid_sizer']

        for i, item in enumerate(gbs.GetChildren()):
            pos = item.GetPos()

            if pos.GetRow() == row and pos.GetCol() == col:
                window = item.GetWindow()

                if window:
                    gbs.Detach(window)
                    window.Destroy()

                gbs.Layout()
                panel = arg_dict['panel']

                if panel:
                    panel.Layout()
                    panel.Refresh()

                ret = True

        return ret

    def _turn_off_highlight(self, arg_dict, orig_color):
        gbs = arg_dict.get('bot_grid_sizer')
        arg_dict['spin_ctrl'].SetValue("")
        arg_dict['new_field_name'].SetValue("")

        for row in range(gbs.GetRows()):
            self.__previous_row = None
            gbs.highlight_row(row, orig_color)
            self.Layout()

    def _stop_call_later(self):
        if self.__cl and self.__cl.IsRunning():
            self.__cl.Stop()
            self.__cl = None

    def _update_screen_size(self, arg_dict):
        panel = arg_dict['panel']
        width, height = arg_dict['top_grid_sizer'].GetMinSize()
        wx.CallLater(100, panel.SetupScrolling, rate_x=20, rate_y=40)

    @property
    def _description(self):
        buff = StringIO()
        buff.write("This page allows you to add, hide, or rename fields on ")
        buff.write("various data entry pages. Fields can never be deleted ")
        buff.write("and should only be hidden at the start of a Fiscal Year ")
        buff.write("before the field is used. If hidden later in the year ")
        buff.write("valid data may be missing from reports and cause ")
        buff.write("balences to not be correct.")
        value = buff.getvalue()
        buff.close()
        return value
