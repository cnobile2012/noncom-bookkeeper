# -*- coding: utf-8 -*-
#
# src/panel_factory.py
#
__docformat__ = "restructuredtext en"

from io import StringIO

from .config import TomlMetaData
from .bases import find_dict
from .custom_widgits import ordered_month
from .utilities import StoreObjects


class PanelFactory(TomlMetaData):
    """
    Parse the config data and create the panels.
    """
    __panels = {}
    __class_names = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._so = StoreObjects()

    @property
    def class_name_keys(self):
        return self.__class_names.keys()

    def get_class_name(self, panel: str) -> str:
        return self.__class_names.get(panel)

    def get_panel_code(self, panel: str) -> str:
        return self.__panels.get(panel)

    def parse(self) -> None:
        for m_name, panel, _ in self.panels:
            try:
                self._setup_panel(panel)
            except Exception as e:
                self._log.critical("Critical error, cannot start application "
                                   "please contact the developer for help, %s",
                                   str(e), exc_info=True)

    def _setup_panel(self, panel: str) -> None:
        class_name = f"{panel.capitalize()}Panel"
        self.__class_names[panel] = class_name
        panel_kwargs = self.panel_config.get(panel, {}).get('meta')
        klass = StringIO()

        if panel == 'organization':
            klass.write("from src.bases import BaseGenerated\n")
            klass.write("from src.custom_widgits import BadiDatePickerCtrl, "
                        "EVT_BADI_DATE_CHANGED\n")
            klass.write("from src.utilities import StoreObjects\n\n\n")
        elif panel == 'budget':
            klass.write("from src.bases import BaseGenerated\n")
            klass.write("from src.utilities import StoreObjects\n\n\n")
        elif panel == 'monthly':
            klass.write("from src.bases import BaseGenerated\n")
            klass.write("from src.utilities import StoreObjects\n")
            klass.write("from src.custom_widgits import FlatArrowButton, "
                        "EVT_FLAT_ARROW\n\n\n")
        elif panel == 'fiscal':
            klass.write("from src.bases import BaseGenerated\n")
            klass.write("from src.utilities import StoreObjects\n")
            klass.write("from src.custom_widgits import ColorCheckBox, "
                        "EVT_COLOR_CHECKBOX\n\n\n")

        klass.write(f"class {class_name}(BaseGenerated):\n")
        klass.write("    def __init__(self, parent, *args, **kwargs):\n")
        klass.write("        super().__init__(parent, *args, **kwargs)\n")

        if panel in ('organization', 'budget', 'fiscal', 'monthly'):
            klass.write("        self._so = StoreObjects()\n")

        self._bg_color = panel_kwargs.get('bg_color')
        klass.write(f"        self._bg_color = {self._bg_color}\n")
        klass.write("        self.SetBackgroundColour(wx.Colour("
                    "*self._bg_color))\n")
        self._w_bg_color_1 = panel_kwargs.get('w_bg_color_1', False)
        self._w_bg_color_2 = panel_kwargs.get('w_bg_color_2', False)
        self._w_bg_color_3 = panel_kwargs.get('w_bg_color_3', False)
        self._w_fg_color_1 = panel_kwargs.get('w_fg_color_1', False)
        self._order = panel_kwargs.get('order', {})
        # Set default font.
        ps, fam, style, weight, ul, fn = self._parse_font('font_12_normal')
        klass.write(f"        self.SetFont(wx.Font({ps}, {fam}, {style}, "
                    f"{weight}, {ul}, '{fn}'))\n")
        klass.write(f"        self.locale_prefix = {self.locale_prefix}\n")
        self.main_sizer = None
        self.second_sizer = None
        self.panel_data = self.panel_config.get(panel, {})
        self.v_pos = 0

        # Create all the sizers.
        for sizer, value in self.panel_data.get('sizers', {}).items():
            if value[0] == 'BoxSizer':
                self.box_sizer(klass, sizer, value)
            elif value[0] == 'FlexGridSizer':
                self.flex_grid_sizer(klass, sizer, value)
            elif value[0] == 'GridBagSizer':
                self.grid_bag_sizer(klass, sizer, value)

        # Create all the widgets.
        panel_widgets = self.panel_data.get('widgets', {})

        for widget, value in panel_widgets.items():
            self._process_widgets(klass, panel, widget, value)

        # for field_name, widgets in self._order.items():
        #     for widget in widgets:
        #         value = panel_widgets[widget]
        #         self._process_widgets(klass, panel, widget, value)
        #         #print(field_name, panel, widget)

        #     self.v_pos += 1

        # Create all buttons.
        buttons = self.panel_data.get('buttons', {})
        values = [(item, value) for item, value in buttons.items()]

        if values:
            self._assemble_buttons(klass, panel, values)

        if self.main_sizer:
            klass.write(f"        self.SetSizer({self.main_sizer})\n")

        klass.write("        self.SetupScrolling(rate_x=20, rate_y=40)\n")
        klass.write("        self.Layout()\n")
        klass.write("        self.Hide()\n")

        # Add methods to specific panels.
        if panel in ('organization', 'budget'):
            self._create_save_cancel_events(klass)
        elif panel == 'fiscal':
            self._create_fiscal_combobox_select_event(klass)
        elif panel == 'monthly':
            self._create_save_cancel_events(klass)
            self._create_monthly_combobox_select_event(klass)

        self.__panels[panel] = klass.getvalue()
        klass.close()

    def _process_widgets(self, klass: StringIO, panel: str, widget: str,
                         value: list) -> None:
        if value[0] == 'RadioBox':
            self.radio_box(klass, panel, widget, value)
        elif value[0] == 'StaticText':
            self.static_text(klass, panel, widget, value)
        elif value[0] == 'TextCtrl':
            self.text_ctrl(klass, panel, widget, value)
        elif value[0] == 'DatePickerCtrl':
            self.date_picker_ctrl(klass, panel, widget, value)
        elif value[0] == 'BadiDatePickerCtrl':
            self.badi_date_picker_ctrl(klass, panel, widget, value)
        elif value[0] in ('Choice', 'ComboBox'):
            self.choice_combo_box(klass, panel, widget, value)
        elif value[0] == 'ColorCheckBox':
            self.color_check_box(klass, panel, widget, value)
        elif value[0] == 'StaticLine':
            self.static_line(klass, widget, value)

    def box_sizer(self, klass: StringIO, sizer: str, values: list) -> None:
        self.main_sizer = sizer
        flag = self._fix_flags(values[1])
        klass.write(f"        {sizer} = wx.BoxSizer({flag})\n")

    def flex_grid_sizer(self, klass: StringIO, sizer: str, values: list
                        ) -> None:
        self.second_sizer = sizer
        dict_ = find_dict(values)
        grid = dict_.get('grid')
        klass.write(f"        {sizer} = wx.FlexGridSizer(*{grid})\n")
        self._set_add_to_sizer(klass, sizer, values)

    def grid_bag_sizer(self, klass: StringIO, sizer: str, values: list
                       ) -> None:
        self.second_sizer = sizer
        dict_ = find_dict(values)
        gap = dict_.get('gap')
        klass.write(f"        {sizer} = wx.GridBagSizer(*{gap})\n")
        self._set_add_to_sizer(klass, sizer, values)

    def radio_box(self, klass: StringIO, panel: str, widget: str, values: list
                  ) -> None:
        dict_ = find_dict(values)
        mandatory = dict_.get('mandatory', False)
        parent, id, label = dict_.get('args')
        label = label[:-1] if label[-1] == ':' else label
        style = dict_.get('style', 0)
        style = style if style == 0 else self._fix_flags(style)
        choices = dict_.get('choices', [])
        callback = dict_.get('callback')
        dim = dict_.get('dim', 0)
        update = dict_.get('update')
        id = self._fix_flags(id)
        klass.write(f"        {widget} = wx.RadioBox("
                    f"{parent}, {id}, '{label}', style={style}, "
                    f"choices={choices}, majorDimension={dim})\n")
        self._set_colors(klass, widget, values)
        self._set_font(klass, widget, dict_)
        tip = dict_.get('tip', "")

        if tip:
            klass.write(f"        {widget}.SetToolTip('{tip}')\n")

        if dict_.get('focus', False):
            klass.write(f"        {widget}.SetFocus()\n")

        select = dict_.get('select', 0)
        klass.write(f"        {widget}.SetSelection({select})\n")
        self._set_add_to_sizer(klass, widget, values)
        dirty_flag = dict_.get('dirty_event', True)

        if callback:
            klass.write(f"        {widget}.Bind(wx.EVT_RADIOBOX, "
                        f"self.{callback}('{update}', {dirty_flag}))\n")
            klass.write("        wx.CallLater(1000, self._locality_prefix, "
                        f"*({widget}, '{update}'))\n")
        elif dirty_flag:
            klass.write(f"        {widget}.Bind(wx.EVT_RADIOBOX, "
                        "self.set_dirty_flag)\n")

        klass.write(f"        {widget}.mandatory = {mandatory}\n")

    def static_text(self, klass: StringIO, panel: str, widget: str,
                    values: list) -> None:
        dict_ = find_dict(values)
        hidden = dict_.get('hidden', False)

        if not hidden:
            parent, id, label = dict_.get('args')
            label = f"'''{label}'''"
            style = dict_.get('style', 0)
            style = style if style == 0 else self._fix_flags(style)
            id = self._fix_flags(id)
            klass.write(f"        {widget} = wx.StaticText("
                        f"{parent}, {id}, {label}, style={style})\n")
            wrap = dict_.get('wrap')
            self._set_colors(klass, widget, values)
            self._set_font(klass, widget, dict_)
            min_size = dict_.get('min')

            if min_size:
                klass.write(f"        {widget}.SetMinSize({min_size})\n")

            if dict_.get('focus', False):
                klass.write(f"        {widget}.SetFocus()\n")

            if wrap:
                klass.write(f"        {widget}.Wrap({wrap})\n")

            self._set_add_to_sizer(klass, widget, values)

            if dict_.get('instance'):
                klass.write(f"        self.{widget} = {widget}\n")

    def text_ctrl(self, klass: StringIO, panel: str, widget: str, values: list
                  ) -> None:
        dict_ = find_dict(values)
        hidden = dict_.get('hidden', False)

        if not hidden:
            mandatory = dict_.get('mandatory', False)
            parent, id, label = dict_.get('args')
            label = f"'''{label}'''"
            style = dict_.get('style', 0)
            style = style if style == 0 else self._fix_flags(style)
            id = self._fix_flags(id)
            klass.write(f"        {widget} = wx.TextCtrl("
                        f"{parent}, {id}, {label}, style={style})\n")
            self._set_colors(klass, widget, values)
            self._set_font(klass, widget, dict_)
            min_size = dict_.get('min')

            if min_size:
                klass.write(f"        {widget}.SetMinSize({min_size})\n")

            if dict_.get('focus', False):
                klass.write(f"        {widget}.SetFocus()\n")

            if dict_.get('dirty_event', True):
                klass.write(f"        {widget}.Bind(wx.EVT_TEXT, "
                            "self.set_dirty_flag)\n")

            self._set_add_to_sizer(klass, widget, values)

            if dict_.get('instance'):
                klass.write(f"        self.{widget} = {widget}\n")

            value = dict_.get('financial', False)
            klass.write(f"        {widget}.financial = {value}\n")
            klass.write(f"        {widget}.mandatory = {mandatory}\n")

    def date_picker_ctrl(self, klass: StringIO, panel: str, widget: str,
                         values: list) -> None:
        dict_ = find_dict(values)
        mandatory = dict_.get('mandatory', False)
        parent, id, _ = dict_.get('args')
        id = self._fix_flags(id)
        klass.write(f"        {widget} = wx.adv.DatePickerCtrl({parent}, "
                    f"{id})\n")
        self._set_colors(klass, widget, values)
        min_size = dict_.get('min')

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        klass.write(f"        {widget}.Bind(wx.adv.EVT_DATE_CHANGED, "
                    "self.set_dirty_flag)\n")
        klass.write(f"        {widget}.mandatory = {mandatory}\n")
        self._set_add_to_sizer(klass, widget, values)

    def badi_date_picker_ctrl(self, klass: StringIO, panel: str, widget: str,
                              values: list) -> None:
        dict_ = find_dict(values)
        mandatory = dict_.get('mandatory', False)
        parent, id, _ = dict_.get('args')
        id = self._fix_flags(id)
        klass.write(f"        {widget} = BadiDatePickerCtrl({parent}, "
                    f"{id})\n")
        self._set_colors(klass, widget, values)
        min_size = dict_.get('min')

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        klass.write(f"        {widget}.Bind(EVT_BADI_DATE_CHANGED, "
                    "self.set_dirty_flag)\n")
        klass.write(f"        {widget}.mandatory = {mandatory}\n")
        self._set_add_to_sizer(klass, widget, values)

    def choice_combo_box(self, klass: StringIO, panel: str, widget: str,
                         values: list) -> None:
        dict_ = find_dict(values)
        mandatory = dict_.get('mandatory', False)
        parent, id, name = dict_.get('args')
        widget_type = values[0]

        if widget_type == 'ComboBox':
            if panel == 'monthly':
                db = self._so.get_object('Database')
                fy_data = db.full_fiscal_year_data()
                choices = [f"{year}-{ord:>02} {month}"
                           for idx, year, ord, month in fy_data]

                if not choices:
                    choices.insert(0, "For Fiscal Years--Restart")

                first = choices[0]
                label = f"value='''{first}''',"
            elif panel == 'fiscal':
                choices = []
                first = 'Choose Fiscal Year'
                label = f"value='''{first}''',"
                choices.insert(0, first)
        else:
            label = ''

        style = dict_.get('style', 0)
        style = style if style == 0 else self._fix_flags(style)
        id = self._fix_flags(id)
        klass.write(f"        {widget} = wx.{widget_type}({parent}, {id}, "
                    f"{label} choices={choices}, style={style})\n")
        klass.write(f"        {widget}.SetLabel('{name}')\n")
        self._set_colors(klass, widget, values)
        min_size = dict_.get('min')

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        if dict_.get('dirty_event', True):
            klass.write(f"        {widget}.Bind(wx.EVT_COMBOBOX, "
                        "self.set_dirty_flag)\n")
        else:
            klass.write(f"        {widget}.Bind(wx.EVT_COMBOBOX, "
                        "self.get_selection)\n")

        klass.write(f"        {widget}.mandatory = {mandatory}\n")
        self._set_add_to_sizer(klass, widget, values)

    def color_check_box(self, klass: StringIO, panel: str, widget: str,
                        values: list) -> None:
        dict_ = find_dict(values)
        mandatory = dict_.get('mandatory', False)
        parent, id, label, name = dict_.get('args')
        id = self._fix_flags(id)
        klass.write(f"        {widget} = ColorCheckBox({parent}, {id}, "
                    f"label='{label}', name='{name}')\n")
        self._set_colors(klass, widget, values)
        min_size = dict_.get('min')
        enabled = dict_.get('enabled', True)

        if min_size:
            klass.write(f"        {widget}.SetMinSize({min_size})\n")

        if dict_.get('dirty_event', True):
            klass.write(f"        {widget}.Bind(EVT_COLOR_CHECKBOX, "
                        "self.set_dirty_flag)\n")

        klass.write(f"        {widget}.Enable({enabled})\n")
        klass.write(f"        {widget}.mandatory = {mandatory}\n")
        self._set_add_to_sizer(klass, widget, values)

    def static_line(self, klass: StringIO, widget: str, values: list) -> None:
        dict_ = find_dict(values)
        parent, flags = dict_.get('args')
        flags = self._fix_flags(flags)
        klass.write(f"        {widget} = wx.StaticLine({parent}, {flags})\n")
        self._set_colors(klass, widget, values)
        self._set_add_to_sizer(klass, widget, values)

    def _assemble_buttons(self, klass: StringIO, panel: str, values: list
                          ) -> None:
        """
        Assemble the buttons for this panel.

        :param StringIO klass: A `StringIO` object.
        :param str panel: The current panel name.
        :param list values: This is a list of tuples as in [(<item>, value),
                            ...]. Where `<item>` is the variable name for a
                            panel, sizer, or widget and `value` is the list
                            of values from the toml config file.
        """
        for items in values:
            name, value = items
            dict_ = find_dict(value)

            if value[0] == 'Panel':
                panel_parent = dict_.get('args')
                items = dict_.get('add', ())
                panel_prop, flags, panel_border = items
                panel_flags = self._fix_flags(flags)
                btn_panel = name
            elif value[0] == 'BoxSizer':
                btn_sizer = name
            elif value[0] == 'Button':
                prop, flags, label = dict_.get('args')
                callback = dict_.get('callback')

                if 'ID_CANCEL' == flags:
                    c_parent = prop  # Should be the same as btn_panel above.
                    c_flags = self._fix_flags(flags)
                    c_label = label
                    c_widget = name
                    button_cancel = callback
                    c_value = value
                else:
                    f_parent = prop  # Should be the same as btn_panel above.
                    f_flags = self._fix_flags(flags)
                    f_label = label
                    f_widget = name
                    button_save = callback
                    f_value = value
            elif value[0] == 'StaticLine':
                sl_value = value
                sl_widget = name

        self.static_line(klass, sl_widget, sl_value)
        klass.write(f"        {btn_panel} = wx.Panel({panel_parent})\n")
        klass.write(f"        {btn_sizer} = wx.BoxSizer(wx.HORIZONTAL)\n")
        klass.write(f"        {f_widget} = wx.Button({f_parent}, {f_flags}, "
                    f"label='{f_label}')\n")
        self._set_colors(klass, f_widget, f_value)
        klass.write(f"        {f_widget}.Bind(wx.EVT_BUTTON, "
                    f"self.{button_save})\n")
        klass.write(f"        {btn_sizer}.Add({f_widget}, 0, wx.ALL, 10)\n")
        klass.write(f"        {c_widget} = wx.Button({c_parent}, {c_flags}, "
                    f"label='{c_label}')\n")
        self._set_colors(klass, c_widget, c_value)
        klass.write(f"        {c_widget}.Bind(wx.EVT_BUTTON, "
                    f"self.{button_cancel})\n")
        klass.write(f"        {btn_sizer}.Add({c_widget}, 0, wx.ALL, 10)\n")
        klass.write(f"        {btn_panel}.SetSizer({btn_sizer})\n")
        klass.write(f"        {self.main_sizer}.Add({btn_panel}, "
                    f"{panel_prop}, {panel_flags}, {panel_border})\n")

    def _create_save_cancel_events(self, klass: StringIO) -> None:
        klass.write("\n    def button_save(self, event):\n")
        klass.write("        self.save = True\n")
        klass.write("        event.Skip()\n\n")
        klass.write("    @property\n")
        klass.write("    def save(self):\n")
        klass.write("        return self._save\n\n")
        klass.write("    @save.setter\n")
        klass.write("    def save(self, value):\n")
        klass.write("        if self.dirty:\n")
        klass.write("            mf = self._so.get_object('MainFrame')\n")
        klass.write("            mf.statusbar_message = 'Saving data.'\n\n")
        klass.write("        self._save = value\n\n")
        klass.write("    def button_cancel(self, event):\n")
        klass.write("        self.cancel = True\n")
        klass.write("        event.Skip()\n\n")
        klass.write("    @property\n")
        klass.write("    def cancel(self):\n")
        klass.write("        return self._cancel\n\n")
        klass.write("    @cancel.setter\n")
        klass.write("    def cancel(self, value):\n")
        klass.write("        if self.dirty:\n")
        klass.write("            mf = self._so.get_object('MainFrame')\n")
        klass.write("            mf.statusbar_message = 'Restoring data.'\n\n")
        klass.write("        self._cancel = value\n")

    def _create_fiscal_combobox_select_event(self, klass: StringIO) -> None:
        klass.write("\n    def get_selection(self, event):\n")
        klass.write("        value = event.GetString()\n")
        klass.write("        year, _, nyear = value.partition('-')\n")
        klass.write("        db = self._so.get_object('Database')\n\n")
        klass.write("        if year.isdecimal():\n")
        klass.write("            db.populate_fiscal_panel(int(year))\n")
        klass.write("            self.selected = True\n")
        klass.write("        else:\n")
        klass.write("            db.set_fiscal_panel(False, False, False)\n")
        klass.write("            self.selected = False\n")

    def _create_monthly_combobox_select_event(self, klass: StringIO) -> None:
        klass.write("\n    def get_selection(self, event):\n")
        klass.write("        value = event.GetString()\n")
        klass.write("        db = self._so.get_object('Database')\n")
        klass.write("        db.update_monthly_panel(value)\n")

    def _set_colors(self, klass: StringIO, widget: str, value: list) -> None:
        """
        Sets the background and/or foreground color. Also raise an
        assertion error if more than one of either has been specified.
        """
        has_bgc = 'bg_color' in value
        has_bgc1 = 'w_bg_color_1' in value
        has_bgc2 = 'w_bg_color_2' in value
        has_bgc3 = 'w_bg_color_3' in value
        bg = [x for x in (has_bgc, has_bgc1, has_bgc2, has_bgc3) if x]
        assert -1 < len(bg) < 2, ("Error: Cannot set more than one "
                                  f"background color in '{widget}'")
        has_fgc1 = 'w_fg_color_1' in value
        fg = [x for x in (has_fgc1,) if x]
        assert -1 < len(fg) < 2, ("Error: Cannot set more than one "
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
        elif has_bgc3 and self._w_bg_color_3:
            klass.write(f"        {widget}.SetBackgroundColour("
                        f"wx.Colour(*{self._w_bg_color_3}))\n")

        if has_fgc1 and self._w_fg_color_1:
            klass.write(f"        {widget}.SetForegroundColour("
                        f"wx.Colour(*{self._w_fg_color_1}))\n")

    def _set_font(self, klass: StringIO, widget: str, dict_: dict) -> None:
        font_type = dict_.get('font')

        if font_type:
            ps, fam, style, weight, ul, fn = self._parse_font(font_type)
            klass.write(f"        {widget}.SetFont(wx.Font({ps}, {fam}, "
                        f"{style}, {weight}, {ul}, '{fn}'))\n")

    def _parse_font(self, font_type: str) -> tuple:
        font = self.get_font(font_type)
        ps, fam, style, weight, ul, fn = font
        fam = self._fix_flags(fam)
        style = self._fix_flags(style)
        weight = self._fix_flags(weight)
        return ps, fam, style, weight, ul, fn

    def _fix_flags(self, flags: str | int) -> str:
        if isinstance(flags, int):
            item = flags
        else:
            flag_list = flags.replace(' ', '').split('|')
            item = ' | '.join([f"wx.{flag.upper()}" for flag in flag_list])

        return item

    def _set_add_to_sizer(self, klass: StringIO, widget: str, values: list
                          ) -> None:
        """
        Adds the item to the specified sizer.

        :param StringIO klass: A `StringIO` object.
        :param str widget: Can be a widget, panel, or sizer.
        :param list values: Various values used to add items to a sizer.
        """
        sizer = self.main_sizer if 'Sizer' in values[0] else self.second_sizer
        dict_ = find_dict(values)
        prop, flags, border = dict_.get('add')
        flags = self._fix_flags(flags) if flags != 0 else flags
        pos = dict_.get('pos')
        span = dict_.get('span')

        if pos and len(pos) == 1:
            pos.insert(0, self.v_pos)

        if pos and span:
            klass.write(f"        {sizer}.Add({widget}, {pos}, "
                        f"{span}, {flags}, {border})\n")
        else:
            klass.write(f"        {sizer}.Add({widget}, {prop}, "
                        f"{flags}, {border})\n")
