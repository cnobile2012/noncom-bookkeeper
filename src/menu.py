# -*- coding: utf-8 -*-
#
# src/menu.py
#
__docformat__ = "restructuredtext en"

from collections import OrderedDict

from .config import TomlAppConfig, TomlMetaData

import wx
from wx.lib.inspection import InspectionTool

from .tools import ShortCuts, FieldEdit
from .settings import Paths


class MenuBar:
    """
    Dynamic menu bar.
    """
    _tmd = TomlMetaData()
    __short_cut = None
    __inspection = None
    _current_menus = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_menu(self):
        names = [panel[0] for panel in self._tmd.panels]

        self.__item_map = OrderedDict([
            ('file', [None, '&File\tALT+F', "File and App operations.",
                      None, wx.Menu(), True, OrderedDict([
                          ('open', [wx.ID_OPEN, '&Open\tCTRL+O',
                                    "Open TOML configuration file.",
                                    'file_picker', None,  False, None]),
                          ('save', [wx.ID_SAVE, "&Save\tCTRL+S",
                                    "Save TOML configuration file.",
                                    'file_save', None, False, None]),
                          ('save_as', [wx.ID_SAVEAS, "&Save As\tCTRL+A",
                                       "Save a TOML configuration file with "
                                       "a different name.", 'file_save_as',
                                       None, False, None]),
                          ('separator_0', []),
                          ('close', [wx.ID_CLOSE, "&Close\tCTRL+C",
                                     "Close the current frame.",
                                     'file_close', None, True, None]),
                          ('quit', [wx.ID_EXIT, "&Quit\tCTRL+Q",
                                    "Quit this application.",
                                    'app_quit', None, True, None]),
                          ])]),
            ('edit', [None, '&Edit\tALT+E', "Screen editing operations.",
                      None, wx.Menu(), True, OrderedDict([
                          ('conf', [200, f"&{names[0]}\tCTRL+F",
                                    "Edit basic organization configuration.",
                                    'edit_config', None, True, None]),
                          ('budget', [201, f"&{names[1]}\tCTRL+B",
                                      "Edit yearly budget.",
                                      'edit_budget', None, True, None]),
                          ('month', [202, f"&{names[2]}\tCTRL+M",
                                     "Edit monthy data.",
                                     'edit_month', None, True, None]),
                          ('fiscal', [203, f"&{names[3]}\tCTRL+O",
                                      "Choose Fiscal Year",
                                      'choose_fiscal_year', None, True, None]),
                          ('hide', [204, "&Close All\tCTRL+L",
                                    "Close all panels.",
                                    'edit_hide_all', None, True, None]),
                          ])]),
            ('reports', [None, '&Reports\tALT+R', "Print reports.",
                         None, wx.Menu(), True, OrderedDict([
                             ('budget', [300, "&Budget Worksheet\tCTRL+W",
                                         "Yearly budget report.",
                                         'report_budget', None, True, None]),
                             ])]),
            ('tools', [None, '&Tools\tALT+T',
                       "Various tool to help with productivity.",
                       None, wx.Menu(), True, OrderedDict([
                           ('short', [400, "&Short Cuts\tCTRL+H",
                                      "Show the short cut screen.",
                                      'tool_short_cuts', None, True, None]),
                           ('inspection', [401, "&Inspection\tCTRL+I",
                                           "Show the WX inspection tool.",
                                           'tool_inspection', None,
                                           True, None]),
                           ('fields', [402, "&Edit Fields\tCTRL+D",
                                       "Edit fields on various screens.",
                                       'tool_fields', None, True, None]),
                           ('separator_1', []),
                           ('reset', [403, "Reset",
                                      "Reset some default settings.",
                                      None, wx.Menu(), True, OrderedDict([
                                          ('window_size', [
                                              4031, "&Window Size\tALT+W",
                                              "Reset default window size.",
                                              'tool_reset_window',
                                              None, True, None]),
                                          ])]),
                           ])]),
            ('settings', [None, '&Settings\tALT+S', "Application settings",
                          None, wx.Menu(), True, OrderedDict([
                              ('paths', [500, "&Application Paths\tCTRL+P",
                                         "Show the application paths.",
                                         'settings_paths', None, True, None]),
                              ])]),
            ('help', [None, '&Help\tALT+H', "Documentation",
                      None, wx.Menu(), True, OrderedDict([
                          ('manual', [600, "&Manual\tCTRL+N",
                                      "Open an online manual.",
                                      'app_manual', None, True, None]),
                          ('releases', [601, "&Releases\tCTRL+R",
                                        "Open the online release page.",
                                        'app_manual', None, True, None]),
                          ('about', [wx.ID_ABOUT, "&About\tCTRL+T",
                                     "Display the about screen.",
                                     'app_about', None, True, None]),
                          ])]),
            ])
        self._create_menu()

    def _create_menu(self):
        """
        Create a drop down menu based on the data structure below.
        <id|None>  = wx ID
        <name|key> = Name and key code.
        disc       = Description
        <cb|None>  = callback
        <mo|None>  = Menu object
        <t|f>      = True or False
        <od|None>  = OrderedDict

        OrderedDict([
            (item, [None, <name|key>, disc, None, mo, <t|f>, OrderedDict([
                (item, [id, <name|key>, disc, cb, None, <t|f>, None]),
                (seperator, []),
                (item, [id, <name|key>, disc, cb, mo, <t|f>, OrderedDict([
                    (item, [id, <name|key>, disc, cb, None, <t|f>, None]),
                    (item, [id, <name|key>, disc, cb, None, <t|f>, None]),
                ])]),
            ])]),
            (item, [None, <name|key>, disc, None, mo, <t|f>, OrderedDict([
                (item, [id, <name|key>, disc, cb, None, <t|f>, None]),
                (seperator, []),
                (item, [id, <name|key>, disc, cb, mo, <t|f>, OrderedDict([
                    (item, [id, <name|key>, disc, cb, None, <t|f>, None]),
                    (item, [id, <name|key>, disc, cb, None, <t|f>, None]),
                ])]),
            ])]),
        ])
        """
        bind_map = {}
        self._menu = wx.MenuBar()
        self.__recurse_menu(self.menu_items, bind_map, self._menu)
        [self.Bind(event=wx.EVT_MENU, handler=handler, source=source)
         for handler, source in bind_map.values()]
        # Puts menu info in status bar.
        self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.mouse_over)
        self.SetMenuBar(self._menu)

    def __recurse_menu(self, map_, bind_map, menu):
        for item in map_:
            used = 0
            values = map_[item]
            v_size = len(values)

            try:
                assert v_size in (0, 7), f"Item '{item}' is wrong length."

                if v_size == 0:
                    if used != 0: menu.AppendSeparator()
                else:
                    id, nk, disc, cb, mo, tf, od = values

                    if not id and nk and not cb and mo and tf and od:
                        # Top level menu item.
                        name, tab, key = nk.partition('\t')
                        menu.Append(mo, name)
                        self.__recurse_menu(od, bind_map, menu=mo)
                    elif id and nk and cb and not mo and not od:
                        # Normal menu item.
                        menu_item = menu.Append(id, nk, disc)
                        bind_map.setdefault(nk, [getattr(self, cb), menu_item])
                        used += 1
                        self._menu.Enable(id, tf)
                    elif id and nk and not cb and mo and od:
                        # Submenu
                        menu_item = menu.Append(id, nk, mo, disc)
                        bind_map.setdefault(nk, [None, menu_item])
                        used += 1
                        self._menu.Enable(id, tf)
                        self.__recurse_menu(od, bind_map, menu=mo)
            except Exception:
                self._log.error("One of the menu items failed: %s, %s",
                                values, menu, exc_info=True)

    @property
    def menu_items(self):
        return self.__item_map

    def change_menu_items(self, list_=()):
        """
        list_ = ((id, True|False), ...)
        """
        if list_:
            # Enable menu items.
            [self._menu.Enable(id, value) for id, value in list_]
            self.set_menu_item(list_)
        else:
            # Disable menu items.
            [self._menu.FindItem(id)[0].Enable(False)
             for id, values in self._current_menus]

            # Change menu_item states to False in menu_items.
            for item in self._current_menus:
                item[-1] = False

            self.set_menu_item(self._current_menus)

        self._current_menus = list_

    def set_menu_item(self, list_):
        list_size = len(list_)
        changed = []

        for items in self.menu_items.values():
            if items[-1]:
                for inner in items[-1].values():
                    for item in list_:
                        id, value = item

                        if id == inner[0]:
                            inner[-2] = value
                            changed.append(item)
                            break
                    if len(changed) == list_size:
                        break
            if len(changed) == list_size:
                break

        assert len(changed) == list_size, (
            f"Could not find all menu items found: '{changed}', "
            f"should be: '{list_}'.")

    def file_picker(self, event):
        title = "Open config file for editing."
        wildcard = "TOML Config File (*.toml)|*.toml"

        with wx.FileDialog(self, title, wildcard=wildcard,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() != wx.ID_CANCEL:
                # Proceed loading the file chosen by the user.
                fullpath = dlg.GetPath()

                try:
                    with open(fullpath, 'r') as file:
                        self.load_file(fullpath)
                except IOError:
                    wx.LogError("Cannot open file '%s'." % fullpath)

        dlg.Destroy()

    def file_save(self, event):
        pass

    def file_save_as(self, event):
        pass

    def file_close(self, event):
        pass

    def app_quit(self, event):
        # *** TODO *** We need to check for unsaved files.
        self.parent.Destroy()

    def edit_config(self, event):
        self.change_menu_items()
        self._hide_all_panels()
        self.panel = self.panels['organization']
        self._set_panel()

    def edit_budget(self, event):
        self.change_menu_items()
        self._hide_all_panels()
        self.panel = self.panels['budget']
        self._set_panel()

    def edit_month(self, event):
        self.change_menu_items()
        self._hide_all_panels()
        self.panel = self.panels['month']
        self._set_panel()

    def choose_fiscal_year(self, event):
        self.change_menu_items()
        self._hide_all_panels()
        self.panel = self.panels['fiscal']
        self._set_panel()

    def _set_panel(self):
        self.sizer.Detach(self.panel)
        size = self.parent.GetSize()
        self.panel.SetSize(*size)
        self.sizer.Add(self.panel, 1, wx.EXPAND)
        self.parent.SetTitle(self.panel.title)
        self.panel.Show()
        self.parent.Layout()

        if self.__short_cut:
            self._update_short_cuts(self.panel.background_color)

    def edit_hide_all(self, event):
        self.change_menu_items()
        self._hide_all_panels()
        self.panel = None

        if self.__short_cut:
            self._update_short_cuts(self.parent_bg_color)

    def _hide_all_panels(self):
        [obj.Hide() for obj in self.panels.values() if obj.IsShown()]
        self.SetTitle(self.title)

    def report_budget(self, event):
        pass

    def tool_short_cuts(self, event):
        if not self.__short_cut:
            self.__short_cut = ShortCuts(self.parent)

        if self.panel:
            color = self.panel.background_color
        else:
            color = self.parent_bg_color

        self._update_short_cuts(color)

    def _update_short_cuts(self, color):
        self.__short_cut.set_text(self.parent)
        self.__short_cut.SetBackgroundColour(wx.Colour(*color))

    def tool_inspection(self, event):
        if not self.__inspection:
            self.__inspection = InspectionTool()
            self.__inspection.Show()
        else:
            self.__inspection = None

    def tool_reset_window(self, event):
        tac = TomlAppConfig()
        size = tac.get_value('app_size', 'size')
        self.set_size(size, 'default')

    def tool_fields(self, event):
        if 'fields' not in self.panels:
            self.set_panel('fields', FieldEdit(self.parent))

        self.change_menu_items()
        self._hide_all_panels()
        self.panel = self.panels['fields']
        self.change_menu_items(([wx.ID_OPEN, True], [wx.ID_SAVE, True],
                                [wx.ID_SAVEAS, True],))
        self._set_panel()

    def settings_paths(self, event):
        if 'paths' not in self.panels:
            self.set_panel('paths', Paths(self.parent))

        self.change_menu_items()
        self._hide_all_panels()
        self.panel = self.panels['paths']
        self._set_panel()

    def app_manual(self, event):
        pass

    def app_releases(self, event):
        pass

    def app_about(self, event):
        pass

    def load_file(self, fullpath):
        pass

    def mouse_over(self, event):
        id = event.GetMenuId()
        item = self.GetMenuBar().FindItemById(id)

        if item:
            text = item.GetItemLabelText()
            help_ = item.GetHelp()

        event.Skip()
