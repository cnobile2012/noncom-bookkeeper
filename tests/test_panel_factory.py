# -*- coding: utf-8 -*-
#
# test/test_panel_factory.py
#
__docformat__ = "restructuredtext en"

import os
import re
import unittest
import wx

from io import StringIO
from collections.abc import KeysView
from unittest.mock import patch

from src.panel_factory import PanelFactory
from . import BASE_DIR, check_flag, patchers
from .base_database_test import BaseAsyncTests


class TestPanelFactory(BaseAsyncTests):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        patchers(self)
        self.pf = PanelFactory()
        full_path = os.path.join(BASE_DIR, 'tests', 'panels.toml')
        self.pf.panel_config = self.pf.parse_toml(full_path)
        self.pf.parse()

    async def asyncSetUp(self):
        await self.db.create_db()
        await self.insert_data()
        await self.db.cache.load()

    async def asyncTearDown(self):
        self.db.cache._flush_cache()
        await self.truncate_all_tables()

    #@unittest.skip("Temporarily skipped")
    def test_class_name_keys(self):
        """
        Test that the class_name_keys property returns a KeysView of the
        panel names.
        """
        expected = 'organization'
        result = self.pf.class_name_keys
        self.assertIsInstance(result, KeysView)
        result = list(self.pf.class_name_keys)[0]
        self.assertEqual(expected, result)

    #@unittest.skip("Temporarily skipped")
    def test_get_class_name(self):
        """
        Test that the get_class_name method returns the class name that
        is being built.
        """
        expected = 'OrganizationPanel'
        result = self.pf.get_class_name('organization')
        self.assertEqual(expected, result)

    #@unittest.skip("Temporarily skipped")
    def test_get_panel_code(self):
        """
        Test that the get_panel_code method returns
        """
        expected = 'class OrganizationPanel(BaseGenerated):'
        result = self.pf.get_panel_code('organization')
        self.assertIn(expected, result)

    @unittest.skip("Temporarily skipped")
    def test_parse(self):
        """
        Test that the parse method 
        """


    @unittest.skip("Temporarily skipped")
    def test__setup_panel(self):
        """
        Test that the _setup_panel method 
        """
        

    @unittest.skip("Temporarily skipped")
    def test__process_widgets(self):
        """
        Test that the _process_widgets method 
        """


    #@unittest.skip("Temporarily skipped")
    def test_box_sizer(self):
        """
        Test that the box_sizer method sets up the sizer.
        """
        sizer = 'sizer_0'
        values = ['BoxSizer', 'VERTICAL']
        expected = ("        sizer_0 = wx.BoxSizer(wx.VERTICAL)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.box_sizer(buff, sizer, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_flex_grid_sizer(self):
        """
        Test that the flex_grid_sizer method sets up the sizer.
        """
        sizer = 'sizer_1'
        values = ['FlexGridSizer', {'grid': [2, 2, 2, 2],
                                    'add': [0, 'CENTER | ALL', 10]}]
        expected = ("        sizer_1 = wx.FlexGridSizer(*[2, 2, 2, 2])\n"
                    "        sizer_0.Add(sizer_1, 0, wx.CENTER | "
                    "wx.ALL, 10)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.flex_grid_sizer(buff, sizer, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_grid_bag_sizer(self):
        """
        Test that the grid_bag_sizer method sets up the sizer.
        """
        sizer = 'sizer_1'
        values = ['GridBagSizer', {'gap': [2, 2],
                                   'add': [0, 'CENTER | ALL', 10]}]
        expected = ("        sizer_1 = wx.GridBagSizer(*[2, 2])\n"
                    "        sizer_0.Add(sizer_1, 0, wx.CENTER | "
                    "wx.ALL, 10)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.grid_bag_sizer(buff, sizer, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_radio_box(self):
        """
        Test that the static_text method returns the code for
        a RadioBox.
        """
        panel = 'organization'
        widget = 'widget_01'
        values0 = ['RadioBox', 'w_fg_color_1',
                   {'args': ['self', 'ID_ANY', 'Locality Prefix'],
                    'choices': ['LSA', 'Group'], 'dim': 1,
                    'style': 'RA_SPECIFY_ROWS', 'font': 'font_10_bold',
                    'tip': "Choose if your community is an LSA or a group.",
                    'select': 0,
                    'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP',
                            6], 'pos': [1, 0], 'span': [1, 1],
                    'callback': 'locality_prefix', 'update': 'widget_02'}]
        expect0 = ("        widget_01 = wx.RadioBox(self, wx.ID_ANY, "
                   "'Locality Prefix', style=wx.RA_SPECIFY_ROWS, "
                   "choices=['LSA', 'Group'], majorDimension=1)\n"
                   "        widget_01.SetForegroundColour("
                   "wx.Colour(*[50, 50, 204]))\n"
                   "        widget_01.SetFont(wx.Font(10, "
                   "wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, "
                   "wx.FONTWEIGHT_BOLD, 0, ''))\n"
                   "        widget_01.SetToolTip('Choose if your community "
                   "is an LSA or a group.')\n"
                   "        widget_01.SetSelection(0)\n"
                   "        sizer_1.Add(widget_01, [1, 0], [1, 1], "
                   "wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | "
                   "wx.TOP, 6)\n"
                   "        widget_01.Bind(wx.EVT_RADIOBOX, "
                   "self.locality_prefix('widget_02', True))\n"
                   "        wx.CallLater(1000, self._locality_prefix, "
                   "*(widget_01, 'widget_02'))\n"
                   "        widget_01.mandatory = False\n")
        values1 = ['RadioBox', 'w_fg_color_1',
                   {'args': ['self', 'ID_ANY', 'Locality Prefix'],
                    'choices': ['LSA', 'Group'], 'dim': 1,
                    'style': 'RA_SPECIFY_ROWS', 'font': 'font_10_bold',
                    'tip': "Choose if your community is an LSA or a group.",
                    'select': 0,
                    'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP',
                            6], 'pos': [1, 0], 'span': [1, 1],
                    'dirty_event': True, 'focus': True}]
        expect1 = ("        widget_01 = wx.RadioBox(self, wx.ID_ANY, "
                   "'Locality Prefix', style=wx.RA_SPECIFY_ROWS, "
                   "choices=['LSA', 'Group'], majorDimension=1)\n"
                   "        widget_01.SetForegroundColour("
                   "wx.Colour(*[50, 50, 204]))\n"
                   "        widget_01.SetFont(wx.Font(10, "
                   "wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, "
                   "wx.FONTWEIGHT_BOLD, 0, ''))\n"
                   "        widget_01.SetToolTip('Choose if your community is "
                   "an LSA or a group.')\n"
                   "        widget_01.SetFocus()\n"
                   "        widget_01.SetSelection(0)\n"
                   "        sizer_1.Add(widget_01, [1, 0], [1, 1], "
                   "wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | "
                   "wx.TOP, 6)\n"
                   "        widget_01.Bind(wx.EVT_RADIOBOX, "
                   "self.set_dirty_flag)\n"
                   "        widget_01.mandatory = False\n")

        data = (
            ('organization', 'widget_01', values0, expect0),
            ('organization', 'widget_01', values1, expect1)
            )
        msg = "Expected '{}', found '{}'."

        for panel, widget, values, expected in data:
            with StringIO() as buff:
                self.pf.radio_box(buff, panel, widget, values)
                result = buff.getvalue()
                self.assertEqual(expected, result, msg.format(
                    expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_static_text(self):
        """
        Test that the static_text method returns the code for
        a StaticText.
        """
        panel = 'organization'
        widget = 'widget_03'
        values = ['StaticText', 'w_fg_color_1',
                  {'args': ['self', 'ID_ANY', 'Locale Name:'], 'min': [-1, -1],
                   'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP', 6],
                   'pos': [2, 0], 'span': [1, 1], 'focus': True}]
        expected = ("        widget_03 = wx.StaticText(self, wx.ID_ANY, "
                    "'''Locale Name:''', style=0)\n"
                    "        widget_03.SetForegroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        widget_03.SetMinSize([-1, -1])\n"
                    "        widget_03.SetFocus()\n"
                    "        sizer_1.Add(widget_03, [2, 0], [1, 1], "
                    "wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | "
                    "wx.TOP, 6)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.static_text(buff, panel, widget, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_text_ctrl(self):
        """
        Test that the text_ctrl method returns the code for
        a TextCtrl.
        """
        panel = 'organization'
        widget = 'widget_02'
        values = ['TextCtrl', 'w_bg_color_1', 'w_fg_color_1',
                  {'args': ['self', 'ID_ANY', ''], 'style': 'TE_READONLY',
                   'font': 'font_10_normal', 'min': [260, 26], 'wrap': 240,
                   'add': [0, 'ALIGN_BOTTOM | LEFT | RIGHT | TOP', 6],
                   'pos': [1, 1], 'span': [1, 1], 'instance': True,
                   'dirty_event': False, 'financial': False,
                   'mandatory': False}]
        expected = ("        widget_02 = wx.TextCtrl(self, wx.ID_ANY, "
                    "'''''', style=wx.TE_READONLY)\n"
                    "        widget_02.SetBackgroundColour("
                    "wx.Colour(*[222, 237, 230]))\n"
                    "        widget_02.SetForegroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        widget_02.SetFont(wx.Font(10, "
                    "wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, "
                    "wx.FONTWEIGHT_NORMAL, 0, ''))\n"
                    "        widget_02.SetMinSize([260, 26])\n"
                    "        sizer_1.Add(widget_02, [1, 1], [1, 1], "
                    "wx.ALIGN_BOTTOM | wx.LEFT | wx.RIGHT | wx.TOP, 6)\n"
                    "        self.widget_02 = widget_02\n"
                    "        widget_02.financial = False\n"
                    "        widget_02.mandatory = False\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.text_ctrl(buff, panel, widget, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_date_picker_ctrl(self):
        """
        Test that the date_picker_ctrl method returns the code for
        a DatePickerCtrl.
        """
        panel = 'organization'
        widget = 'widget_10'
        values = ['DatePickerCtrl', 'w_bg_color_1', 'w_fg_color_1',
                  {'args': ['self', 'ID_ANY', ''], 'min': [130, 26],
                   'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP', 6],
                   'pos': [5, 1], 'span': [1, 1], 'mandatory': False}]
        expected = ("        widget_10 = wx.adv.DatePickerCtrl(self, "
                    "wx.ID_ANY)\n"
                    "        widget_10.SetBackgroundColour("
                    "wx.Colour(*[222, 237, 230]))\n"
                    "        widget_10.SetForegroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        widget_10.SetMinSize([130, 26])\n"
                    "        widget_10.Bind(wx.adv.EVT_DATE_CHANGED, "
                    "self.set_dirty_flag)\n"
                    "        widget_10.mandatory = False\n"
                    "        sizer_1.Add(widget_10, [5, 1], [1, 1], "
                    "wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | "
                    "wx.TOP, 6)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.date_picker_ctrl(buff, panel, widget, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_badi_date_picker_ctrl(self):
        """
        Test that the badi_date_picker_ctrl method returns the code for
        a BadiDatePickerCtrl.
        """
        panel = 'organization'
        widget = 'widget_10'
        values = ['BadiDatePickerCtrl', 'w_bg_color_1', 'w_fg_color_1',
                  {'args': ['self', 'ID_ANY', ''], 'min': [130, 26],
                   'add': [0, 'ALIGN_CENTER_VERTICAL | LEFT | RIGHT | TOP', 6],
                   'pos': [5, 1], 'span': [1, 1], 'mandatory': False}]
        expected = ("        widget_10 = BadiDatePickerCtrl(self, wx.ID_ANY)\n"
                    "        widget_10.SetBackgroundColour("
                    "wx.Colour(*[222, 237, 230]))\n"
                    "        widget_10.SetForegroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        widget_10.SetMinSize([130, 26])\n"
                    "        widget_10.Bind(EVT_BADI_DATE_CHANGED, "
                    "self.set_dirty_flag)\n"
                    "        widget_10.mandatory = False\n"
                    "        sizer_1.Add(widget_10, [5, 1], [1, 1], "
                    "wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | "
                    "wx.TOP, 6)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.badi_date_picker_ctrl(buff, panel, widget, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_choice_combo_box(self):
        """
        Test that the choice_combo_box method returns the code for a ComboBox.

        NOTE: Needs the db implimented in the tests before this test will work.
        """
        panel = 'monthly'
        widget = 'widget_01'
        values = ['ComboBox', 'w_bg_color_1', 'w_fg_color_1',
                  {'args': ['self', 'ID_ANY', 'Month Index:'],
                   'style': 'CB_READONLY', 'min': [228, 26],
                   'add': [0, 'ALIGN_BOTTOM | ALL', 10], 'pos': [1, 0],
                   'span': [1, 1], 'dirty_event': True, 'mandatory': True}]
        expected = ("        widget_01 = wx.ComboBox(self, wx.ID_ANY, "
                    "value='''183-03 Jamál''', choices=['183-03 Jamál', "
                    "\"183-04 'Aẓamat\", '183-05 Núr', '183-06 Raḥmat', "
                    "'183-07 Kalimát', '183-08 Kamál', \"183-09 Asmá'\", "
                    "\"183-10 'Izzat\", '183-11 Mashíyyat', \"183-12 'Ilm\", "
                    "'183-13 Qudrat', '183-14 Qawl', '183-15 Masá’il', "
                    "'183-16 Sharaf', '183-17 Sulṭán', '183-18 Mulk', "
                    "'183-00 Ayyám-i-Há', \"183-19 'Alá'\", '184-01 Bahá', "
                    "'184-02 Jalál', '184-03 Jamál'], style=wx.CB_READONLY)\n"
                    "        widget_01.SetLabel('Month Index:')\n"
                    "        widget_01.SetBackgroundColour("
                    "wx.Colour(*[222, 237, 230]))\n"
                    "        widget_01.SetForegroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        widget_01.SetMinSize([228, 26])\n"
                    "        widget_01.Bind(wx.EVT_COMBOBOX, "
                    "self.set_dirty_flag)\n"
                    "        widget_01.mandatory = True\n"
                    "        sizer_1.Add(widget_01, [1, 0], [1, 1], "
                    "wx.ALIGN_BOTTOM | wx.ALL, 10)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.choice_combo_box(buff, panel, widget, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_color_check_box(self):
        """
        Test that the color_check_box method returns the code for
        a ColorCheckBox.
        """
        panel = 'fiscal'
        widget = 'widget_04'
        values = ['ColorCheckBox', 'bg_color', 'w_fg_color_1',
                  {'args': ['self', 'ID_ANY', 'fiscal_current', 'current'],
                   'font': 'font_10_normal', 'min': [20, 20], 'enabled': False,
                   'add': [0, 'ALIGN_BOTTOM | LEFT | RIGHT | TOP', 6],
                   'pos': [4, 1], 'span': [1, 1], 'dirty_event': True,
                   'financial': False, 'mandatory': False}]
        expected = ("        widget_04 = ColorCheckBox(self, wx.ID_ANY, "
                    "label='fiscal_current', name='current')\n"
                    "        widget_04.SetBackgroundColour("
                    "wx.Colour(*[210, 190, 255]))\n"
                    "        widget_04.SetForegroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        widget_04.SetMinSize([20, 20])\n"
                    "        widget_04.Bind(EVT_COLOR_CHECKBOX, "
                    "self.set_dirty_flag)\n"
                    "        widget_04.Enable(False)\n"
                    "        widget_04.mandatory = False\n"
                    "        sizer_1.Add(widget_04, [4, 1], [1, 1], "
                    "wx.ALIGN_BOTTOM | wx.LEFT | wx.RIGHT | wx.TOP, 6)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.color_check_box(buff, panel, widget, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_static_line(self):
        """
        Test that the static_line method returns the code for a StaticLine.
        """
        widget = 'line_00'
        values = ['StaticLine', 'w_bg_color_2',
                  {'args': ['self', 'ID_ANY'],
                   'add': [0, 'EXPAND | BOTTOM', 4], 'pos': [7, 0],
                   'span': [1, 2]}]
        expected = ("        line_00 = wx.StaticLine(self, wx.ID_ANY)\n"
                    "        line_00.SetBackgroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        sizer_1.Add(line_00, [7, 0], [1, 2], "
                    "wx.EXPAND | wx.BOTTOM, 4)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf.static_line(buff, widget, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_assemble_buttons(self):
        """
        Test that the assemble_buttons method returns the buttons used
        in many panels.
        """
        panel = 'organization'
        values = [('line_01',
                   ['StaticLine', 'w_bg_color_2',
                    {'args': ['self', 'ID_ANY'],
                     'add': [0, 'EXPAND | TOP', 20], 'pos': [9, 0],
                     'span': [1, 2]}]),
                  ('panel_0',
                   ['Panel', {'args': 'self', 'add': [0, 'CENTER', 0]}]),
                  ('sizer_2', ['BoxSizer']),
                  ('button_00',
                   ['Button', 'w_bg_color_2',
                    {'args': ['panel_0', 'ID_SAVE', ''],
                     'callback': 'button_save'}]),
                  ('button_01',
                   ['Button', 'w_bg_color_2',
                    {'args': ['panel_0', 'ID_CANCEL', ''],
                     'callback': 'button_cancel'}])]
        expected = ("        panel_0 = wx.Panel(self)\n"
                    "        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)\n"
                    "        button_00 = wx.Button(panel_0, wx.ID_SAVE, "
                    "label='')\n"
                    "        button_00.SetBackgroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        button_00.Bind(wx.EVT_BUTTON, self.button_save)\n"
                    "        sizer_2.Add(button_00, 0, wx.ALL, 10)\n"
                    "        button_01 = wx.Button(panel_0, wx.ID_CANCEL, "
                    "label='')\n"
                    "        button_01.SetBackgroundColour("
                    "wx.Colour(*[50, 50, 204]))\n"
                    "        button_01.Bind(wx.EVT_BUTTON, "
                    "self.button_cancel)\n"
                    "        sizer_2.Add(button_01, 0, wx.ALL, 10)\n"
                    "        panel_0.SetSizer(sizer_2)\n"
                    "        sizer_0.Add(panel_0, 0, wx.CENTER, 0)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf._assemble_buttons(buff, panel, values)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__create_save_cancel_events(self):
        """
        Test that the _create_save_cancel_events method returns the
        save and cancel event methods and properties.
        """
        expected = ("\n    def button_save(self, event):\n"
                    "        self.save = True\n"
                    "        event.Skip()\n\n"
                    "    @property\n"
                    "    def save(self):\n"
                    "        return self._save\n\n"
                    "    @save.setter\n"
                    "    def save(self, value):\n"
                    "        if self.dirty:\n"
                    "            mf = self._so.get_object('MainFrame')\n"
                    "            mf.statusbar_message = 'Saving data.'\n\n"
                    "        self._save = value\n\n"
                    "    def button_cancel(self, event):\n"
                    "        self.cancel = True\n"
                    "        event.Skip()\n\n"
                    "    @property\n"
                    "    def cancel(self):\n"
                    "        return self._cancel\n\n"
                    "    @cancel.setter\n"
                    "    def cancel(self, value):\n"
                    "        if self.dirty:\n"
                    "            mf = self._so.get_object('MainFrame')\n"
                    "            mf.statusbar_message = 'Restoring data.'\n\n"
                    "        self._cancel = value\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf._create_save_cancel_events(buff)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__create_fiscal_combobox_select_event(self):
        """
        Test that the _create_fiscal_combobox_select_event method returns
        the fiscal ComboBox select event method.
        """
        expected = ("\n    def get_selection(self, event):\n"
                    "        value = event.GetString()\n"
                    "        year, _, nyear = value.partition('-')\n"
                    "        db = self._so.get_object('Database')\n\n"
                    "        if year.isdecimal():\n"
                    "            db.populate_fiscal_panel(int(year))\n"
                    "            self.selected = True\n"
                    "        else:\n"
                    "            db.set_fiscal_panel(False, False, False)\n"
                    "            self.selected = False\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf._create_fiscal_combobox_select_event(buff)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__create_monthly_combobox_select_event(self):
        """
        Test that the _create_monthly_combobox_select_event method returns
        the monthly ComboBox select event method.
        """
        expected = ("\n    def get_selection(self, event):\n"
                    "        value = event.GetString()\n"
                    "        db = self._so.get_object('Database')\n"
                    "        db.update_monthly_panel(value)\n")
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf._create_monthly_combobox_select_event(buff)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__set_colors(self):
        """
        Test that the _set_colors method creates the foreground or
        background colors properly.

        NOTE: Since the PanelFactory only stores the last panel process
        not all color values can be tested.
        """
        err_msg0 = "Error: Cannot set more than one background color in '{}'"
        err_msg1 = "Error: Cannot set more than one foreground color in '{}'"
        values0 = ['ColorCheckBox', 'bg_color', 'w_fg_color_1']
        expect0 = ("        widget_04.SetBackgroundColour("
                   "wx.Colour(*[210, 190, 255]))\n"
                   "        widget_04.SetForegroundColour("
                   "wx.Colour(*[50, 50, 204]))\n")
        values1 = ['ComboBox', 'w_bg_color_1', 'w_fg_color_1']
        expect1 = ("        widget_02.SetBackgroundColour("
                   "wx.Colour(*[222, 237, 230]))\n"
                   "        widget_02.SetForegroundColour("
                   "wx.Colour(*[50, 50, 204]))\n")
        values2 = ['StaticLine', 'w_bg_color_2']
        expect2 = ("        line_00.SetBackgroundColour("
                   "wx.Colour(*[50, 50, 204]))\n")
        values3 = ['StaticLine', 'w_bg_color_3']
        expect3 = ("        line_00.SetBackgroundColour("
                   "wx.Colour(*[50, 50, 204]))\n")
        values4 = ['StaticText', 'w_fg_color_1']
        expect4 = ("        widget_00.SetForegroundColour("
                   "wx.Colour(*[50, 50, 204]))\n")
        values5 = ['ComboBox', 'w_bg_color_1', 'w_bg_color_2']
        values6 = ['ComboBox', 'w_fg_color_1', 'w_fg_color_2']
        data = (
            ('widget_04', values0, True, expect0),
            ('widget_02', values1, True, expect1),
            ('line_00', values2, True, expect2),
            #('line_00', values3, True, expect3),  # Only in budget.
            ('widget_00', values4, True, expect4),
            ('widget_02', values5, False, err_msg0.format('widget_02')),
            # None of the panels have more that one Foreground color
            #('widget_02', values6, False, err_msg1.format('widget_02')),
            )
        msg = "Expected '{}', found '{}'."

        for widget, values, valid, expected in data:
            with StringIO() as buff:
                if valid:
                    self.pf._set_colors(buff, widget, values)
                    result = buff.getvalue()
                    self.assertEqual(expected, result, msg.format(
                        expected, result))
                else:
                    with self.assertRaises(AssertionError) as cm:
                        self.pf._set_colors(buff, widget, values)

                    result = str(cm.exception)
                    self.assertEqual(expected, result, msg.format(
                        expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__set_font(self):
        """
        Test that the _set_font method returns a string representing
        the given font.
        """
        expected = ("        widget_00.SetFont(wx.Font(16, "
                    "wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, "
                    "wx.FONTWEIGHT_BOLD, 0, ''))\n")
        dict_ = {'args': ['self', 'ID_ANY', 'Organization Information'],
                 'font': 'font_16_bold', 'min': [-1, -1],
                 'add': [0, 'ALIGN_CENTER_HORIZONTAL | ALL', 6], 'pos': [0, 0],
                 'span': [1, 2]}
        msg = "Expected '{}', found '{}'."

        with StringIO() as buff:
            self.pf._set_font(buff, 'widget_00', dict_)
            result = buff.getvalue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__parse_font(self):
        """
        Test that the _parse_font method returns the parts of the font
        when given the fond string.
        """
        expected = (12, 'wx.FONTFAMILY_DEFAULT', 'wx.FONTSTYLE_NORMAL',
                    'wx.FONTWEIGHT_NORMAL', 0, '')
        font_type = 'font_12_normal'
        result = self.pf._parse_font(font_type)
        msg = "Expected '{}', found '{}'."
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__fix_flags(self):
        """
        Test that the _fix_flags method returns a string or integer
        depending on the incoming value.
        """
        data = (
            ('ALIGN_CENTER_HORIZONTAL | ALL',
             'wx.ALIGN_CENTER_HORIZONTAL | wx.ALL'),
            (wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 496),
            )
        msg = "Expected '{}', found '{}'."

        for flags, expected in data:
            result = self.pf._fix_flags(flags)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__set_add_to_sizer(self):
        """
        Test that the _set_add_to_sizer method adds items to the specified
        sizer.
        """
        values0 = ['StaticText', 'w_fg_color_1',
                   {'args': ['self', 'ID_ANY', 'Organization Information'],
                    'font': 'font_16_bold', 'min': [-1, -1],
                    'add': [0, 'ALIGN_CENTER_HORIZONTAL | ALL', 6],
                    'pos': [0, 0], 'span': [1, 2]}]
        expect0 = ("        sizer_1.Add(widget_00, [0, 0], [1, 2], "
                   "wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 6)\n")

        data = (
            ('widget_00', values0, expect0),
            )
        msg = "Expected '{}', found '{}'."

        for item, values, expected in data:
            with StringIO() as buff:
                self.pf._set_add_to_sizer(buff, item, values)
                result = buff.getvalue()
                self.assertEqual(expected, result, msg.format(
                    expected, result))
