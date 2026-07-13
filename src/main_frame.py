# -*- coding: utf-8 -*-
#
# src/main_frame.py
#
__docformat__ = "restructuredtext en"

import os
import asyncio
import logging

from .config import TomlAppConfig
from .utilities import StoreObjects, AsyncRunner
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

    def __init__(self, parent=None, id=wx.ID_ANY,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
                 size=(500, 800), options=None, *args, **kwargs):
        super().__init__(parent, id=id, style=style)
        self.args = args
        self.kwargs = kwargs
        self.options = options
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

        # Store current object
        StoreObjects().set_object(self.__class__.__name__, self)
        # Create and store async runner
        ar = AsyncRunner()
        StoreObjects().set_object(ar.__class__.__name__, ar)

        # Create and store the Database
        if self._tac.config_type == 'bahai':
            from .bahai_database import Database
        else:  # generic
            pass

        self.db = Database()
        StoreObjects().set_object(self.db.__class__.__name__, self.db)
        asyncio.run(self.start(), debug=options.debug)

    async def start(self):
        """
        Check that the db has the Organization Information. If not start
        the 'Organization Information' panel.
        """
        # Read panel config file and create panels.
        self.create_menu()
        await self.db.create_db()

        if not self.db.cache.has_cache:
            await self.db.cache.load()

        self.load_panels()
        await self.db.populate_panels()

        # *** TODO *** Display a panel that offers the user the ability
        #              to add or change fields.
        if not self.db.has_org_info_data:
            self._log.info("The Organization data needs to be entered.")
            self.edit_config(None)
        elif not self.db.has_budget_data:
            self._log.info("The budget data needs to be entered.")
            self.edit_budget(None)
        else:
            self.edit_monthly(None)
            #self.edit_ledger_data(None)

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer_closure(), self._timer)
        seconds = 1000*5  # = 5 seconds
        self._log.info("Checking panel dirty flag every %s seconds.",
                       seconds/1000)
        self._timer.Start(seconds)

    def on_timer_closure(self):
        def do_save(name, panel):
            self._log.debug("Checking '%s' for changes.", name)
            error = asyncio.run(self.db.save_to_database(name, panel),
                                debug=self.options.debug)
            panel.dirty = False

            if error is None:
                c_name = name.capitalize()
                self.statusbar_message = f"Finished saving {c_name} data."
            else:
                self.statusbar_warning = error
                # *** TODO *** Reset to default all values in panel.

        def on_timer(event):
            for name, panel in self.panels.items():
                if panel.dirty:
                    if name in ('organization', 'budget', 'monthly', 'ledger'):
                        match name:
                            case 'organization':
                                data = self.db.dp.organization_data
                            case 'budget':
                                data = self.db.dp.budget_data
                            case 'monthly':
                                data = self.db.dp.monthly_data
                            case 'ledger':
                                data = {}  # *** TODO *** Figure this out

                        if panel.save:
                            panel.save = False
                            do_save(name, panel)
                            panel.dirty = False
                        elif panel.cancel:
                            panel.cancel = False
                            self.db.populate_panel_values(name, panel, data)
                            panel.dirty = False
                            c_name = name.capitalize()
                            self.statusbar_message = (
                                f"Finished restoring {c_name} data.")
                    else:
                        self.statusbar_message = f"Saving {name} data."
                        do_save(name, panel)

        return on_timer

    def load_panels(self):
        sf = PanelFactory()
        sf.parse()

        for panel in sf.class_name_keys:
            code = sf.get_panel_code(panel)

            if code:
                # Write the code files to the cache, only used for debugging.
                if self.options.file_dump:
                    filename = f"{panel}.py"
                    dir = self._tac.cached_factory_dir
                    pathname = os.path.join(dir, filename)

                    with open(pathname, 'w') as f:
                        f.write(code)

                # Create the panels.
                exec(code, globals())
                class_name = sf.get_class_name(panel)
                self.__panel_classes[panel] = globals(
                    )[class_name](self.parent, *self.args, **self.kwargs)

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
    def panels(self) -> dict:
        return self.__panel_classes

    @panels.setter
    def panels(self, values: tuple) -> None:
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
        # Wait for 20 seconds before resetting the message.
        wx.CallLater(20000, self.__reset_status, default_color)

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
