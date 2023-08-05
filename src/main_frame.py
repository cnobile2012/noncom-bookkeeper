# -*- coding: utf-8 -*-
#
# src/main_frame.py
#
__docformat__ = "restructuredtext en"

import sys
from pprint import pprint

import wx

from .config import BaseSystemData
from src.panel_factory import PanelFactory, BasePanel


class MenuBar:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_menu()

    def create_menu(self):
        bind_map = {}
        self.menubar = wx.MenuBar()
        file_menu = wx.Menu()
        # Open TOML config file.
        load_item = file_menu.Append(wx.ID_OPEN, "&Open\tCTRL+O",
                                     "Open TOML configuration file.")
        bind_map.setdefault('open', [self.file_picker, load_item])
        # Save TOML config file.
        save_item = file_menu.Append(wx.ID_SAVE, "&Save\tCTRL+S",
                                     "Save TOML configuration file.")
        bind_map.setdefault('save', [self.file_save, save_item])
        # Save As TOML config file.
        save_as_item = file_menu.Append(
            wx.ID_SAVEAS, "Save As\tCTRL+A",
            "Save as a different name a TONL configuration file.")
        bind_map.setdefault('save_as', [self.file_save_as, save_as_item])
        file_menu.AppendSeparator()
        # Close current frame.
        close_item = file_menu.Append(wx.ID_CLOSE, "&Close\tCTRL+C",
                                      "Close the current frame.")
        bind_map.setdefault('close', [self.file_close, close_item])
        # Exit application.
        exit_item = file_menu.Append(wx.ID_EXIT, "&Exit\tCTRL+E",
                                     "Exit this application.")
        bind_map.setdefault('exit', [self.app_exit, exit_item])
        self.menubar.Append(file_menu, "&File")
        edit_menu = wx.Menu()
        # Edit configuration.
        conf_item = edit_menu.Append(wx.ID_ANY, "&Configuration\tCTRL+F",
                                     "Edit basic organization configuration.")
        bind_map.setdefault('config', [self.edit_config, conf_item])
        # Edit yearly budget.
        budget_item = edit_menu.Append(wx.ID_ANY, "&Budget\tCTRL+B",
                                       "Edit yearly budget.")
        bind_map.setdefault('budget', [self.edit_budget, budget_item])
        # Hide all panels.
        hide_item = edit_menu.Append(wx.ID_ANY, "&Close All\tCTRL+L",
                                     "Close all panels.")
        bind_map.setdefault('hide', [self.edit_hide_all, hide_item])

        self.menubar.Append(edit_menu, "&Edit")
        tool_menu = wx.Menu()
        # Show all short cuts.
        short_item = tool_menu.Append(wx.ID_ANY, "&Short Cuts\tCTRL+H",
                                      "Show the short cut screen.")
        bind_map.setdefault('short', [self.tool_short_cuts, short_item])

        self.menubar.Append(tool_menu, "&Tools")
        help_menu = wx.Menu()
        # Open online manual.
        manual_item = help_menu.Append(wx.ID_ANY, "&Manual\tCTRL+M",
                                       "Open an online manual.")
        bind_map.setdefault('manual', [self.app_manual, manual_item])
        # Open online release schedule.
        releases_item = help_menu.Append(wx.ID_ANY, "&Releases\tCTRL+R",
                                         "Open the online release page.")
        bind_map.setdefault('releases', [self.app_releases, releases_item])
        # Open an about screen.
        about_item = help_menu.Append(wx.ID_ABOUT, "&About\tCTRL+B",
                                      "Display the about screen.")
        bind_map.setdefault('about', [self.app_about, about_item])
        self.menubar.Append(help_menu, "&Help")
        [self.Bind(event=wx.EVT_MENU, handler=handler, source=source)
         for handler, source in bind_map.values()]
        self.SetMenuBar(self.menubar)

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

    def app_exit(self, event):
        # *** TODO *** We need to check for unsaved files.
        sys.exit(0)

    def edit_config(self, event):
        self._hide_all_panels()
        self.panels['config'].Show()

    def edit_budget(self, event):
        self._hide_all_panels()
        self.panels['budget'].Show()



    def edit_hide_all(self, event):
        self._hide_all_panels()

    def _hide_all_panels(self):
        [obj.Hide() for obj in self.panels.values() if obj.IsShown()]

    def tool_short_cuts(self, event):
        pass


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

    def __init__(self, parent=None,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.Size(800, 800),
                 style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL):
        super().__init__(parent, id=id, pos=pos, size=size, style=style)
        self.SetTitle('Main Screen')
        self.SetBackgroundColour(wx.Colour(128, 128, 128))
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        box_sizer = wx.BoxSizer(wx.VERTICAL)
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
