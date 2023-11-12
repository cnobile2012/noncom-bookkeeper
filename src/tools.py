# -*- coding: utf-8 -*-
#
# src/tools.py
#
__docformat__ = "restructuredtext en"

import types
from io import StringIO
from pprint import pprint # *** TODO *** Remove later

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .config import TomlMetaData, TomlCreatePanel
from .bases import BasePanel
from .utilities import GridBagSizer, ConfirmationDialog, EventStaticText


class ShortCuts(wx.Frame):
    """
    This dialog displayes the list of short cuts used in the menu bar.
    """
    short_cut_text = None

    def __init__(self, parent, title="Short Cuts"):
        super().__init__(parent, title=title)
        w_fg_color_0 = (50, 50, 204)
        old_style = self.GetWindowStyle()
        self.SetWindowStyle(old_style | wx.STAY_ON_TOP)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.short_cut_text = wx.StaticText(self, wx.TE_MULTILINE, "")
        self.short_cut_text.SetForegroundColour(wx.Colour(*w_fg_color_0))
        self.short_cut_text.SetFont(wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL, 0, "Courier Prime"))
        self.sizer.Add(self.short_cut_text, 1, wx.EXPAND | wx.ALL, 10)
        dismiss = wx.Button(self, id=wx.ID_OK, label="&Dismiss")
        dismiss.Bind(wx.EVT_BUTTON, self.close_frame)
        self.sizer.Add(dismiss, 0, wx.ALL|wx.ALIGN_CENTER,5)
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
            if len(values) == 0: continue # seperator
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

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.title = "Add/Remove Fields"
        self._bg_color = (232, 213, 149)
        w_bg_color = (222, 237, 230)
        w_fg_color_0 = (50, 50, 204)
        w_fg_color_1 = (197, 75, 108)
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
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

    def on_size(self, event):
        event.Skip()
        self.__resized = True

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
                    height = height - th + self.parent.statusbar_size[1]
                    panel_bot.SetSizeHints((tgs_w, height))
                    self.parent.Layout()

        return on_idle

    def _panel_top(self, arg_dict):
        w_bg_color = arg_dict['w_bg_color']
        w_fg_color_0 = arg_dict['w_fg_color_0']
        w_fg_color_1 = arg_dict['w_fg_color_1']
        static_text_flags = (wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.BOTTOM
                             | wx.TOP)
        ctrl_but_flags = wx.LEFT | wx. BOTTOM | wx.TOP
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        grid_sizer = wx.GridBagSizer(vgap=2, hgap=2)
        sizer.Add(grid_sizer, 0, wx.CENTER | wx.TOP | wx.LEFT | wx.RIGHT, 6)
        desc = wx.StaticText(panel, wx.ID_ANY, self._description, style=0)
        desc.SetForegroundColour(wx.Colour(*w_fg_color_1))
        desc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(desc, (0, 0), (1, 3), wx.ALIGN_CENTER | wx.ALL, 6)

        edit_names = [m_name for m_name, name in self._tmd.panels]
        edit_names.insert(0, 'Choose the Page to Edit')
        combo_box = wx.ComboBox(panel, wx.ID_ANY, value=edit_names[0],
                                choices=edit_names, style=wx.TE_READONLY)
        combo_box.SetBackgroundColour(wx.Colour(*w_bg_color))
        combo_box.SetForegroundColour(wx.Colour(*w_fg_color_0))
        combo_box.SetMinSize((200, 32))
        self.Bind(wx.EVT_COMBOBOX, self.selection_closure(arg_dict), combo_box)
        grid_sizer.Add(combo_box, (1, 0), (1, 1), static_text_flags, 6)

        field_desc = wx.StaticText(
            panel, wx.ID_ANY, "Enter a new field name:", style=0)
        field_desc.SetForegroundColour(wx.Colour(*w_fg_color_0))
        field_desc.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(field_desc, (2, 0), (1, 1), static_text_flags, 4)

        field_name = wx.TextCtrl(panel,  wx.ID_ANY, "", style=wx.TE_LEFT)
        field_name.SetBackgroundColour(wx.Colour(*w_bg_color))
        field_name.SetForegroundColour(wx.Colour(*w_fg_color_0))
        field_name.SetMinSize((266, 32))
        grid_sizer.Add(field_name, (2, 1), (1, 1), ctrl_but_flags, 4)

        embed_sizer = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer.Add(embed_sizer, (3, 1), (1, 1), ctrl_but_flags, 4)
        but_flags = wx.RIGHT

        add_button = wx.Button(panel,  wx.ID_ANY, "Add")
        add_button.SetMinSize((62, 32))
        add_button.SetBackgroundColour(wx.Colour(*w_bg_color))
        add_button.SetForegroundColour(wx.Colour(*w_fg_color_0))
        embed_sizer.Add(add_button, 0, but_flags, 6)
        update_button = wx.Button(panel,  wx.ID_ANY, "Update")
        update_button.SetMinSize((62, 32))
        update_button.SetBackgroundColour(wx.Colour(*w_bg_color))
        update_button.SetForegroundColour(wx.Colour(*w_fg_color_0))
        embed_sizer.Add(update_button, 0, but_flags, 6)
        remove_button = wx.Button(panel,  wx.ID_ANY, "Remove")
        remove_button.SetMinSize((62 , 32))
        remove_button.SetBackgroundColour(wx.Colour(*w_bg_color))
        remove_button.SetForegroundColour(wx.Colour(*w_fg_color_0))
        embed_sizer.Add(remove_button, 0, but_flags, 6)
        undo_button = wx.Button(panel,  wx.ID_ANY, "Undo")
        undo_button.SetMinSize((62 , 32))
        undo_button.SetBackgroundColour(wx.Colour(*w_bg_color))
        undo_button.SetForegroundColour(wx.Colour(*w_fg_color_0))
        embed_sizer.Add(undo_button, 0, but_flags, 6)

        spin_desc = wx.StaticText(
            panel, wx.ID_ANY, "Click field then move it:", style=0)
        spin_desc.SetForegroundColour(wx.Colour(*w_fg_color_0))
        spin_desc.SetFont(wx.Font(
            10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(spin_desc, (4, 0), (1, 1), static_text_flags, 4)
        spin_ctrl = wx.SpinCtrl(panel, wx.ID_ANY, name="")
        spin_ctrl.SetMinSize((-1, 32))
        spin_ctrl.SetBackgroundColour(wx.Colour(*w_bg_color))
        spin_ctrl.SetForegroundColour(wx.Colour(*w_fg_color_0))
        grid_sizer.Add(spin_ctrl, (4, 1), (1, 1), ctrl_but_flags, 4)

        line = wx.StaticLine(panel, wx.ID_ANY)
        line.SetBackgroundColour(wx.Colour(*w_fg_color_0))
        grid_sizer.Add(line, (5, 0), (1, 3), wx.EXPAND, 0)
        arg_dict['top_grid_sizer'] = grid_sizer
        arg_dict['spin_ctrl'] = spin_ctrl
        arg_dict['new_field_name'] = field_name
        arg_dict['add_button'] = add_button
        arg_dict['update_button'] = update_button
        arg_dict['remove_button'] = remove_button
        arg_dict['undo_buttom'] = undo_button
        #print(f"Top panel size: {panel.GetSize()}")
        return panel

    def _panel_bot(self, arg_dict):
        w_bg_color = arg_dict['w_bg_color']
        w_fg_color_0 = arg_dict['w_fg_color_0']
        w_fg_color_1 = arg_dict['w_fg_color_1']
        spin_ctrl = arg_dict['spin_ctrl']
        panel = ScrolledPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        grid_sizer = GridBagSizer(vgap=2, hgap=2)
        panel.SetBackgroundColour(wx.Colour(*w_bg_color))
        sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 6)
        widget_labels = arg_dict['widget_labels']

        for idx, label in enumerate(widget_labels):
            widget = EventStaticText(panel, wx.ID_ANY, label)

            if label.endswith(':'):
                span = 1
                ps = 12
                width = -1
                height = -1
                weight = wx.FONTWEIGHT_NORMAL
            else:
                span = 2
                ps = 12
                width = 448
                height = 50 if len(label) > width/8 else -1
                weight = wx.FONTWEIGHT_BOLD

            widget.SetFont(wx.Font(
                ps, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, weight, 0, ''))
            widget.SetForegroundColour(wx.Colour(*w_fg_color_0))
            widget.SetMinSize((width, height))
            grid_sizer.Add(
                widget, (idx, 0), (1, span),
                wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, 6)
            spin_ctrl.SetValue("")
            self.Bind(
                widget.EVT_CLICK_POSITION, self.event_click_closure(
                    arg_dict, orig_color=wx.Colour(*w_bg_color)),
                id=widget.GetId())

        arg_dict['panel'] = panel
        arg_dict['bot_grid_sizer'] = grid_sizer
        self.bind_events(arg_dict)
        return panel

    def bind_events(self, arg_dict):
        spin_ctrl = arg_dict['spin_ctrl']
        grid_sizer = arg_dict['bot_grid_sizer']
        w_bg_color = arg_dict['w_bg_color']
        add_button = arg_dict['add_button']
        update_button = arg_dict['update_button']
        remove_button = arg_dict['remove_button']
        undo_button = arg_dict['undo_buttom']

        evt_b = add_button.Unbind(wx.EVT_BUTTON)
        add_button.Bind(wx.EVT_BUTTON, self.add_closuer(arg_dict))

        evt_u = update_button.Unbind(wx.EVT_BUTTON)
        update_button.Bind(wx.EVT_BUTTON, self.update_closuer(arg_dict))

        evt_r = remove_button.Unbind(wx.EVT_BUTTON)
        remove_button.Bind(wx.EVT_BUTTON, self.remove_closuer(arg_dict))

        evt_d = undo_button.Unbind(wx.EVT_BUTTON)
        undo_button.Bind(wx.EVT_BUTTON, self.undo_closuer(arg_dict))

        evt_s = self.Unbind(wx.EVT_SPINCTRL)
        self.Bind(wx.EVT_SPINCTRL, self.swap_rows_closure(
            arg_dict, wx.Colour(*w_bg_color)))

    def selection_closure(self, arg_dict):
        def get_selection(event):
            edit_names = {m_name: name for m_name, name in self._tmd.panels}
            chosen = edit_names.get(event.GetString())
            widget_labels = []

            if chosen:
                items = self._tmd.panel_config.get(
                    chosen, {}).get('widgets', {})
                self._tcp.current_panel = items

                for value in items.values():
                    if (isinstance(value, list) and value[0] == 'StaticText'):
                        args = self._find_dict(value).get('args', [])
                        widget_labels.append(args[2])

                arg_dict['widget_labels'] = widget_labels
                self._create_widgets(arg_dict)
            else:
                self._destroy_panel(arg_dict.get('panel'),
                                    arg_dict.get('parent_sizer'))

        return get_selection

    def event_click_closure(self, arg_dict, orig_color=None,
                            color='lightblue'):
        """
        Event to highlight the GBS row when a widget is clicked.
        """
        def event_click(event):
            self.stop_call_later()
            gbs = arg_dict.get('bot_grid_sizer')
            spin_ctrl = arg_dict['spin_ctrl']
            field_name = arg_dict['new_field_name']
            widget = event.get_window()
            arg_dict['current_widget'] = widget
            field_name.SetValue(widget.GetLabel())
            pos = event.get_value()
            row, col = pos
            gbs.highlight_row(self.__previous_row, orig_color)
            gbs.highlight_row(row, color)
            self.__previous_row = row
            spin_ctrl.SetValue(row)
            spin_ctrl.SetRange(0, gbs.GetRows() - 1)
            self.__cl = wx.CallLater(
                7000, self.turn_off_highlight, arg_dict, orig_color)

        return event_click

    def swap_rows_closure(self, arg_dict, orig_color):
        """
        Event to swap the two rows.
        """
        def swap_rows(event):
            if self.__previous_row is not None:
                row0 = self.__previous_row
                obj = event.GetEventObject()
                row1 = obj.GetValue()
                self.__previous_row = row1

                if row0 != row1:
                    gbs = arg_dict.get('bot_grid_sizer')
                    self.stop_call_later()
                    gbs.swap_rows(row0, row1)
                    self.Layout()
                    self.__cl = wx.CallLater(
                        7000, self.turn_off_highlight, arg_dict, orig_color)

        return swap_rows

    def _create_widgets(self, arg_dict):
        parent_sizer = arg_dict['parent_sizer']
        panel = arg_dict.get('panel')
        # Destroy previous panel if it exists.
        self._destroy_panel(panel, parent_sizer)
        # Create new panel.
        panel = self._panel_bot(arg_dict)
        parent_sizer.Add(panel, 0, wx.CENTER | wx.ALL, 6)
        width, height = arg_dict['top_grid_sizer'].GetMinSize()
        bot_grid_sizer = arg_dict['bot_grid_sizer']
        self._update_screen_size(arg_dict)

    def _destroy_panel(self, panel, parent_sizer):
        if panel and parent_sizer:
            parent_sizer.Remove(1)
            panel.Destroy()
            parent_sizer.Layout()

    def add_closuer(self, arg_dict):
        def add_button(event):
            panel = arg_dict['panel']
            w_bg_color = arg_dict['w_bg_color']
            w_fg_color_0 = arg_dict['w_fg_color_0']
            grid_sizer = arg_dict.get('bot_grid_sizer')
            field_name = arg_dict['new_field_name']
            spin_ctrl = arg_dict['spin_ctrl']
            value = field_name.GetValue()

            if value:
                value = value if value.endswith(':') else value + ':'

                if value not in self._tcp.field_names:
                    row_count = grid_sizer.GetRows()
                    widget = EventStaticText(panel, wx.ID_ANY, value)
                    widget.SetFont(wx.Font(
                        12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL, 0, ''))
                    widget.SetForegroundColour(wx.Colour(*w_fg_color_0))
                    widget.SetMinSize((-1, -1))
                    grid_sizer.Add(widget, (row_count, 0), (1, 1),
                                   (wx.ALIGN_CENTER_VERTICAL | wx.LEFT
                                    | wx.RIGHT), 6)
                    grid_sizer.Layout()
                    self.Bind(
                        widget.EVT_CLICK_POSITION, self.event_click_closure(
                            arg_dict, orig_color=wx.Colour(*w_bg_color)),
                        id=widget.GetId())
                    self.bind_events(arg_dict)
                    self._tcp.add_name(value)
                    self._update_screen_size(arg_dict)
                else:
                    msg = "Duplicate fields are not allowed."
                    self.parent.statusbar_warning = msg

                field_name.SetValue("")

        return add_button

    def update_closuer(self, arg_dict):
        def update_button(event):
            value = arg_dict['new_field_name'].GetValue()

            if value.endswith(':'):
                widget = arg_dict['current_widget']
                widget.SetLabel(value if value.endswith(':') else value + ':')
            elif value:
                self.parent.statusbar_warning = "Cannot update title fields."

            field_name.SetValue("")

        return update_button

    def remove_closuer(self, arg_dict):
        def remove_button(event):
            value = arg_dict['new_field_name'].GetValue()

            if value.endswith(':'):
                w_fg_color_0 = arg_dict['w_fg_color_0']
                msg = f'Confirm the removal of the following field:\n"{value}"'

                # *** TODO *** Check database for entries on this field.

                cap = "Removal Confirmation"
                dlg = ConfirmationDialog(self, msg, cap, fg_color=w_fg_color_0)
                ret = dlg.show()

                if ret:
                    gbs = arg_dict.get('bot_grid_sizer')
                    rows = gbs.GetRows()
                    # Row to remove
                    spin_ctrl = arg_dict['spin_ctrl']
                    row = spin_ctrl.GetValue()

                    # Move the row to remove to the end of the list.
                    if row >= 0:
                        spin_ctrl.SetValue("")
                        start_row = row

                        for count in range(rows-row-1):
                            self.gbs_swap_rows(gbs, start_row, start_row+1)
                            start_row += 1

                        windows = [(item.GetWindow())
                                   for item in gbs.GetChildren()
                                   if item and item.GetPos()[0] == rows-1]

                        for window in windows:
                            window.Unbind(window.EVT_CLICK_POSITION)
                            window.Destroy()

                        self._tcp.remove_name(value)
                        gbs.Layout()
                        arg_dict['panel'].Layout()
            elif value:
                self.parent.statusbar_warning = "Cannot remove title fields."

        return remove_button

    def undo_closuer(self, arg_dict):
        def undo_button(event):
            value = arg_dict['new_field_name'].GetValue()

            if value.endswith(':'):
                self._tcp.undo_name(name)


        return undo_button

    def turn_off_highlight(self, arg_dict, orig_color):
        gbs = arg_dict.get('bot_grid_sizer')
        arg_dict['spin_ctrl'].SetValue("")
        arg_dict['new_field_name'].SetValue("")

        for row in range(gbs.GetRows()):
            self.__previous_row = None
            gbs.highlight_row(row, orig_color)
            self.Layout()

    def stop_call_later(self):
        if self.__cl and self.__cl.IsRunning():
            self.__cl.Stop()
            self.__cl = None

    def _update_screen_size(self, arg_dict):
        panel = arg_dict['panel']
        grid_sizer = arg_dict.get('bot_grid_sizer')
        width, height = arg_dict['top_grid_sizer'].GetMinSize()
        self._setup_sizer_height_correctly(grid_sizer, swidth=width)
        wx.CallLater(100, panel.SetupScrolling, rate_x=20, rate_y=40)

    @property
    def _description(self):
        buff = StringIO()
        buff.write("This page allows you to add or delete fields on various ")
        buff.write("data entry pages.\nDeletion of fields should only be ")
        buff.write("done when this application is first run.\nIf it is done ")
        buff.write("afterwards data may disappear from reports.")
        value = buff.getvalue()
        buff.close()
        return value
