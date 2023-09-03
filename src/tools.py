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


class ShortCuts(wx.Frame):
    """
    This dialog displayes the list of short cuts used in the menu bar.
    """
    short_cut_text = None

    def __init__(self, parent, title="Short Cuts"):
        super().__init__(parent, title=title)
        old_style = self.GetWindowStyle()
        self.SetWindowStyle(old_style | wx.STAY_ON_TOP)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.short_cut_text = wx.StaticText(self, wx.TE_MULTILINE, "")
        self.short_cut_text.SetForegroundColour(wx.Colour(50, 50, 204))
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


#class FieldEdit(wx.ScrolledWindow):
class FieldEdit(ScrolledPanel):
    """
    Add or remove fields in various panels.
    """
    tmd = TomlMetaData()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.SetScrollRate(10, 10)
        self.title = '''Add/Remove Fields'''
        self._bg_color = [232, 213, 149]
        w_bg_color = [222, 237, 230]
        w_fg_color_0 = [50, 50, 204]
        w_fg_color_1 = [197, 75, 108]
        self.SetBackgroundColour(wx.Colour(*self._bg_color))
        # Setup sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        grid_sizer = wx.GridBagSizer(vgap=2, hgap=2)
        sizer.Add(grid_sizer, 10, wx.CENTER | wx.ALL, 10)
        self.Bind(wx.EVT_SIZE, self.resize_closure(sizer), self)

        desc = wx.StaticText(self, wx.ID_ANY, self._description, style=0)
        desc.SetForegroundColour(wx.Colour(*w_fg_color_1))
        desc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(desc, (0, 0), (1, 2), wx.ALIGN_CENTER | wx.ALL, 6)

        edit_names = self._edit_names
        edit_names.insert(0, 'Choose the Page to Edit')
        combo_box = wx.ComboBox(self, wx.ID_ANY, value=edit_names[0],
                                choices=edit_names, style=wx.TE_READONLY)
        combo_box.SetBackgroundColour(wx.Colour(*w_bg_color))
        combo_box.SetForegroundColour(wx.Colour(*w_fg_color_0))
        combo_box.SetMinSize([196, 23])
        kwargs = {'edit_names': edit_names, 'grid_sizer': grid_sizer,
                  'w_fg_color_0': w_fg_color_0, 'w_fg_color_1': w_fg_color_1,
                  'y_pos': 4} # y_pos = number of hard coded fields.
        self.Bind(wx.EVT_COMBOBOX, self.selection_closure(**kwargs), combo_box)
        grid_sizer.Add(combo_box, (1, 0), (1, 1),
                       wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)

        field_desc = wx.StaticText(self, wx.ID_ANY,
                                   "Enter a new field name:", style=0)
        field_desc.SetForegroundColour(wx.Colour(*w_fg_color_0))
        field_desc.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD, 0, ''))
        grid_sizer.Add(field_desc, (2, 0), (1, 1), wx.LEFT | wx.ALL, 6)
        field_name = wx.TextCtrl(self,  wx.ID_ANY, "", style=wx.TE_LEFT)
        field_name.SetBackgroundColour(wx.Colour(*w_bg_color))
        field_name.SetForegroundColour(wx.Colour(*w_fg_color_0))
        field_name.SetMinSize((200, 23))
        grid_sizer.Add(field_name, (2, 1), (1, 1), wx.LEFT | wx.ALL, 6)

        line = wx.StaticLine(self, wx.ID_ANY)
        line.SetBackgroundColour(wx.Colour(*w_fg_color_0))
        grid_sizer.Add(line, (3, 0), (1, 2), wx.EXPAND | wx.BOTTOM, 2)

    def selection_closure(self, **kwargs):
        def get_selection(event):
            edit_names = kwargs['edit_names']
            chosen = event.GetString().lower()
            panel_labels = []

            if edit_names[0].lower() != chosen:
                items = self.tmd.panel_config.get(
                    chosen, {}).get('widgets', {})

                for value in items.values():
                    if (not isinstance(value, list)
                        or value[0] != 'StaticText'): continue
                    args = self._find_dict(value).get('args', [])
                    panel_labels.append(args[2])

                kwargs['panel_labels'] = panel_labels
                self._create_panel(**kwargs)
            else:
                self._remove_widgets(**kwargs)

        return get_selection

    def _create_panel(self, **kwargs):
        y_pos = kwargs['y_pos']
        grid_sizer = kwargs['grid_sizer']
        w_fg_color_0 = kwargs['w_fg_color_0']
        w_fg_color_1 = kwargs['w_fg_color_1']
        panel_labels = kwargs['panel_labels']
        self._remove_widgets(**kwargs)
        buff = StringIO()
        buff.write("def created_panel(self, grid_sizer):\n")

        for idx, label in enumerate(panel_labels):
            widget = f"widget_{idx:02}"
            buff.write(f"    {widget} = wx.StaticText(self, "
                       f"wx.ID_ANY, '''{label}''')\n")

            if label.endswith(':'):
                span = 1
                buff.write(f"    {widget}.SetFont(wx.Font(10, "
                           "wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, "
                           "wx.FONTWEIGHT_BOLD, 0, ''))\n")
                buff.write(f"    {widget}.SetForegroundColour(wx.Colour("
                           f"*{w_fg_color_0}))\n")
            else:
                span = 2
                buff.write(f"    {widget}.SetFont(wx.Font(12, "
                           "wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, "
                           "wx.FONTWEIGHT_BOLD, 0, ''))\n")
                buff.write(f"    {widget}.SetForegroundColour(wx.Colour("
                           f"*{w_fg_color_1}))\n")

            buff.write(f"    {widget}.SetMinSize((-1, 23))\n")
            buff.write(f"    grid_sizer.Add({widget}, ({idx + y_pos}, 0), "
                       f"(1, {span}), wx.ALIGN_CENTER_VERTICAL | wx.LEFT | "
                       "wx.RIGHT | wx.TOP, 6)\n")
            buff.write("    self.Layout()\n")

        code = buff.getvalue()
        buff.close()
        print(code) # *** TODO *** Remove later
        exec(code)
        FieldEdit.created_panel = locals().get('created_panel')
        self.created_panel(grid_sizer)

    def _remove_widgets(self, **kwargs):
        grid_sizer = kwargs['grid_sizer']
        y_pos = kwargs['y_pos']
        num_items = grid_sizer.GetItemCount()
        children = grid_sizer.GetChildren()

        for idx, child in enumerate(children):
            if idx >= y_pos:
                widget = child.GetWindow()
                widget.SetForegroundColour(wx.Colour(*self._bg_color))

        [grid_sizer.Remove(x) for x in range(num_items)[::-1] if x >= y_pos]

    def _find_dict(self, value):
        for item in value:
            if isinstance(item, dict):
                break
            else:
                item = {}

        return item

    def resize_closure(self, sizer):
        def on_size_change(event):
            #size = self.GetSize()
            #self.parent.SetSize(*size)
            # Fit child elements
            #sizer.FitInside(self.parent)
            # Resize scrolling
            #r = self.GetScrollRange(wx.VERTICAL)
            #self.Scroll(0, r)
            #self.SetupScrolling(scrollIntoView=True, scrollToTop=False)
            #self.Refresh()
            self.Layout()

        return on_size_change

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

        if item_list: # Just incase the list is empty.
            for item in item_list[-1].values():
                if item: # Just incase we find a separator.
                    name, tab, key = item[1].partition('\t')
                    if "Close All" in name: continue
                    item_names.append(name.lstrip('&'))

        item_names.sort()
        return item_names

    @property
    def background_color(self):
        return self._bg_color
