# -*- coding: utf-8 -*-
#
# src/main_frame.py
#
__docformat__ = "restructuredtext en"

from collections import OrderedDict
from pprint import pprint # *** TODO *** Remove later

import wx

from .config import BaseSystemData
from .panel_factory import PanelFactory, BasePanel
from .tools import ShortCuts


class MenuBar:
    """
    Dynamic menu bar.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__item_map = OrderedDict([
            ('file', ['&File', 'ALT+F', wx.Menu(), OrderedDict([
                ('open', [wx.ID_OPEN, "&Open\tCTRL+O",
                          "Open TOML configuration file.",
                          'file_picker', False]),
                ('save', [wx.ID_SAVE, "&Save\tCTRL+S",
                          "Save TOML configuration file.",
                          'file_save', False]),
                ('save_as', [wx.ID_SAVEAS, "&Save As\tCTRL+A",
                             "Save a TOML configuration file with a "
                             "different name.", 'file_save_as', False]),
                ('separator_0', None),
                ('close', [wx.ID_CLOSE, "&Close\tCTRL+C",
                           "Close the current frame.", 'file_close', True]),
                ('quit', [wx.ID_EXIT, "&Quit\tCTRL+Q",
                          "Quit this application.", 'app_quit', True]),
                ])]),
            ('edit', ["&Edit", 'ALT+E', wx.Menu(), OrderedDict([
                ('conf', [wx.ID_ANY, "&Configuration\tCTRL+F",
                          "Edit basic organization configuration.",
                          'edit_config', True]),
                ('budget', [wx.ID_ANY, "&Budget\tCTRL+B",
                            "Edit yearly budget.", 'edit_budget', True]),
                ('hide', [wx.ID_ANY, "&Close All\tCTRL+L",
                          "Close all panels.", 'edit_hide_all', True]),
                ])]),
            ('tools', ['&Tools', 'ALT+T', wx.Menu(), OrderedDict([
                ('short', [wx.ID_ANY, "&Short Cuts\tCTRL+H",
                           "Show the short cut screen.",
                           'tool_short_cuts', True]),
                ])]),
            ('help', ['&Help', 'ALT+H', wx.Menu(), OrderedDict([
                ('manual', [wx.ID_ANY, "&Manual\tCTRL+M",
                            "Open an online manual.", 'app_manual', True]),
                ('releases', [wx.ID_ANY, "&Releases\tCTRL+R",
                            "Open the online release page.",
                              'app_manual', True]),
                ('about', [wx.ID_ABOUT, "&About\tCTRL+T",
                           "Display the about screen.", 'app_about', True]),
                ])]),
            ])
        self.create_menu()

    def create_menu(self):
        bind_map = {}
        self.menubar = wx.MenuBar()

        for drop in self.__item_map:
            used = 0
            item, sc, obj, inner = self.__item_map[drop]
            self.menubar.Append(obj, item)

            for key in inner:
                if 'separator' in key:
                    if used != 0: obj.AppendSeparator()
                    continue

                id, item, help, callback, display = inner[key]

                if display:
                    menu_item =  obj.Append(id, item, help)
                    bind_map.setdefault(
                        key, [getattr(self, callback), menu_item])
                    used += 1

        [self.Bind(event=wx.EVT_MENU, handler=handler, source=source)
         for handler, source in bind_map.values()]
        self.SetMenuBar(self.menubar)

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
        panel = self.panels['config']
        panel.Show()
        self.parent.SetTitle(panel.title)

    def edit_budget(self, event):
        self._hide_all_panels()
        panel = self.panels['budget']
        panel.Show()
        self.parent.SetTitle(panel.title)



    def edit_hide_all(self, event):
        self._hide_all_panels()

    def _hide_all_panels(self):
        [obj.Hide() for obj in self.panels.values() if obj.IsShown()]
        self.SetTitle(self.title)

    def tool_short_cuts(self, event):
        sc = ShortCuts(self.parent)



    def app_manual(self, event):
        pass

    def app_releases(self, event):
        pass

    def app_about(self, event):
        pass

    def load_file(self, fullpath):
        pass


class MainFrame(MenuBar, wx.Frame):
    """
    The main frame of the application.
    """
    title = 'Main Screen'

    def __init__(self, parent=None,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.Size(800, 800),
                 style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL):
        super().__init__(parent, id=id, pos=pos, size=size, style=style)
        self.SetTitle(self.title)
        self.SetBackgroundColour(wx.Colour(128, 128, 128))
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        box_sizer = wx.BoxSizer(wx.VERTICAL)

        # Status Bar
        status_widths = [-1, -1, -1, -1]
        frame_statusbar = self.CreateStatusBar(len(status_widths),
                                               wx.STB_DEFAULT_STYLE)
        frame_statusbar.SetStatusWidths(status_widths)
        # statusbar fields
        self.frame_statusbar_fields = {'temp0': "frame_statusbar_0",
                                       'temp1': "frame_statusbar_1"}

        for idx, key in enumerate(self.frame_statusbar_fields.keys()):
            status = self.frame_statusbar_fields.get(key)
            frame_statusbar.SetStatusText(status, idx)
        # End Status Bar

        self.SetSizer(box_sizer)
        self.Layout()
        self.Center(wx.BOTH)
        self.__panel_classes = {}

        sf = PanelFactory()
        sf.parse()
        panel_names = sf.class_name_keys
        print("Panal Names:") # *** TODO *** Remove later
        pprint(panel_names)   # *** TODO *** Remove later

        for panel in panel_names:
            code = sf.get_panel_code(panel)

            if code:
                print(code)   # *** TODO *** Remove later
                exec(code)
                class_name = sf.get_class_name(panel)
                self.__panel_classes[panel] = eval(class_name)(self, size=size)

    @property
    def panels(self):
        return self.__panel_classes

    @property
    def parent(self):
        return self

    def add_status(self, key, status):
        self.frame_statusbar_fields[key] = status

    def remove_status(self, key):
        self.frame_statusbar_fields.pop(key, None)
