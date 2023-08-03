# -*- coding: utf-8 -*-
#
# src/screen_factory.py
#
__docformat__ = "restructuredtext en"

import sys
from io import StringIO

from .config import BaseSystemData

import wx
import wx.adv
# https://pwwang.github.io/python-varname/
#from varname import varname, nameof


class MenuBar:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_menu()

    def create_menu(self):
        bind_map = {}
        self.menubar = wx.MenuBar()
        file_menu = wx.Menu()
        load_item = file_menu.Append(wx.ID_ANY, "Load\tCTRL+L",
                                     "Load something")
        bind_map.setdefault('load', [self.file_picker, load_item])

        save_item = file_menu.Append(wx.ID_ANY, "Save", "")
        bind_map.setdefault('save', [self.file_save, save_item])

        save_as_item = file_menu.Append(wx.ID_ANY, "Save As", "")
        bind_map.setdefault('save_as', [self.file_save_as, save_as_item])

        file_menu.AppendSeparator()
        close_item = file_menu.Append(wx.ID_ANY, "Close", "")
        bind_map.setdefault('close', [self.file_close, close_item])

        exit_item = file_menu.Append(wx.ID_ANY, "Exit", "")
        bind_map.setdefault('exit', [self.app_exit, exit_item])

        self.menubar.Append(file_menu, "&File")
        edit_menu = wx.Menu()
        self.menubar.Append(edit_menu, "&Edit")
        win_menu = wx.Menu()
        self.menubar.Append(win_menu, "&Windows")
        help_menu = wx.Menu()
        manual_item = help_menu.Append(wx.ID_ANY, "Manual", "")
        bind_map.setdefault('manual', [self.app_manual, manual_item])

        releases_item = help_menu.Append(wx.ID_ANY, "Releases", "")
        bind_map.setdefault('releases', [self.app_releases, releases_item])

        about_item = help_menu.Append(wx.ID_ANY, "About", "")
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

    def file_save(self, event):
        pass

    def file_save_as(self, event):
        pass

    def file_close(self, event):
        pass

    def app_exit(self, event):
        # *** TODO *** We need to check for unsaved files.
        sys.exit(0)

    def app_manual(self, event):
        pass

    def app_releases(self, event):
        pass

    def app_about(self, event):
        pass

    def load_file(self, fullpath):
        pass




class BaseFrame(MenuBar, wx.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(parent=None, **kwargs)
        self.panal_0 = wx.Panel(self)


class FrameFactory(BaseSystemData):
    """
    Parse the config data and create the frames.
    """
    frames = {}
    __class_names = {}

    def __init__(self):
        super().__init__()

    @property
    def class_name_keys(self):
        return self.__class_names.keys()

    def get_class_name(self, key):
        return self.__class_names.get(key)

    def parse(self):
        meta = self.config.get('meta')

        for frame in meta.get('frames'):
            try:
                self.setup_frame(frame)
            except Exception as e:
                self._log.critical("Critical error, cannot start application "
                                   "please contact the developer for help, %s",
                                   str(e), exc_info=True)
                # *** TODO *** This needs to be shown on the frame if detected.

        # *** TODO *** Remove later
        return self.frames[frame], self.__class_names

    def setup_frame(self, frame):
        class_name = f"{frame.capitalize()}Frame"
        self.__class_names[frame] = class_name
        frame_kwargs = self.config.get(frame, {}).get('meta')
        klass = StringIO()
        klass.write(f"class {class_name}(BaseFrame):\n")
        klass.write("    def __init__(self, *args, **kwargs):\n")
        klass.write("        super().__init__(*args, **kwargs)\n")
        # The line below permits us to grab a vairable dynamically.
        #klass.write("        local_vars = locals()\n")
        title = frame_kwargs.get('title')
        klass.write(f"        self.SetTitle('{title}')\n")
        self.bg_color = frame_kwargs.get('bg_color')
        klass.write(f"        bg_color = {self.bg_color}\n")
        klass.write("        self.SetBackgroundColour(wx.Colour("
                    f"*{self.bg_color}))\n")
        self.fg_color = frame_kwargs.get('fg_color')
        klass.write(f"        fg_color = {self.fg_color}\n")
        self.tc_bg_color = frame_kwargs.get('tc_bg_color')
        klass.write(f"        tc_bg_color = {self.tc_bg_color}\n")
        font = frame_kwargs.get('font')
        klass.write(f"        font = {font}\n")
        size = frame_kwargs.get('size')
        klass.write(f"        self.SetSize(*{size})\n")
        self.main_sizer = None
        self.second_sizer = None

        # Create all the sizers.
        for sizer, value in self.config.get(frame, {}).get('sizers').items():
            if value[0] == 'BoxSizer':
                self.box_sizer(klass, sizer, value)
            elif value[0] == 'FlexGridSizer':
                self.flex_grid_sizer(klass, sizer, value)

        # Create all the widgets.
        for widget, value in self.config.get(
            frame, {}).get('widgets').items():
            if value[0] == 'StaticText':
                self.static_text(klass, widget, value)
            elif value[0] == 'TextCtrl':
                self.text_ctrl(klass, widget, value)
            elif value[0] == 'DatePickerCtrl':
                self.date_picker_ctrl(klass, widget, value)


        klass.write(f"        self.SetSizer({self.main_sizer})\n")
        klass.write("        self.Layout()\n")
        self.frames[frame] = klass.getvalue()
        klass.close()

    def box_sizer(self, klass, sizer, value):
        self.main_sizer = sizer
        klass.write(f"        {sizer} = wx.BoxSizer(wx.{value[1].upper()})\n")

    def flex_grid_sizer(self, klass, sizer, value):
        self.second_sizer = sizer
        dict_ = self._find_dict(value)
        grid = dict_.get('grid')
        klass.write(f"        {sizer} = wx.FlexGridSizer(*{grid})\n")
        win, prop, flag, border = self._fix_add_args(dict_.get('add'))
        klass.write(f"        {self.main_sizer}.Add({win}, {prop}, "
                    f"{flag}, {border})\n")

    def static_text(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id, label = dict_.get('args')
        klass.write(f"        {widget} = wx.StaticText("
                    f"{parent}, wx.{id}, '{label}')\n")
        min_size = dict_.get('min')
        klass.write(f"        {widget}.SetMinSize({min_size})\n")
        klass.write(f"        {widget}.SetForegroundColour("
                    "wx.Colour(*fg_color))\n")
        ps, fam, style, weight, ul, fn = dict_.get('font')
        fam = self._fix_wx_arg(fam)
        style = self._fix_wx_arg(style)
        weight = self._fix_wx_arg(weight)
        klass.write(f"        {widget}.SetFont(wx.Font({ps}, {fam}, "
                    f"{style}, {weight}, {ul}, '{fn}'))\n")

        if dict_.get('focus', False):
            klass.write(f"        {widget}.SetFocus()\n")

        win, prop, flag, border = self._fix_add_args(dict_.get('add'))
        klass.write(f"        {self.second_sizer}.Add({win}, {prop}, "
                    f"{flag}, {border})\n")

    def text_ctrl(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id, label = dict_.get('args')
        klass.write(f"        {widget} = wx.TextCtrl("
                    f"{parent}, wx.{id}, '{label}')\n")
        min_size = dict_.get('min')

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        klass.write(f"        {widget}.SetBackgroundColour("
                    "wx.Colour(*tc_bg_color))\n")
        klass.write(f"        {widget}.SetForegroundColour("
                    "wx.Colour(*fg_color))\n")
        win, prop, flag, border = self._fix_add_args(dict_.get('add'))
        klass.write(f"        {self.second_sizer}.Add({win}, {prop}, "
                    f"{flag}, {border})\n")

    def date_picker_ctrl(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id = dict_.get('args')
        klass.write(f"        {widget} = wx.adv.DatePickerCtrl("
                    f"{parent}, wx.{id})\n")
        min_size = dict_.get('min')

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        klass.write(f"        {widget}.SetBackgroundColour("
                    "wx.Colour(*tc_bg_color))\n")
        klass.write(f"        {widget}.SetForegroundColour("
                    "wx.Colour(*fg_color))\n")
        win, prop, flag, border = self._fix_add_args(dict_.get('add'))
        klass.write(f"        {self.second_sizer}.Add({win}, {prop}, "
                    f"{flag}, {border})\n")



    def _fix_add_args(self, value):
        add = []

        for idx, v in enumerate(value):
            if idx == 2:
                tmp = v.replace(' ', '').split('|')
                tmp = ' | '.join([f'wx.{flag}' for flag in tmp])
                add.append(eval(tmp))
            else:
                add.append(v)

        return add

    def _fix_wx_arg(self, value):
        return f"wx.{value}"

    def _find_dict(self, value):
        for item in value:
            if isinstance(item, dict):
                break
            else:
                item = {}

        return item


