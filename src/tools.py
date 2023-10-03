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

from .config import TomlMetaData
from .bases import BasePanel
from .utilities import GBSRowSwapping, EventStaticText


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


class FieldEdit(GBSRowSwapping, BasePanel, wx.Panel):
    """
    Add or remove fields in various panels.
    """
    tmd = TomlMetaData()
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
                    height = height - th - self.parent.statusbar_size[1]
                    panel_bot.SetSizeHints((tgs_w, height))

        return on_idle

    def _panel_top(self, arg_dict):
        w_bg_color = arg_dict['w_bg_color']
        w_fg_color_0 = arg_dict['w_fg_color_0']
        w_fg_color_1 = arg_dict['w_fg_color_1']
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

        edit_names = self._edit_names
        arg_dict['edit_names'] = edit_names
        edit_names.insert(0, 'Choose the Page to Edit')
        combo_box = wx.ComboBox(panel, wx.ID_ANY, value=edit_names[0],
                                choices=edit_names, style=wx.TE_READONLY)
        combo_box.SetBackgroundColour(wx.Colour(*w_bg_color))
        combo_box.SetForegroundColour(wx.Colour(*w_fg_color_0))
        combo_box.SetMinSize((196, 23))
        self.Bind(wx.EVT_COMBOBOX, self.selection_closure(arg_dict), combo_box)
        grid_sizer.Add(combo_box, (1, 0), (1, 1),
                       wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        field_desc = wx.StaticText(
            panel, wx.ID_ANY, "Enter a new field name:", style=0)
        field_desc.SetForegroundColour(wx.Colour(*w_fg_color_0))
        field_desc.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(field_desc, (2, 0), (1, 1), wx.ALL, 6)

        field_name = wx.TextCtrl(panel,  wx.ID_ANY, "", style=wx.TE_LEFT)
        field_name.SetBackgroundColour(wx.Colour(*w_bg_color))
        field_name.SetForegroundColour(wx.Colour(*w_fg_color_0))
        field_name.SetMinSize((200, 23))
        grid_sizer.Add(field_name, (2, 1), (1, 1), wx.ALL, 6)
        add_button = wx.Button(panel,  wx.ID_ANY, "Add")
        add_button.SetMinSize((50, 23))
        add_button.SetBackgroundColour(wx.Colour(*w_bg_color))
        add_button.SetForegroundColour(wx.Colour(*w_fg_color_0))
        add_button.Bind(wx.EVT_BUTTON, self.add_closuer(arg_dict))
        grid_sizer.Add(add_button, (2, 2), (1, 1), wx.ALL, 6)

        spin_desc = wx.StaticText(
            panel, wx.ID_ANY, "Click field then move it:", style=0)
        spin_desc.SetForegroundColour(wx.Colour(*w_fg_color_0))
        spin_desc.SetFont(wx.Font(
            10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(spin_desc, (3, 0), (1, 1), wx.ALL, 6)
        spin_ctrl = wx.SpinCtrl(self, wx.ID_ANY, "")
        #spin_ctrl.SetMinSize((75, 23))
        spin_ctrl.SetBackgroundColour(wx.Colour(*w_bg_color))
        spin_ctrl.SetForegroundColour(wx.Colour(*w_fg_color_0))
        grid_sizer.Add(spin_ctrl, (3, 1), (1, 1),
                       wx.RIGHT | wx.BOTTOM | wx.TOP, 6)
        line = wx.StaticLine(panel, wx.ID_ANY)
        line.SetBackgroundColour(wx.Colour(*w_fg_color_0))
        grid_sizer.Add(line, (4, 0), (1, 3), wx.EXPAND, 0)
        arg_dict['top_grid_sizer'] = grid_sizer
        arg_dict['spin_ctrl'] = spin_ctrl
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
        grid_sizer = wx.GridBagSizer(vgap=2, hgap=2)
        panel.SetBackgroundColour(wx.Colour(*w_bg_color))
        sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 6)
        widget_labels = arg_dict['widget_labels']

        for idx, label in enumerate(widget_labels):
            label = label.replace(r'\n', '\n')
            widget = EventStaticText(panel, wx.ID_ANY, label)

            if label.endswith(':'):
                span = 1
                weight = 10
                color = w_fg_color_0
            else:
                span = 2
                weight = 12
                color = w_fg_color_1

            if '\n' in label:
                width = 46
            else:
                width = 23

            widget.SetFont(wx.Font(
                weight, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD, 0, ''))
            widget.SetForegroundColour(wx.Colour(*color))
            widget.SetMinSize((-1, width))
            grid_sizer.Add(
                widget, (idx, 0), (1, span),
                wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
            self.Bind(
                widget.event_click_position, self.event_click_closure(
                    grid_sizer, spin_ctrl, wx.Colour(*w_bg_color)),
                id=widget.GetId())

        self.Bind(wx.EVT_SPINCTRL, self.swap_rows_closure(
            grid_sizer, wx.Colour(*w_bg_color)))
        #print(f"Bottom panel size: {panel.GetSize()}")
        arg_dict['panel'] = panel
        arg_dict['bot_grid_sizer'] = grid_sizer
        return panel

    def selection_closure(self, arg_dict):
        def get_selection(event):
            edit_names = arg_dict['edit_names']
            chosen = event.GetString().lower()
            widget_labels = []

            if edit_names[0].lower() != chosen:
                items = self.tmd.panel_config.get(
                    chosen, {}).get('widgets', {})

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

    def event_click_closure(self, gbs, sb, orig_color=None, color='blue'):
        """
        Event to highlight the GBS row when a widget is clicked.
        """
        def event_click(event):
            self.stop_call_later()
            pos = event.get_value()
            row, col = pos
            self.highlight_row(gbs, self.__previous_row, color=orig_color)
            self.highlight_row(gbs, row, color=color)
            self.__previous_row = row
            sb.SetValue(row)
            self.__cl = wx.CallLater(
                4000, self.turn_off_highlight, gbs, orig_color)

        return event_click

    def swap_rows_closure(self, gbs, orig_color):
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
                    self.stop_call_later()
                    flags = (wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT
                             | wx.BOTTOM)
                    self.gbs_swap_rows(gbs, row0, row1, flags, 6)
                    self.Layout()
                    self.__cl = wx.CallLater(
                        4000, self.turn_off_highlight, gbs, orig_color)

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
        self._setup_sizer_height_correctly(bot_grid_sizer, swidth=width)
        wx.CallLater(100, panel.SetupScrolling, rate_x=10, rate_y=10)

    def _destroy_panel(self, panel, parent_sizer):
        if panel and parent_sizer:
            parent_sizer.Remove(1)
            panel.Destroy()
            parent_sizer.Layout()

    def add_closuer(self, arg_dict):
        def add_button(event):
            grid_sizer = arg_dict.get('bot_grid_sizer')

            if grid_sizer:
                row_count = grid_sizer.GetRows()
                print(f"Num of rows: {row_count}")
                print(arg_dict['widget_labels'])

        return add_button

    def static_text_click(self, event):
        print("StaticText Clicked")

    def _find_dict(self, value):
        for item in value:
            if isinstance(item, dict):
                break
            else:
                item = {}

        return item

    def turn_off_highlight(self, gbs, orig_color):
        for row in range(gbs.GetRows()):
            self.__previous_row = None
            self.highlight_row(gbs, row, color=orig_color)
            self.Layout()

    def stop_call_later(self):
        if self.__cl and self.__cl.IsRunning():
            self.__cl.Stop()
            self.__cl = None

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

    @property
    def _edit_names(self):
        item_list = self.parent.menu_items.get('edit', [])
        item_names = []

        if item_list: # Just in case the list is empty.
            for item in item_list[-1].values():
                if item: # Just in case we find a separator.
                    name, tab, key = item[1].partition('\t')
                    if "Close All" in name: continue
                    item_names.append(name.lstrip('&'))

        item_names.sort()
        return item_names
