# -*- coding: utf-8 -*-
#
# src/main_frame.py
#
__docformat__ = "restructuredtext en"

import asyncio
import logging

from .config import TomlAppConfig
from .database import Database
from .utilities import StoreObjects

import wx

from .menu import MenuBar
# BaseGenerated is used by the factory created classes.
from .bases import BaseGenerated, version
from .panel_factory import PanelFactory

try: # pragma: no cover
    from ctypes import windll
    # Only exists on Windows.
    myappid = f"tetrasys.nc-bookkeeper.{version()}"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


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
        self.__box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.setup_resize_event()

        # Status Bar
        status_widths = (-1,)
        self._statusbar = self.CreateStatusBar(len(status_widths),
                                               wx.STB_DEFAULT_STYLE)
        self._statusbar.SetStatusWidths(status_widths)
        size = (500, 800)
        self.set_size(size)
        self.SetSizer(self.__box_sizer)
        self.Layout()
        self.SetAutoLayout(True)
        #self.Center()
        sf = PanelFactory()
        sf.parse()

        for panel in sf.class_name_keys:
            code = sf.get_panel_code(panel)

            if code:
                #print(code)   # *** TODO *** Remove later
                exec(code)
                class_name = sf.get_class_name(panel)
                self.__panel_classes[panel] = eval(class_name)(self)

        self.create_menu()
        StoreObjects().set_object(self.__class__.__name__, self)
        asyncio.run(self.start())

    async def start(self):
        """
        Check that the db has the Organization Information. If not start
        the 'Organization Information' panel.
        """
        db = Database()
        self._log.info("Create the database if it does not exist.")
        await db.create_db()
        self._log.info("Populating all panels.")
        await db.populate_panels()

        if not db.has_org_info_data:
            self._log.info("The Organization Information has not been "
                           "entered yet.")
            # *** TODO *** Display a panel that offers the user ability
            #              to add or change fields.
            self.edit_config(None)
        elif not db.has_budget_data:
            self._log.info("The budget data has not been entered yet.")
            # *** TODO *** Display a panel that offers the user ability
            #              to add or change fields.
            self.edit_budget(None)
        ## elif not db.has_month_data:
        ##     self._log.info("The month data has not been entered yet.")
        ##     # *** TODO *** Display a panel that offers the user ability
        ##     #              to add or change fields.
        ##     self.edit_month(None)

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer_closure(db), self._timer)
        seconds = 1000*10
        self._log.info("Checking panel dirty flag every %s seconds.",
                       seconds/1000)
        self._timer.Start(seconds)

    def on_timer_closure(self, db):
        def on_timer(event):
            for name, panel in self.panels.items():
                if panel.dirty:
                    asyncio.run(db.save_to_database(name, panel))
                    self._log.debug("Checking '%s' for changes, dirty "
                                    "flag '%s'", name, panel.dirty)

        return on_timer

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
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle)

    def on_size(self, event):
        event.Skip()
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

    def statusbar_warning(self, value):
        self.__set_status(value, 'yellow')
    statusbar_warning = property(None, statusbar_warning)

    def statusbar_error(self, value):
        self.__set_status(value, 'pink')
    statusbar_error = property(None, statusbar_error)

    def __set_status(self, value, color):
        self._statusbar.SetStatusText(value, 0)
        bg_color = self._statusbar.GetBackgroundColour()
        fg_color = self._statusbar.GetForegroundColour()
        self._statusbar.SetBackgroundColour(color)
        self._statusbar.SetForegroundColour('black')
        # Wait for 10 seconds before resetting the message.
        wx.CallLater(10000, self.__reset_status, bg_color, fg_color)

    def __reset_status(self, bg_color, fg_color):
        self._statusbar.SetStatusText("", 0)
        self._statusbar.SetBackgroundColour(bg_color)
        self._statusbar.SetForegroundColour(fg_color)

    @property
    def statusbar_size(self):
        return self._statusbar.GetSize()

    def add_status(self, key, status):
        self.statusbar_fields[key] = status

    def remove_status(self, key):
        self.statusbar_fields.pop(key, None)
