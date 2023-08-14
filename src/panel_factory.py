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

    def __init__(self, parent, id=wx.ID_ANY,
                 style=wx.NO_BORDER | wx.TAB_TRAVERSAL, **kwargs):
        super().__init__(parent, id=id, style=style, **kwargs)

    @property
    def background_color(self):
        return self._bg_color

    def locality_prefix(self, update):
        def do_event(event):
            rb = event.GetEventObject()
            self._locality_prefix(rb, update)

        return do_event

    def _locality_prefix(self, rb, update):
        selection = rb.GetStringSelection()
        text = self.locale_prefix[selection.lower()]
        prefix_widget = getattr(self, update)
        prefix_widget.SetValue(text)


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
        self._bg_color = panel_kwargs.get('bg_color')
        klass.write("        self.SetBackgroundColour(wx.Colour("
                    f"*{self._bg_color}))\n")
        self._w_bg_color_1 = panel_kwargs.get('w_bg_color_1')
        self._w_bg_color_2 = panel_kwargs.get('w_bg_color_2')
        self._w_fg_color_1 = panel_kwargs.get('w_fg_color_1')
        ps, fam, style, weight, ul, fn = panel_kwargs.get('font')
        fam = self._fix_flags(fam)
        style = self._fix_flags(style)
        weight = self._fix_flags(weight)
        klass.write(f"        font = [{ps}, {fam}, {style}, {weight}, "
                    f"{ul}, {fn}]\n")
        self.span = panel_kwargs.get('sizer_span')
        locale_prefix = panel_kwargs.get('locale_prefix')

        if locale_prefix:
             klass.write(f"        self.locale_prefix = {locale_prefix}\n")

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
            if value[0] == 'RadioBox':
                self.radio_box(klass, widget, value)
            elif value[0] == 'StaticText':
                self.static_text(klass, widget, value)
            elif value[0] == 'TextCtrl':
                self.text_ctrl(klass, widget, value)
            elif value[0] == 'DatePickerCtrl':
                self.date_picker_ctrl(klass, widget, value)
            elif value[0] == 'StaticLine':
                self.static_line(klass, widget, value)
            elif value == 'sizer_span':
                self.sizer_span(klass)
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
        flag = self._fix_flags(value[1])
        klass.write(f"        {sizer} = wx.BoxSizer({flag})\n")

    def flex_grid_sizer(self, klass, sizer, value):
        self.second_sizer = sizer
        dict_ = self._find_dict(value)
        grid = dict_.get('grid')
        klass.write(f"        {sizer} = wx.FlexGridSizer(*{grid})\n")
        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.main_sizer}.Add({sizer}, {prop}, "
                    f"{flags}, {border})\n")

    def radio_box(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id, label = dict_.get('args')
        style = dict_.get('style', 0)
        style = style if style == 0 else self._fix_flags(style)
        choices = dict_.get('choices', [])
        callback = dict_.get('callback')
        dim = dict_.get('dim', 0)
        update = dict_.get('update')
        klass.write(f"        {widget} = wx.RadioBox("
                    f"{parent}, wx.{id}, '{label}', style={style}, "
                    f"choices={choices}, majorDimension={dim})\n")
        self._set_colors(klass, widget, value)
        self._set_font(klass, widget, dict_)
        tip = dict_.get('tip', "")

        if tip:
            klass.write(f"        {widget}.SetToolTip('{tip}')\n")

        if dict_.get('focus', False):
            klass.write(f"        {widget}.SetFocus()\n")

        select = dict_.get('select', 0)
        klass.write(f"        {widget}.SetSelection({select})\n")
        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.second_sizer}.Add({widget}, {prop}, "
                    f"{flags}, {border})\n")

        if callback:
            klass.write(f"        {widget}.Bind(wx.EVT_RADIOBOX, "
                        f"self.{callback}('{update}'))\n")
            klass.write("        wx.CallLater(1000, "
                        f"self._locality_prefix, *({widget}, '{update}'))\n")

    def static_text(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id, label = dict_.get('args')
        style = dict_.get('style', 0)
        style = style if style == 0 else self._fix_flags(style)
        klass.write(f"        {widget} = wx.StaticText("
                    f"{parent}, wx.{id}, '{label}', style={style})\n")
        min_size = dict_.get('min')
        font = dict_.get('font')
        wrap = dict_.get('wrap')
        self._set_colors(klass, widget, value)
        self._set_font(klass, widget, dict_)

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        if dict_.get('focus', False):
            klass.write(f"        {widget}.SetFocus()\n")

        if wrap:
            klass.write(f"        {widget}.Wrap({wrap})\n")

        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.second_sizer}.Add({widget}, {prop}, "
                    f"{flags}, {border})\n")

        if dict_.get('instance'):
            klass.write(f"        self.{widget} = {widget}\n")

    def text_ctrl(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id, label = dict_.get('args')
        style = dict_.get('style', 0)
        style = style if style == 0 else self._fix_flags(style)
        klass.write(f"        {widget} = wx.TextCtrl("
                    f"{parent}, wx.{id}, '{label}', style={style})\n")
        min_size = dict_.get('min')
        self._set_colors(klass, widget, value)

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        if dict_.get('focus', False):
            klass.write(f"        {widget}.SetFocus()\n")

        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.second_sizer}.Add({widget}, {prop}, "
                    f"{flags}, {border})\n")

        if dict_.get('instance'):
            klass.write(f"        self.{widget} = {widget}\n")

    def date_picker_ctrl(self, klass, widget, value):
        dict_ = self._find_dict(value)
        parent, id = dict_.get('args')
        klass.write(f"        {widget} = wx.adv.DatePickerCtrl("
                    f"{parent}, wx.{id})\n")
        min_size = dict_.get('min')
        self._set_colors(klass, widget, value)

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags)
        klass.write(f"        {self.second_sizer}.Add({widget}, {prop}, "
                    f"{flags}, {border})\n")

    def static_line(klass, widget, value):
        panel, flags = value
        flags = self._fix_flags(flags)
        klass.write(f"        {widget} = wx.StaticLine({panel}, {flags})")

    def sizer_span(self, klass):
        if self.span:
            klass.write(f"        {self.second_sizer}.Add(*{self.span})\n")

    def blank_line(self, klass):
        pass




    def _fix_flags(self, flags):
        if isinstance(flags, int):
            item = flags
        else:
            flag_list = flags.replace(' ', '').split('|')
            item = ' | '.join([f"wx.{flag.upper()}" for flag in flag_list])

        return item

    def _find_dict(self, value):
        for item in value:
            if isinstance(item, dict):
                break
            else:
                item = {}

        return item

    def _set_colors(self, klass, widget, value):
        """
        Sets the background and/or foreground color. Also raise an
        assertion error if more than one of either has been specified.
        """
        has_bgc = 'bg_color' in value
        has_bgc1 = 'w_bg_color_1' in value
        has_bgc2 = 'w_bg_color_2' in value
        bg = [x for x in (has_bgc, has_bgc1, has_bgc2) if x]
        assert -1 < len(bg) < 2, print("Error: Cannot set more than one "
                                       f"background color in '{widget}'")
        has_fgc1 = 'w_fg_color_1' in value
        fg = [x for x in (has_fgc1,) if x]
        assert -1 < len(fg) < 2, print("Error: Cannot set more than one "
                                       f"foreground color in '{widget}'")

        if has_bgc and self._bg_color:
            klass.write(f"        {widget}.SetBackgroundColour("
                        f"wx.Colour(*{self._bg_color}))\n")
        elif has_bgc1 and self._w_bg_color_1:
            klass.write(f"        {widget}.SetBackgroundColour("
                        f"wx.Colour(*{self._w_bg_color_1}))\n")
        elif has_bgc2 and self._w_bg_color_2:
            klass.write(f"        {widget}.SetBackgroundColour("
                        f"wx.Colour(*{self._w_bg_color_2}))\n")

        if has_fgc1 and self._w_fg_color_1:
            klass.write(f"        {widget}.SetForegroundColour("
                        f"wx.Colour(*{self._w_fg_color_1}))\n")

    def _set_font(self, klass, widget, dict_):
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
