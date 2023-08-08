# -*- coding: utf-8 -*-
#
# src/panel_factory.py
#
__docformat__ = "restructuredtext en"

from io import StringIO

from .config import BaseSystemData

import wx
import wx.adv
# https://pwwang.github.io/python-varname/
#from varname import varname, nameof


class BasePanel(wx.Panel):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    @property
    def background_color(self):
        return self.bg_color


class PanelFactory(BaseSystemData):
    """
    Parse the config data and create the panels.
    """
    __panels = {}
    __class_names = {}

    def __init__(self):
        super().__init__()

    @property
    def class_name_keys(self):
        return self.__class_names.keys()

    def get_class_name(self, panel):
        return self.__class_names.get(panel)

    def get_panel_code(self, panel):
        return self.__panels.get(panel)

    def parse(self):
        panels = self.config.get('meta', {}).get('panels')

        for panel in panels:
            try:
                self.setup_panel(panel)
            except Exception as e:
                self._log.critical("Critical error, cannot start application "
                                   "please contact the developer for help, %s",
                                   str(e), exc_info=True)
                # *** TODO *** This needs to be shown on the panel if detected.

    def setup_panel(self, panel):
        class_name = f"{panel.capitalize()}Panel"
        self.__class_names[panel] = class_name
        panel_kwargs = self.config.get(panel, {}).get('meta')
        klass = StringIO()
        klass.write(f"class {class_name}(BasePanel):\n")
        klass.write("    def __init__(self, parent, **kwargs):\n")
        klass.write("        super().__init__(parent, **kwargs)\n")
        title = panel_kwargs.get('title')
        klass.write(f"        self.title = '''{title}'''\n")
        self.bg_color = panel_kwargs.get('bg_color')
        klass.write(f"        self.bg_color = {self.bg_color}\n")
        klass.write("        self.SetBackgroundColour(wx.Colour("
                    f"*{self.bg_color}))\n")
        self.fg_color = panel_kwargs.get('fg_color')
        klass.write(f"        fg_color = {self.fg_color}\n")
        self.tc_bg_color = panel_kwargs.get('tc_bg_color')
        klass.write(f"        tc_bg_color = {self.tc_bg_color}\n")
        ps, fam, style, weight, ul, fn = panel_kwargs.get('font')
        fam = self._fix_flags(fam)
        style = self._fix_flags(style)
        weight = self._fix_flags(weight)
        klass.write(f"        font = [{ps}, {fam}, {style}, {weight}, "
                    f"{ul}, {fn}]\n")
        self.blank = panel_kwargs.get('blank_line')
        self.main_sizer = None
        self.second_sizer = None

        # Create all the sizers.
        for sizer, value in self.config.get(
            panel, {}).get('sizers', {}).items():
            if value[0] == 'BoxSizer':
                self.box_sizer(klass, sizer, value)
            elif value[0] == 'FlexGridSizer':
                self.flex_grid_sizer(klass, sizer, value)

        # Create all the widgets.
        for widget, value in self.config.get(
            panel, {}).get('widgets', {}).items():
            if value[0] == 'StaticText':
                self.static_text(klass, widget, value)
            elif value[0] == 'TextCtrl':
                self.text_ctrl(klass, widget, value)
            elif value[0] == 'DatePickerCtrl':
                self.date_picker_ctrl(klass, widget, value)
            elif value[0] == 'StaticLine':
                self.static_line(klass, widget, value)
            elif value == "blank":
                self.blank_line(klass)

        if self.main_sizer:
            klass.write(f"        self.SetSizer({self.main_sizer})\n")

        klass.write("        self.Layout()\n")
        klass.write("        self.Hide()\n")
        self.__panels[panel] = klass.getvalue()
        klass.close()

    def box_sizer(self, klass, sizer, value):
        self.main_sizer = sizer
        klass.write(f"        {sizer} = wx.BoxSizer(wx.{value[1].upper()})\n")

    def flex_grid_sizer(self, klass, sizer, value):
        self.second_sizer = sizer
        dict_ = self._find_dict(value)
        grid = dict_.get('grid')
        klass.write(f"        {sizer} = wx.FlexGridSizer(*{grid})\n")
        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.main_sizer}.Add({sizer}, {prop}, "
                    f"{flags}, {border})\n")

    def static_text(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id, label = dict_.get('args')
        style = dict_.get('style', 0)
        style = style if style == 0 else self._fix_flags(style)
        klass.write(f"        {widget} = wx.StaticText("
                    f"{parent}, wx.{id}, '{label}', style={style})\n")
        min_size = dict_.get('min')

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        klass.write(f"        {widget}.SetForegroundColour("
                    "wx.Colour(*fg_color))\n")
        font = dict_.get('font')

        if font:
            ps, fam, style, weight, ul, fn = font
            fam = self._fix_flags(fam)
            style = self._fix_flags(style)
            weight = self._fix_flags(weight)
            klass.write(f"        {widget}.SetFont(wx.Font({ps}, {fam}, "
                        f"{style}, {weight}, {ul}, '{fn}'))\n")
        else:
            klass.write(f"        {widget}.SetFont(wx.Font(*font))\n")

        if dict_.get('focus', False):
            klass.write(f"        {widget}.SetFocus()\n")

        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.second_sizer}.Add({widget}, {prop}, "
                    f"{flags}, {border})\n")

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
        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.second_sizer}.Add({widget}, {prop}, "
                    f"{flags}, {border})\n")

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
        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.second_sizer}.Add({widget}, {prop}, "
                    f"{flags}, {border})\n")

    def static_line(klass, widget, value):
        panel, flags = value
        flags = self._fix_flags(flags)
        klass.write(f"        {widget} = wx.StaticLine({panel}, {flags})")

    def blank_line(self, klass):
        if self.blank:
            klass.write(f"        {self.second_sizer}.Add(*{self.blank})\n")




    def _fix_flags(self, flags):
        flag_list = flags.replace(' ', '').split('|')
        return  ' | '.join([f"wx.{flag}" for flag in flag_list])

    def _find_dict(self, value):
        for item in value:
            if isinstance(item, dict):
                break
            else:
                item = {}

        return item

