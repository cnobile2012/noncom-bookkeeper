# -*- coding: utf-8 -*-
#
# src/main_frame.py
#
__docformat__ = "restructuredtext en"

import os
import asyncio
import logging

from .config import TomlAppConfig
from .utilities import StoreObjects
from .custom_widgits import (BadiDatePickerCtrl, EVT_BADI_DATE_CHANGED,
                             ColorCheckBox, EVT_COLOR_CHECKBOX)

import wx
import wx.adv

from .menu import MenuBar
# BaseGenerated is used by the factory created classes.
from .bases import BaseGenerated, version
from .panel_factory import PanelFactory


try:  # pragma: no cover
    from ctypes import windll
    # Only exists on Windows.
    myappid = f"tetrasys.nc-bookkeeper.{version()}"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class MainFrame(wx.Frame, MenuBar):
    """
    The main frame of the application.
    """
    __panel_classes = {}
    #title = 'Main Screen'

    def __init__(self, parent=None, id=wx.ID_ANY,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
                 size=(500, 800), options=None, *args, **kwargs):
        super().__init__(parent, id=id, style=style)
        self._tac = TomlAppConfig()
        self._log = logging.getLogger(self._tac.logger_name)
        self.SetTitle(self._tmd.title)
        self.frame_bg_color = (128, 128, 128)  # Gray
        self.SetBackgroundColour(wx.Colour(*self.frame_bg_color))
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sizer = wx.BoxSizer(wx.VERTICAL)  # Frame sizer
        self.SetSizer(sizer)

        # All content panels switch within this panel.
        self.container = wx.Panel(self)
        self.container_sizer = wx.BoxSizer(wx.VERTICAL)
        self.container.SetSizer(self.container_sizer)
        sizer.Add(self.container, 1, wx.EXPAND)

        # Status Bar
        status_widths = (-1,)
        self._statusbar = self.CreateStatusBar(len(status_widths),
                                               wx.STB_DEFAULT_STYLE)
        self._statusbar.SetStatusWidths(status_widths)
        self.Layout()

        # Setup resizer
        self.set_size(size)
        self.setup_resize_event()

        StoreObjects().set_object(self.__class__.__name__, self)
        sf = PanelFactory()
        sf.parse()

        for panel in sf.class_name_keys:
            code = sf.get_panel_code(panel)

            if code:
                # Only used for debugging.
                if options.file_dump:  # Write the code files to the cache.
                    filename = f"{panel}.py"
                    pathname = os.path.join(self._tac.cached_factory_dir,
                                            filename)

                    with open(pathname, 'w') as f:
                        f.write(code)

                # Create the panels.
                exec(code, globals())
                class_name = sf.get_class_name(panel)
                self.__panel_classes[panel] = globals(
                    )[class_name](self.parent, *args, **kwargs)

        self.create_menu()
        self.options = options
        asyncio.run(self.start(), debug=options.debug)

    async def start(self):
        """
        Check that the db has the Organization Information. If not start
        the 'Organization Information' panel.
        """
        if self._tac.config_type == 'bahai':
            from .bahai_database import Database
        else:  # generic
            pass

        db = Database()
        StoreObjects().set_object(db.__class__.__name__, db)
        self._log.info("Create the database if it does not exist.")
        await db.create_db()
        await db.populate_panels()

        if not db.has_org_info_data:
            self._log.info("The Organization Information has not been "
                           "entered yet.")
            # *** TODO *** Display a panel that offers the user the ability
            #              to add or change fields.
            self.edit_config(None)
        elif not db.has_budget_data:
            self._log.info("The budget data has not been entered yet.")
            # *** TODO *** Display a panel that offers the user the ability
            #              to add or change fields.
            self.edit_budget(None)
        elif not db.has_month_data:
            self._log.info("The month data has not been entered yet.")
            # *** TODO *** Display a panel that offers the user the ability
            #              to add or change fields.
            self.edit_month(None)

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer_closure(db), self._timer)
        seconds = 1000*10  # 1000*10 = 10 seconds
        self._log.info("Checking panel dirty flag every %s seconds.",
                       seconds/1000)
        self._timer.Start(seconds)

    def on_timer_closure(self, db):
        def do_save(db, name, panel):
            error = asyncio.run(db.save_to_database(name, panel),
                                debug=self.options.debug)
            panel.dirty = False

            if error is None:
                c_name = name.capitalize()
                self.statusbar_message = f"Finished saving {c_name} data."
                self._log.debug("Checking '%s' for changes.", name)
            else:
                self.statusbar_warning = error
                # *** TODO *** Reset to default all values in panel.

        def on_timer(event):
            for name, panel in self.panels.items():
                if panel.dirty:
                    if name in ('organization',):
                        if panel.save:
                            panel.save = False
                            do_save(db, name, panel)
                        elif panel.cancel:
                            panel.cancel = False
                            db.populate_panel_values(
                                name, panel, db.organization_data)
                            panel.dirty = False
                            c_name = name.capitalize()
                            self.statusbar_message = (
                                f"Finished restoring {c_name} data.")
                    else:
                        do_save(db, name, panel)

        return on_timer

    def set_size(self, size, key='size'):
        """
        Sets the size of the Frame.

        :param tuple or list size: The size to set as (width, height).
        :param str key: The key in the TOML config file. Can be 'size' or
                        'default'. The default is 'size'.
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
                height = height - self.frame.statusbar_size[1]
                panel.SetSizeHints(width, height)

    @property
    def panels(self):
        return self.__panel_classes

    @panels.setter
    def panels(self, values):
        assert isinstance(values, tuple), ("The 'values' argument must be "
                                           f"a tuple, found {type(values)}.")
        #                    panel name   panel object
        self.__panel_classes[values[0]] = values[1]

    @property
    def frame(self):
        return self

    @property
    def parent(self):
        return self.container

    @property
    def sizer(self):
        return self.container_sizer

    def statusbar_warning(self, value):
        self.__set_status(value, 'yellow')
    statusbar_warning = property(None, statusbar_warning)

    def statusbar_error(self, value):
        self.__set_status(value, 'pink')
    statusbar_error = property(None, statusbar_error)

    def statusbar_message(self, value):
        self.__set_status(value, 'lightgreen')
    statusbar_message = property(None, statusbar_message)

    def __set_status(self, value, color):
        self._statusbar.SetStatusText(value, 0)
        default_color = wx.Colour('black')
        self._statusbar.SetBackgroundColour(color)
        self._statusbar.SetForegroundColour(default_color)
        # Wait for 10 seconds before resetting the message.
        wx.CallLater(15000, self.__reset_status, default_color)

    def __reset_status(self, default_color):
        self._statusbar.SetStatusText("", 0)
        self._statusbar.SetBackgroundColour(default_color)
        self._statusbar.SetForegroundColour(default_color)

    @property
    def statusbar_size(self):
        return self._statusbar.GetSize()

    def add_status(self, key, status):
        self.statusbar_fields[key] = status

    def remove_status(self, key):
        self.statusbar_fields.pop(key, None)
