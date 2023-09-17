# -*- coding: utf-8 -*-
#
# src/main_frame.py
#
__docformat__ = "restructuredtext en"

import logging
from collections import OrderedDict
from pprint import pprint # *** TODO *** Remove later

import wx
from wx.lib.inspection import InspectionTool

from .bases import BaseGenerated
from .config import TomlAppConfig
from .panel_factory import PanelFactory
from .tools import ShortCuts, FieldEdit
from .settings import Paths


class MenuBar:
    """
    Dynamic menu bar.
    """
    __short_cut = None
    __inspection = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                          ('conf', [wx.ID_ANY, "&Configuration\tCTRL+F",
                                    "Edit basic organization configuration.",
                                    'edit_config', None, True, None]),
                          ('budget', [wx.ID_ANY, "&Budget\tCTRL+B",
                                      "Edit yearly budget.",
                                      'edit_budget', None, True, None]),
                          ('month', [wx.ID_ANY, "&Month\tCTRL+M",
                                      "Edit monthy data.",
                                      'edit_month', None, True, None]),
                          ('hide', [wx.ID_ANY, "&Close All\tCTRL+L",
                                    "Close all panels.",
                                    'edit_hide_all', None, True, None]),
                          ])]),
            ('reports', [None, '&Reports\tALT+R', "Print reports.",
                         None, wx.Menu(), True, OrderedDict([
                             ('budget', [wx.ID_ANY,
                                         "&Budget Worksheet\tCTRL+W",
                                         "Yearly budget report.",
                                         'report_budget', None, True, None]),
                             ])]),
            ('tools', [None, '&Tools\tALT+T',
                       "Various tool to help with productivity.",
                       None, wx.Menu(), True, OrderedDict([
                           ('short', [wx.ID_ANY, "&Short Cuts\tCTRL+H",
                                      "Show the short cut screen.",
                                      'tool_short_cuts', None, True, None]),
                           ('inspection', [wx.ID_ANY, "&Inspection\tCTRL+I",
                                           "Show the WX inspection tool.",
                                           'tool_inspection', None,
                                           True, None]),
                           ('fields', [wx.ID_ANY,
                                       "&Edit Fields\tCTRL+D",
                                       "Edit fields on various screens.",
                                       'tool_fields', None, True, None]),
                           ('separator_1', []),
                           ('reset', [wx.ID_ANY, "Reset",
                                      "Reset some default settings.",
                                      None, wx.Menu(), True, OrderedDict([
                                          ('window_size', [
                                              wx.ID_ANY,
                                              "&Window Size\tALT+W",
                                              "Reset default window size.",
                                              'tool_reset_window',
                                              None, True, None]),
                                          ])]),
                           ])]),
            ('settings', [None, '&Settings\tALT+S', "Application settings",
                          None, wx.Menu(), True, OrderedDict([
                              ('paths', [wx.ID_ANY,
                                         "&Application Paths\tCTRL+P",
                                         "Show the application paths.",
                                         'settings_paths', None, True, None]),
                              ])]),
            ('help', [None, '&Help\tALT+H', "Documentation",
                      None, wx.Menu(), True, OrderedDict([
                          ('manual', [wx.ID_ANY, "&Manual\tCTRL+N",
                                      "Open an online manual.",
                                      'app_manual', None, True, None]),
                          ('releases', [wx.ID_ANY, "&Releases\tCTRL+R",
                                        "Open the online release page.",
                                        'app_manual', None, True, None]),
                          ('about', [wx.ID_ABOUT, "&About\tCTRL+T",
                                     "Display the about screen.",
                                     'app_about', None, True, None]),
                          ])]),
            ])
        self.create_menu()

    def create_menu(self):
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
        menu = wx.MenuBar()
        self.__recurse_menu(self.__item_map, bind_map, menu)
        [self.Bind(event=wx.EVT_MENU, handler=handler, source=source)
         for handler, source in bind_map.values()]
        self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.mouse_over)
        self.SetMenuBar(menu)

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
                    elif id and nk and cb and not mo and tf and not od:
                        # Normal menu item.
                        menu_item = menu.Append(id, nk, disc)
                        bind_map.setdefault(nk, [getattr(self, cb), menu_item])
                        used += 1
                    elif id and nk and not cb and mo and tf and od:
                        # Submenu
                        menu_item = menu.Append(id, nk, mo, disc)
                        bind_map.setdefault(nk, [None, menu_item])
                        used += 1
                        self.__recurse_menu(od, bind_map, menu=mo)
            except Exception as e:
                self._log.error("One of the menu items failed: %s, %s",
                                values, menu, exc_info=True)

    @property
    def menu_items(self):
        return self.__item_map

    def menu_item_toggle(self, drop, name):
        inner = self.item_map.get(drop)[2]
        inner[name][-1] = False if inner[name][-1] else True
        return inner[name][-1]

    def menu_item_state(self, drop, name):
        inner = self.item_map.get(drop)[2]
        return inner[name][-1]

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
        self._hide_all_panels()
        self.panel = self.panels['configuration']

        #self.menu_item_toggle(drop, name)

        self._set_panel()

    def edit_budget(self, event):
        self._hide_all_panels()
        self.panel = self.panels['budget']

        #self.menu_item_toggle(drop, name)

        self._set_panel()

    def edit_month(self, event):
        self._hide_all_panels()
        self.panel = self.panels['month']

        #self.menu_item_toggle(drop, name)

        self._set_panel()

    def _set_panel(self):
        self.sizer.Detach(self.panel)
        size = self.parent.GetSize()
        self.panel.SetSize(*size)
        self.sizer.Add(self.panel, 1, wx.EXPAND)
        self.panel.Show()
        self.parent.SetTitle(self.panel.title)

        if self.__short_cut:
            self._update_short_cuts(self.panel.background_color)

    def edit_hide_all(self, event):
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

        self._hide_all_panels()
        self.panel = self.panels['fields']
        self._set_panel()

    def settings_paths(self, event):
        if 'paths' not in self.panels:
            self.set_panel('paths', Paths(self.parent))

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


class MainFrame(MenuBar, wx.Frame):
    """
    The main frame of the application.
    """
    title = 'Main Screen'
    __active_panel = None
    __panel_classes = {}

    def __init__(self, parent=None, id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL):
        self._tac = TomlAppConfig()
        self._log = logging.getLogger(self._tac.logger_name)
        super().__init__(parent, id=id, pos=pos, style=style)
        self.SetTitle(self.title)
        self.parent_bg_color = (128, 128, 128)
        self.SetBackgroundColour(wx.Colour(*self.parent_bg_color))
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        #self.SetIcon(wx.Icon("icons/wxwin.ico"))
        self.__box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.setup_resize_event()

        # Status Bar
        status_widths = [-1, -1]
        self._statusbar = self.CreateStatusBar(len(status_widths),
                                               wx.STB_DEFAULT_STYLE)
        self._statusbar.SetStatusWidths(status_widths)
        # statusbar fields
        ## self.statusbar_fields = {
        ##     'temp0': "statusbar_0",
        ##     'temp1': "statusbar_1"
        ##     }

        ## for idx, key in enumerate(self.statusbar_fields.keys()):
        ##     status = self.statusbar_fields.get(key)
        ##     statusbar.SetStatusText(status, idx)
        # End Status Bar

        size = (500, 800)
        self.set_size(size)
        self.SetSizer(self.__box_sizer)
        self.Layout()
        self.SetAutoLayout(True)
        #self.Center()
        sf = PanelFactory()
        sf.parse()
        panel_names = sf.class_name_keys

        for panel in panel_names:
            code = sf.get_panel_code(panel)

            if code:
                #print(code)   # *** TODO *** Remove later
                exec(code)
                class_name = sf.get_class_name(panel)
                self.__panel_classes[panel] = eval(class_name)(self)

    def set_size(self, size, key='size'):
        """
        Sets the size of the Frame.

        :param size: The size to set as (width, height).
        :type size: Tuple or List
        :param key: The key in the TOML config file. Can be 'size' or
                    'default'. The default is 'size'.
        :type key: str
        """
        value = self._tac.get_value('app_size', key)
        self.SetSize(wx.Size(value if value else size))

    def setup_resize_event(self):
        self.__resized = False
        self.Bind(wx.EVT_SIZE,self.on_size)
        self.Bind(wx.EVT_IDLE,self.on_idle)

    def on_size(self, event):
        self.__resized = True

    def on_idle(self, event):
        if self.__resized:
            width, height = self.GetSize()
            self._tac.update_app_config('app_size', 'size', (width, height))
            self.__resized = False

            for panel in self.panels.values():
                panel.SetSize((width, height))
                height = height - self.parent.statusbar_size[1]
                panel.SetSizeHints(width, height)
                panel.Layout()

    @property
    def panels(self):
        return self.__panel_classes

    def set_panel(self, name, panel):
        self.__panel_classes[name] = panel

    @property
    def panel(self):
        return self.__active_panel

    @panel.setter
    def panel(self, value):
        self.__active_panel = value

    @property
    def parent(self):
        return self

    @property
    def sizer(self):
        return self.__box_sizer

    @property
    def statusbar_size(self):
        return self._statusbar.GetSize()

    def add_status(self, key, status):
        self.statusbar_fields[key] = status

    def remove_status(self, key):
        self.statusbar_fields.pop(key, None)
