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
        self.set_text(parent)
        self.short_cut_text.SetFont(wx.Font(
            10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL, 0, "Courier Prime"))
        self.sizer.Add(self.short_cut_text, 1,
                       wx.ALL | wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
        dismiss = wx.Button(self, id=wx.ID_OK, label="&Dismiss")
        dismiss.Bind(wx.EVT_BUTTON, self.close_frame)
        self.sizer.Add(dismiss, 0, wx.ALL|wx.ALIGN_CENTER,5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
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


class FieldEdit(BasePanel, wx.Panel):
    """
    Add or remove fields in various panels.
    """
    tmd = TomlMetaData()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.title = '''Add/Remove Fields'''
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

    def _panel_top(self, arg_dict):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        grid_sizer = wx.GridBagSizer(vgap=2, hgap=2)
        sizer.Add(grid_sizer, 0, wx.CENTER | wx.TOP | wx.LEFT | wx.RIGHT, 6)
        w_bg_color = arg_dict['w_bg_color']
        w_fg_color_0 = arg_dict['w_fg_color_0']
        w_fg_color_1 = arg_dict['w_fg_color_1']
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

        field_desc = wx.StaticText(panel, wx.ID_ANY, "Enter a new field name:",
                                   style=0)
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

        line = wx.StaticLine(panel, wx.ID_ANY)
        line.SetBackgroundColour(wx.Colour(*w_fg_color_0))
        grid_sizer.Add(line, (3, 0), (1, 3), wx.EXPAND, 0)
        #print(f"Top panel size: {panel.GetSize()}")
        return panel

    def _panel_bot(self, arg_dict):
        panel = ScrolledPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        grid_sizer = wx.GridBagSizer(vgap=2, hgap=2)
        sizer.Add(grid_sizer, 0, wx.CENTER | wx.ALL, 6)
        w_fg_color_0 = arg_dict['w_fg_color_0']
        w_fg_color_1 = arg_dict['w_fg_color_1']
        widget_labels = arg_dict['widget_labels']

        for idx, label in enumerate(widget_labels):
            label = label.replace(r'\n', '\n')
            widget = wx.StaticText(panel, wx.ID_ANY, label)

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

        self.Bind(wx.EVT_SIZE, self.resize_closure(panel, grid_sizer,
                                                   arg_dict['panel_top']))
        #print(f"Bottom panel size: {panel.GetSize()}")
        arg_dict['panel'] = panel
        arg_dict['grid_sizer'] = grid_sizer
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
                    if (not isinstance(value, list)
                        or value[0] != 'StaticText'): continue
                    args = self._find_dict(value).get('args', [])
                    widget_labels.append(args[2])

                arg_dict['widget_labels'] = widget_labels
                self._create_widgets(arg_dict)
            else:
                self._destroy_panel(arg_dict.get('panel'),
                                    arg_dict.get('parent_sizer'))

        return get_selection

    def _create_widgets(self, arg_dict):
        parent_sizer = arg_dict['parent_sizer']
        panel = arg_dict.get('panel')
        # Destroy previous panel if it exists.
        self._destroy_panel(panel, parent_sizer)
        # Create new panel.
        panel = self._panel_bot(arg_dict)
        parent_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 6)
        self._setup_sizer_height_correctly(arg_dict['grid_sizer'])
        wx.CallLater(100, panel.SetupScrolling, rate_x=10, rate_y=10)

    def _destroy_panel(self, panel, parent_sizer):
        if panel and parent_sizer:
            parent_sizer.Remove(1)
            panel.Destroy()
            parent_sizer.Layout()

    def add_closuer(self, arg_dict):
        def add_button(event):
            grid_sizer = arg_dict.get('grid_sizer')

            if grid_sizer:
                row_count = grid_sizer.GetRows()
                print(f"Num of rows: {row_count}")
                print(arg_dict['widget_labels'])

        return add_button

    def resize_closure(self, panel, grid_sizer, panel_top):
        def on_size_change(event):
            width, height = grid_sizer.GetMinSize()
            tw, th = panel_top.GetSize()
            height += self.parent.statusbar_size[1]
            panel.SetSizeHints(tw, height)
            mw, mh = self.GetSize()
            bw, bh = panel.GetSize()
            bh = mh - th
            panel.SetSize(bw, bh)
            panel.Refresh()
            ## print(f"----------\nBottom Panel (SetSizeHints): {(tw, height)}")
            ## print(f"Main Panel (GetSize): {self.GetSize()}")
            ## print(f"Top Panel (GetSize): {panel_top.GetSize()}")
            ## print(f"Bottom Panel (GetSize): {panel.GetSize()}")
            ## print(f"Bottom Panel (SetSize): {(bw, bh)}")

        return on_size_change

    def _find_dict(self, value):
        for item in value:
            if isinstance(item, dict):
                break
            else:
                item = {}

        return item

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
