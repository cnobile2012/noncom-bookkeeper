# -*- coding: utf-8 -*-
#
# test/test_utilities.py
#
__docformat__ = "restructuredtext en"

import unittest
import wx

from . import log, check_flag
from src.utilities import (GridBagSizer, ConfirmationDialog, _ClickPosition,
                           EventStaticText)


class BaseTests(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def create_objects(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.gbs = GridBagSizer()
        self.frame.SetSizer(self.gbs)
        widget = EventStaticText(self.frame, wx.ID_ANY,
                                 label="Two column wide text (move me).",
                                 style=0)
        self.gbs.Add(widget, (0, 0), (1, 2), wx.ALL, 6)
        num_widgets = 13
        num = 0

        for idx in range(num_widgets):
            dec = idx % 3
            if not dec: num += 1
            label = f"Widget {num}.{dec}"
            widget = EventStaticText(self.frame, -1, label, style=0)
            pos, span = (num, dec), (1, 1)
            self.gbs.Add(widget, pos, span, wx.ALIGN_CENTER | wx.ALL, 6)


class TestGridBagSizer(BaseTests):
    """
    Test if GridBagSizer gets swapped correctly.
    The GBS items use the following grid.

    Row Column 1    Column 2    Column 3
    --------------------------------------
    1   Two column wide text (move me).
    2   Widget 1.0  Widget 1.1  Widget 1.2
    3   Widget 2.0  Widget 2.1  Widget 2.2
    4   Widget 3.0  Widget 3.1  Widget 3.2
    5   Widget 4.0  Widget 4.1  Widget 4.2
    6   Widget 5.0
    """

    def __init__(self, name):
        super().__init__(name)

    @classmethod
    def setUpClass(self):
        self.create_objects(self)

    def setUp(self):
        check_flag(self.__class__.__name__)

    def check_rows(self, row, test_row):
        """
        """
        msg = "Expected 'Widget {}' found '{}'"
        values = list(test_row)
        cols = self.gbs.GetCols()

        for span, txt in test_row:
            if span > len(test_row):
                values.append((span, txt))

        num = len(values)

        for col in range(cols):
            if col < num:
                item = self.gbs.FindItemAtPosition((row, col))
                window = item.GetWindow()
                label = window.GetLabel()
                span, txt = values[col]
                self.assertIn(str(txt), label, msg.format(num, label))
            else:
                break

    ## def check_children(self):
    ##     for idx in range(14):
    ##         item = self.gbs.GetItem(idx)
    ##         label = item.GetWindow().GetLabel()
    ##         pos = item.GetPos()
    ##         print(f"Label: {label}, Position: {pos}")

    ##     print()

    #@unittest.skip("Temporarily skipped")
    def test_gbs_swap_rows_3_items_in_row(self):
        """
        Test that two rows are swapped correctly.
        """
        row0 = 1
        row1 = 2
        # Test that row0 is in its starting position.
        test_row = [(1, 1.0), (1, 1.1), (1, 1.2)]
        self.check_rows(row0, test_row)
        # Test that row1 is in its starting position.
        test_row = [(1, 2.0), (1, 2.1), (1, 2.2)]
        self.check_rows(row1, test_row)

        # Do the swap.
        self.gbs.swap_rows(row0, row1)

        # Test that row0 is in its ending position.
        test_row = [(1, 1.0), (1, 1.1), (1, 1.2)]
        self.check_rows(row1, test_row)
        # Test that row1 is in its ending position.
        test_row = [(1, 2.0), (1, 2.1), (1, 2.2)]
        self.check_rows(row0, test_row)

    #@unittest.skip("Temporarily skipped")
    def test_gbs_swap_rows_1_item_in_row(self):
        """
        Test that two rows are swapped correctly. row0 has a span of 2 and
        row1 has a span of 1.
        """
        row0 = 0
        row1 = 5
        # Test that row0 is in its starting position.
        test_row = [(2, 'Two column')]
        self.check_rows(row0, test_row)
        # Test that row1 is in its starting position.
        test_row = [(1, 5.0)]
        self.check_rows(row1, test_row)

        # Do the swap.
        self.gbs.swap_rows(row0, row1)

        # Test that row0 is in its ending position.
        test_row = [(1, 'Two column')]
        self.check_rows(row1, test_row)
        # Test that row1 is in its ending position.
        test_row = [(1, 5.0)]
        self.check_rows(row0, test_row)

    #@unittest.skip("Temporarily skipped")
    def test_highlight_row(self):
        """
        Test that a widget has it's background color changed.
        """
        def find_widget(row):
            windows = []

            for item in self.gbs.GetChildren():
                if item.GetPos()[0] == row:
                    windows.append(item.GetWindow())

            return windows

        row = 0
        # Test that the current color is the default.
        windows = find_widget(row)
        expected_color = (42, 46, 50, 255)

        for w in windows:
            found_color = w.GetBackgroundColour()
            msg = f"Expected {expected_color} found {found_color}."
            self.assertEqual(expected_color, found_color, msg)

        # Test that the color changed.
        expected_color = (29, 0, 255, 255)
        new_color = wx.Colour(*expected_color)
        self.gbs.highlight_row(row, new_color)
        windows = find_widget(row)

        for w in windows:
            found_color = w.GetBackgroundColour()
            msg = f"Expected {expected_color} found {found_color}."
            self.assertEqual(expected_color, found_color, msg)


class TestConfirmationDialog(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)
        self.frame = None

    def setUp(self):
        check_flag(self.__class__.__name__)

    def tearDown(self):
        if self.frame: self.frame.Destroy()

    def setup_config_dialog(self, msg, cap, *, bg_color=None, fg_color=None):
        app = wx.App()
        self.frame = wx.Frame(None)
        cd = ConfirmationDialog(self.frame, msg, cap, bg_color=bg_color,
                                fg_color=fg_color)

    def check_widgets(self, bg_color, fg_color, msg):
        # Test that the widgets have the proper properties.
        dialog = self.frame.GetChildren()[0]
        buttom_labels = ('Cancel', 'OK')
        color_msg = f"Color expected {bg_color} found {{}}."
        message_msg = f"Message wxpected '{msg}' found '{{}}'."

        for child in dialog.GetChildren():
            name = child.__class__.__name__

            if name == "StaticText":
                found_color = child.GetBackgroundColour()
                self.assertEqual(bg_color, found_color,
                                  color_msg.format(found_color))
                found_color = child.GetForegroundColour()
                self.assertEqual(fg_color, found_color,
                                  color_msg.format(found_color))
                found_msg = child.GetLabel()
                self.assertEqual(msg, found_msg,
                                  message_msg.format(found_msg))
            elif name == "Button":
                text = child.GetLabelText()
                msg = (f"Button text expected one of '{buttom_labels}' "
                       f"found '{text}'")
                self.assertIn(text, buttom_labels, msg)
            else:
                expected = 'StaticLine'
                msg = f"Expected '{expected}' found {name}"
                self.assertEqual(expected, name, msg)

    #@unittest.skip("Temporarily skipped")
    def test_creating_a_confirmation_dialog_with_defaults(self):
        """
        Test that a confirmation dialog is properly created with
        default values.
        """
        dlg_msg = "Test Default Message"
        caption = "Test Default Caption"
        self.setup_config_dialog(dlg_msg, caption)
        dialog = self.frame.GetChildren()[0]
        # Test that the dialog has the proper properties.
        default_bg_color = (220, 130, 143, 255)
        default_fg_color = (50, 50, 204, 255)
        found_color = dialog.GetBackgroundColour()
        msg = (f"Background color expected '{default_bg_color}' "
               f"found '{found_color}'.")
        self.assertEqual(default_bg_color, found_color, msg)
        found_cap = dialog.GetTitle()
        msg = f"Caption expected '{caption}' found '{found_cap}'."
        self.assertEqual(caption, found_cap, msg)
        self.check_widgets(default_bg_color, default_fg_color, dlg_msg)

    #@unittest.skip("Temporarily skipped")
    def test_creating_a_confirmation_dialog_with_updated_values(self):
        """
        Test that a confirmation dialog is properly created with
        updated values.
        """
        dlg_msg = "Test Updated Message"
        caption = "Test Updated Caption"
        new_bg_color = (255, 247, 236, 255) # Oyster
        new_fg_color = (0, 0, 127, 255) # Dark Gray
        self.setup_config_dialog(dlg_msg, caption, bg_color=new_bg_color,
                                 fg_color=new_fg_color)
        dialog = self.frame.GetChildren()[0]
        # Test that the dialog has the proper properties.
        found_color = dialog.GetBackgroundColour()
        msg = (f"Background color expected '{new_bg_color}' "
               f"found '{found_color}'.")
        self.assertEqual(new_bg_color, found_color, msg)
        found_cap = dialog.GetTitle()
        msg = f"Caption expected '{caption}' found '{found_cap}'."
        self.assertEqual(caption, found_cap, msg)
        self.check_widgets(new_bg_color, new_fg_color, dlg_msg)


class Test_ClickPosition(unittest.TestCase):
    """
    The _ClickPosition() class uses the Borg pattern.
    """

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.widget_name = "NewWidget"
        # Get rid of any previous data, since we are dealing with a
        # borg class.
        self.cp._new_types.clear()

    @classmethod
    def setUpClass(self):
        self.cp = _ClickPosition()

    #@unittest.skip("Temporarily skipped")
    def test_get_new_event_type(self):
        """
        Test that a new even type is returned from wxPython.
        """
        event_type = self.cp.get_new_event_type(self.widget_name)
        msg = f"Event type expected an integer found {event_type}."
        self.assertTrue(isinstance(event_type, int), msg)

    #@unittest.skip("Temporarily skipped")
    def test_get_click_position_event_type_not_set(self):
        """
        Test that get_click_position() rases an AssertionError.
        """
        err_msg = "get_new_event_type"

        with self.assertRaises(AssertionError) as cm:
            self.cp.get_click_position(self.widget_name)

        message = str(cm.exception)
        msg = f"Error message expected {err_msg} found {message}"
        self.assertIn(err_msg, message, msg)

    #@unittest.skip("Temporarily skipped")
    def test_get_click_position_event_type(self):
        """
        Test that get_click_position() returns the new event.
        """
        event_type = self.cp.get_new_event_type(self.widget_name)
        event = self.cp.get_click_position(self.widget_name)
        expected = 'wx.core.PyEventBinder'
        msg = f"Event expected '{expected}' found {event}."
        self.assertIn(expected, str(event), msg)


#class TestWidgetEvent(BaseTests):
#    """
#    Test the WidgetEvent class. This class stores values of the widget and
#    puts them on the event object that is passed to event handlers.
#    """
# The WidgetEvent class cannot be tested directly.
# It's tested in the TestEventStaticText class.
#


class TestEventStaticText(BaseTests):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.create_objects()

    def tearDown(self):
        self.frame.Close()

    def get_widget(self, index=0):
        return self.frame.GetChildren()[index]

    def simulate_left_click(self, widget):
        """
        Thanks to OpenAI for this method.
        This method will not work without the toplevel window shown.
        """
        simulator = wx.UIActionSimulator()
        rect = widget.GetScreenRect()
        center = rect.GetPosition() + rect.GetSize() / 2
        simulator.MouseMove(center)
        simulator.MouseClick()

    #@unittest.skip("Temporarily skipped")
    def test_new_event_type(self):
        """
        Test that a new event type is returned.
        """
        widget = self.get_widget()
        event_type = widget.new_event_type
        msg = f"Event type expected an integer found {event_type}."
        self.assertTrue(isinstance(event_type, int), msg)

    #@unittest.skip("Temporarily skipped")
    def test_EVT_CLICK_POSITION(self):
        """
        Test that a new event is returned.
        """
        widget = self.get_widget()
        #widget.new_event_type
        event = widget.EVT_CLICK_POSITION
        expected = 'wx.core.PyEventBinder'
        msg = f"Event expected '{expected}' found {event}."
        self.assertIn(expected, str(event), msg)

    @unittest.skip("Temporarily skipped")
    def test_WidgetEvent_data(self):
        """
        Test that the WidgetEvent data returns properly.
        """
        self.frame.Show()
        widget = self.get_widget(1)
        expected_label = widget.GetLabel()

        def event_click(event):
            # Test the position.
            expected = (1, 0)
            value = event.get_value()
            msg = f"Value expected '{expected}' found '{value}'."
            self.assertEqual(expected, value, msg)
            # Test the window.
            window = event.get_window()
            label = window.GetLabel()
            msg = f"Label expected '{expected_label}' found '{label}'."
            self.assertEqual(expected_label, label, msg)
            # Exit GUI
            self.app.ExitMainLoop()

        #widget.new_event_type
        self.frame.Bind(widget.EVT_CLICK_POSITION, event_click,
                        id=widget.GetId())
        self.simulate_left_click(widget)
        self.app.MainLoop()
