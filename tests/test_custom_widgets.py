# -*- coding: utf-8 -*-
#
# tests/test_custom_widgits.py
#
__docformat__ = "restructuredtext en"

import unittest
import wx

from unittest.mock import patch, MagicMock, ANY
from badidatetime import date, MONTHNAMES

from src.custom_widgits import (
    ordered_month, CustomTextCtrl, EVT_BADI_DATE_CHANGED, BadiDateChangedEvent,
    BadiCalendarPopup, BadiDatePickerCtrl, EVT_COLOR_CHECKBOX, ColorCheckBox,
    EVT_FLAT_ARROW, FlatArrowClickEvent, FlatArrowButton)

from . import FakeFrame, FakePanel, check_flag


class TestFunctions(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)

    #@unittest.skip("Temporarily skipped")
    def test_ordered_month(self):
        """
        Test that the ordered_month function returns a dict of month
        number and name.
        """
        months = ordered_month()
        msg = "Expected {}, found {}."
        expected_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                          12, 13, 14, 15, 16, 17, 18, 0, 19]
        expected_month = MONTHNAMES

        for idx, (order, month) in enumerate(months.items()):
            expect_ord = expected_order[idx]
            self.assertEqual(expect_ord, order, msg.format(expect_ord, order))
            expect_mon = expected_month[idx]
            self.assertEqual(expect_mon, month, msg.format(expect_mon, month))


class TestCustomTextCtrl(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    @classmethod
    def setUpClass(cls):
        cls.app = wx.GetApp()

        if cls.app is None:
            cls.app = wx.App(False)

    @classmethod
    def tearDownClass(cls):
        if wx.GetApp():
            wx.GetApp().Destroy()

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.frame = FakeFrame()
        self.panel = FakePanel(self.frame)
        self.widget = CustomTextCtrl(self.panel)
        self.panel.sizer.Add(self.widget, 0, wx.CENTER | wx.ALL, 10)

    def tearDown(self):
        self.widget = None
        self.panel = None
        self.frame.Destroy()
        self.frame = None

    def _key_event(self, key_code, shift=False):
        event = MagicMock()
        event.GetKeyCode.return_value = key_code
        event.ShiftDown.return_value = shift
        event.Skip = MagicMock()
        return event

    #@unittest.skip("Temporarily skipped")
    def test_on_paint(self):
        """
        Test that the on_paint method (event) works as expected.
        """
        with patch('wx.AutoBufferedPaintDC') as mock_dc_class:
            self.widget.has_focus = True
            self.widget.cursor_pos = 2
            mock_dc = mock_dc_class.return_value
            mock_dc.GetTextExtent.side_effect = [(40, 14), (20, 14)]
            mock_event = MagicMock()
            mock_event.GetEventObject.return_value = self.widget
            self.widget.on_paint(mock_event)
            mock_dc.DrawText.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_click(self):
        """
        Test that the on_click method (event) works as expected.
        """
        event = wx.MouseEvent(wx.wxEVT_LEFT_DOWN)
        event.SetEventObject(self.widget)

        with patch.object(self.widget, 'SetFocus') as mock_setfocus:
            self.widget.GetEventHandler().ProcessEvent(event)
            mock_setfocus.assert_called_once()
            self.assertTrue(event.GetSkipped())

    #@unittest.skip("Temporarily skipped")
    def test_on_char_printable(self):
        """
        Test that the on_char method (event) works as expected.
        """
        self.widget.text = 'ac'
        self.widget.cursor_pos = 1

        with patch.object(self.widget, 'Refresh') as mock_refresh:
            self.widget.on_char(self._key_event(ord('b')))
            self.assertEqual(self.widget.text, 'abc')
            self.assertEqual(self.widget.cursor_pos, 2)
            mock_refresh.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_char_backspace(self):
        """
        Test that the on_char method (event) works as expected.
        """
        self.widget.text = 'abc'
        self.widget.cursor_pos = 2
        self.widget.on_char(self._key_event(wx.WXK_BACK))
        self.assertEqual(self.widget.text, 'ac')
        self.assertEqual(self.widget.cursor_pos, 1)

    #@unittest.skip("Temporarily skipped")
    def test_on_char_backspace_at_start(self):
        """
        Test that the on_char method (event) works as expected.
        """
        self.widget.text = 'abc'
        self.widget.cursor_pos = 0
        self.widget.on_char(self._key_event(wx.WXK_BACK))
        self.assertEqual(self.widget.text, 'abc')
        self.assertEqual(self.widget.cursor_pos, 0)

    #@unittest.skip("Temporarily skipped")
    def test_on_char_left_arrow(self):
        self.widget.cursor_pos = 2
        self.widget.on_char(self._key_event(wx.WXK_LEFT))
        self.assertEqual(self.widget.cursor_pos, 1)

    #@unittest.skip("Temporarily skipped")
    def test_on_char_right_arrow_clamped(self):
        self.widget.text = 'ab'
        self.widget.cursor_pos = 2
        self.widget.on_char(self._key_event(wx.WXK_RIGHT))
        self.assertEqual(self.widget.cursor_pos, 2)

    #@unittest.skip("Temporarily skipped")
    def test_on_char_tab_forward(self):
        with patch.object(self.widget, 'Navigate') as mock_nav:
            self.widget.on_char(self._key_event(wx.WXK_TAB))
            mock_nav.assert_called_once_with(wx.NavigationKeyEvent.IsForward)

    #@unittest.skip("Temporarily skipped")
    def test_on_char_tab_shift_backward(self):
        with patch.object(self.widget, 'Navigate') as mock_nav:
            self.widget.on_char(self._key_event(wx.WXK_TAB, shift=True))
            mock_nav.assert_called_once_with(wx.NavigationKeyEvent.IsBackward)

    #@unittest.skip("Temporarily skipped")
    def test_on_char_unhandled_key_skips(self):
        event = self._key_event(wx.WXK_F1)
        self.widget.on_char(event)
        event.Skip.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_focus(self):
        """
        Test that the on_focus event firers correctly.
        """
        event = wx.FocusEvent(wx.wxEVT_SET_FOCUS, self.widget.GetId())
        event.SetEventObject(self.widget)
        self.widget.has_focus = False

        with patch.object(self.widget, 'Refresh') as mock_refresh:
            self.widget.GetEventHandler().ProcessEvent(event)
            self.assertTrue(self.widget.has_focus)
            mock_refresh.assert_called_once()
            self.assertTrue(event.GetSkipped())

    #@unittest.skip("Temporarily skipped")
    def test_on_kill_focus(self):
        """
        Test that the on_kill_focus event firers correctly.
        """
        event = wx.FocusEvent(wx.wxEVT_KILL_FOCUS, self.widget.GetId())
        event.SetEventObject(self.widget)
        self.widget.has_focus = True

        with patch.object(self.widget, 'Refresh') as mock_refresh:
            self.widget.GetEventHandler().ProcessEvent(event)
            self.assertFalse(self.widget.has_focus)
            mock_refresh.assert_called_once()
            self.assertTrue(event.GetSkipped())

    #@unittest.skip("Temporarily skipped")
    def test_Set_GetValue(self):
        """
        Test that the GetValue event firers correctly.
        """
        data = ('', 'Test String')
        msg = "Expected {}, found {}."

        for value in data:
            self.widget.SetValue(value)
            result = self.widget.GetValue()
            self.assertEqual(value, result, msg.format(value, result))


class TestBadiDateChangedEvent(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.bdate = date(182, 4, 6)
        self.bdce = BadiDateChangedEvent(self.bdate)

    #@unittest.skip("Temporarily skipped")
    def test_constructor(self):
        """
        Test that the __init__ constructor sets the Badi date correctly.
        """
        msg = f"Expected {self.bdate}, found {self.bdce._bdate}."
        self.assertEqual(self.bdate, self.bdce._bdate, msg)

    #@unittest.skip("Temporarily skipped")
    def test_GetBadiDate(self):
        """
        Test that the GetBadiDate method returns the Badi date.
        """
        bdate = self.bdce.GetBadiDate()
        msg = f"Expected {self.bdate}, found {bdate}."
        self.assertEqual(self.bdate, bdate, msg)


class TestBadiCalendarPopup(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    @classmethod
    def setUpClass(cls):
        cls.app = wx.GetApp()

        if cls.app is None:
            cls.app = wx.App(False)

    @classmethod
    def tearDownClass(cls):
        if wx.GetApp():
            wx.GetApp().Destroy()

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.frame = FakeFrame()
        self.panel = FakePanel(self.frame)
        bdate = date(183, 3, 5)
        self.widget = BadiCalendarPopup(self.panel, bdate=bdate)
        self.panel.sizer.Add(self.widget, 0, wx.CENTER | wx.ALL, 10)

    def tearDown(self):
        self.widget = None
        self.panel = None
        self.frame.Destroy()
        self.frame = None

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_border(self):
        """
        Test that the on_paint_border method sets the pen, brush, and
        rectangle correctly.
        """
        with patch('wx.PaintDC') as mock_dc_class:
            mock_dc = mock_dc_class.return_value
            mock_event = MagicMock()
            mock_event.GetEventObject.return_value = self.widget
            self.widget.on_paint_border(mock_event)
            mock_dc.DrawRectangle.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test__populate_days(self):
        """
        Test that the _populate_days method populates and highlights the day
        correctly.
        """
        data = (
            (1, 1, (wx.Colour(230, 240, 255, 255),
                    wx.Colour(180, 180, 180, 255))),
            (0, 1, (wx.Colour(230, 240, 255, 255),
                    wx.Colour(180, 180, 180, 255))),
            )
        msg = "Expected '{}', found '{}'."

        for month, day, expected in data:
            self.widget.bdate = date(183, month, day)

            with patch('badidatetime.date.today',
                       return_value=self.widget.bdate):
                self.widget._populate_days()
                child = self.widget.grid_sizer.GetChildren()[day-1]
                window = child.GetWindow()
                result = window.GetBackgroundColour()
                self.assertEqual(expected[0], result, msg.format(
                    expected[0], result))

                child = self.widget.grid_sizer.GetChildren()[day]
                window = child.GetWindow()
                result = window.GetBackgroundColour()
                self.assertEqual(expected[1], result, msg.format(
                    expected[1], result))

    #@unittest.skip("Temporarily skipped")
    def test__max_days_in_month(self):
        """
        Test that the _max_days_in_month method the maximum days in any
        Badi month.
        """
        data = (
            (183, 1, 19),
            (183, 0, 4),
            )
        msg = "Expected '{}', founf '{}'."

        for year, month, expected in data:
            result = self.widget._max_days_in_month(year, month)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_on_day_clicked_with_callback(self):
        """
        Test that the on_day_clicked method sets the clicked date.
        """
        self.widget.bdate = date(180, 1, 1)
        day_btn = wx.Button(self.widget, label='15')
        day_btn.day = 15
        day_btn.Bind(wx.EVT_BUTTON, self.widget.on_day_clicked)

        with (patch.object(self.widget, 'Dismiss') as mock_dismiss,
              patch.object(self.widget, 'on_date_selected') as mock_callback):
            event = wx.CommandEvent(wx.wxEVT_BUTTON, day_btn.GetId())
            event.SetEventObject(day_btn)
            day_btn.GetEventHandler().ProcessEvent(event)
            mock_callback.assert_called_once()
            new_date = mock_callback.call_args[0][0]
            self.assertEqual(new_date.year, self.widget.bdate.year)
            self.assertEqual(new_date.month, self.widget.bdate.month)
            self.assertEqual(new_date.day, 15)
            mock_dismiss.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_day_clicked_no_callback(self):
        self.widget.bdate = date(180, 1, 1)
        self.widget.on_date_selected = None
        day_btn = wx.Button(self.widget, label='19')
        day_btn.day = 19
        day_btn.Bind(wx.EVT_BUTTON, self.widget.on_day_clicked)

        with patch.object(self.widget, 'Dismiss') as mock_dismiss:
            event = wx.CommandEvent(wx.wxEVT_BUTTON, day_btn.GetId())
            event.SetEventObject(day_btn)
            day_btn.GetEventHandler().ProcessEvent(event)
            # Should not raise even with no callback set
            mock_dismiss.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_prev_year(self):
        """
        Test that the on_prev_year method sets the previous year.
        """
        m, _, cur_year = self.widget.header.GetLabel().partition(' ')
        self.widget.on_prev_year(None)
        m, _, pre_year = self.widget.header.GetLabel().partition(' ')
        self.assertEqual(int(cur_year)-1, int(pre_year))

    #@unittest.skip("Temporarily skipped")
    def test_on_next_year(self):
        """
        Test that the on_next_year method sets the next year.
        """
        m, _, cur_year = self.widget.header.GetLabel().partition(' ')
        self.widget.on_next_year(None)
        m, _, nxt_year = self.widget.header.GetLabel().partition(' ')
        self.assertEqual(int(cur_year)+1, int(nxt_year))

    #@unittest.skip("Temporarily skipped")
    def test_on_prev_month(self):
        """
        Test that the on_prev_month method sets the previous month and year
        if necessary.
        """
        data = (
            ('Jamál', ('Jalál', '183')),
            ('Jalál', ('Bahá', '183')),
            ('Bahá', ("'Alá'", '182')),
            )
        msg = "Expected '{}', found '{}'."

        for cur_mth, expected in data:
            self.widget.on_prev_month(None)
            pre_mth, _, year = self.widget.header.GetLabel().partition(' ')
            self.assertEqual(expected[0], pre_mth, msg.format(
                expected[0], pre_mth))
            self.assertEqual(expected[1], year, msg.format(expected[1], year))

    #@unittest.skip("Temporarily skipped")
    def test_on_next_month(self):
        """
        Test that the on_next_month method sets the next month and year
        if necessary.
        """
        self.widget.bdate = date(183, 18, 1)
        self.widget.update_header()  # Update the current month and/or year
        data = (
            ('Mulk', ('Ayyám-i-Há', '183')),
            ('Ayyám-i-Há', ("'Alá'", '183')),
            ("'Alá'", ('Bahá', '184')),
            )
        msg = "Expected '{}', found '{}'."

        for cur_mth, expected in data:
            self.widget.on_next_month(None)
            nxt_mth, _, year = self.widget.header.GetLabel().partition(' ')
            self.assertEqual(expected[0], nxt_mth, msg.format(
                expected[0], nxt_mth))
            self.assertEqual(expected[1], year, msg.format(expected[1], year))


class TestBadiDatePickerCtrl(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    @classmethod
    def setUpClass(cls):
        cls.app = wx.GetApp()

        if cls.app is None:
            cls.app = wx.App(False)

    @classmethod
    def tearDownClass(cls):
        if wx.GetApp():
            wx.GetApp().Destroy()

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.frame = FakeFrame()
        self.panel = FakePanel(self.frame)
        bdate = date(183, 3, 5)
        self.widget = BadiDatePickerCtrl(self.panel, bdate=bdate)
        self.panel.sizer.Add(self.widget, 0, wx.CENTER | wx.ALL, 10)

    def tearDown(self):
        self.widget = None
        self.panel = None
        self.frame.Destroy()
        self.frame = None

    def _setup_on_change_mock(self, date, text_date):
        self.widget.bdate = date
        self.widget.text_ctrl = MagicMock()
        self.widget.text_ctrl.GetValue.return_value = text_date
        event = MagicMock()

        with patch('wx.PostEvent') as mock_post:
            self.widget.on_change(event)

        return event, mock_post

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_draws_rounded_rect(self):
        """
        Test that the on_paint method drawn a rounded rectangle.
        """
        event = MagicMock()

        with (patch('wx.AutoBufferedPaintDC'),
              patch('wx.GraphicsContext.Create') as mock_create):
            mock_gc = MagicMock()
            mock_create.return_value = mock_gc
            self.widget.on_paint(event)
            mock_gc.SetBrush.assert_called_once()
            mock_gc.SetPen.assert_called_once()
            mock_gc.DrawRoundedRectangle.assert_called_once()
            # Confirm the rect was deflated before drawing — catches an
            # accidental removal of rect.Deflate(1, 1)
            call_args = mock_gc.DrawRoundedRectangle.call_args[0]
            client_rect = self.widget.GetClientRect()
            self.assertEqual(call_args[0], client_rect.x + 1)
            self.assertEqual(call_args[1], client_rect.y + 1)
            self.assertEqual(call_args[2], client_rect.width - 2)
            self.assertEqual(call_args[3], client_rect.height - 2)
            self.assertEqual(call_args[4], 4)  # corner radius

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_no_graphics_context_does_nothing(self):
        """
        Test that the on_paint method does nothing if no graphics.
        """
        event = MagicMock()

        with (patch('wx.AutoBufferedPaintDC'),
              patch('wx.GraphicsContext.Create', return_value=None)):
            # Should not raise even though gc is falsy
            self.widget.on_paint(event)

    #@unittest.skip("Temporarily skipped")
    def test_on_change_valid_new_date(self):
        """
        Test that the on_change method changes the date properly.
        """
        bdate = date(180, 1, 1)
        event, mock_post = self._setup_on_change_mock(bdate, '0180-02-03')
        self.assertEqual(self.widget.bdate, date(180, 2, 3))
        mock_post.assert_called_once()
        posted_target, posted_event = mock_post.call_args[0]
        self.assertIs(posted_target, self.widget)
        self.assertEqual(posted_event.GetBadiDate(), self.widget.bdate)
        event.Skip.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_change_same_date_no_event(self):
        bdate = date(180, 2, 3)
        event, mock_post = self._setup_on_change_mock(bdate, bdate.isoformat())
        mock_post.assert_not_called()
        event.Skip.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_change_bad_field_lengths_no_change(self):
        bdate = date(180, 2, 3)
        event, mock_post = self._setup_on_change_mock(bdate, '180-2-3')
        self.assertEqual(self.widget.bdate, bdate)
        mock_post.assert_not_called()
        event.Skip.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_change_wrong_part_count_no_change(self):
        bdate = date(180, 2, 3)
        event, mock_post = self._setup_on_change_mock(bdate, '0180-02')
        self.assertEqual(self.widget.bdate, bdate)
        mock_post.assert_not_called()
        event.Skip.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_show_popup_calendar(self):
        """
        Test that the show_popup_calendar method shows the popup calendar.
        """
        self.widget.bdate = date(180, 5, 10)
        event = MagicMock()
        fake_screen_pos = wx.Point(100, 200)

        with (patch('src.custom_widgits.BadiCalendarPopup') as mock_popup_cls,
              patch.object(self.widget, 'ClientToScreen',
                           return_value=fake_screen_pos) as mock_c2s):
            mock_popup = mock_popup_cls.return_value
            self.widget.show_popup_calendar(event)

        mock_popup_cls.assert_called_once_with(self.widget,
                                               bdate=self.widget.bdate)
        self.assertEqual(mock_popup.on_date_selected,
                         self.widget._on_popup_date_selected)
        mock_c2s.assert_called_once_with(
            self.widget.calendar_btn.GetPosition())
        btn_size = self.widget.calendar_btn.GetSize()
        mock_popup.Position.assert_called_once_with(fake_screen_pos,
                                                    (0, btn_size.height))
        mock_popup.Popup.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_show_popup_calendar_wires_callback(self):
        """
        Test that the show_popup_calendar method calls the on_date_selected.
        """
        event = MagicMock()
        fake_screen_pos = wx.Point(100, 200)

        with (patch('src.custom_widgits.BadiCalendarPopup') as mock_popup_cls,
              patch.object(self.widget, 'ClientToScreen',
                           return_value=fake_screen_pos) as mock_c2s):
            mock_popup = mock_popup_cls.return_value
            self.widget.show_popup_calendar(event)

            # Simulate the popup calling back, as it would on a real date click
            new_bdate = date(180, 3, 7)

            with (patch.object(self.widget, 'SetValue') as mock_set_value,
                  patch('wx.PostEvent') as mock_post):
                mock_popup.on_date_selected(new_bdate)

        mock_set_value.assert_called_once_with(new_bdate)
        mock_post.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test__on_popup_date_selected(self):
        """
        Test that the _on_popup_date_selected method posts the event.
        """
        new_bdate = date(180, 5, 12)

        with (patch.object(self.widget, 'SetValue') as mock_set_value,
              patch('wx.PostEvent') as mock_post):
            self.widget._on_popup_date_selected(new_bdate)

        mock_set_value.assert_called_once_with(new_bdate)
        mock_post.assert_called_once()
        posted_target, posted_event = mock_post.call_args[0]
        self.assertIs(posted_target, self.widget)
        self.assertEqual(posted_event.GetBadiDate(), new_bdate)

    #@unittest.skip("Temporarily skipped")
    def test_GetValue_and_SetValue(self):
        """
        Test that the GetValue and SetValue methods gets and sets a
        Badi date value.
        """
        orig = date(183, 3, 5)
        data = (
            (orig, orig),
            ('', ''),
            )

        for bdate, expected in data:
            self.widget.SetValue(bdate)
            result = self.widget.GetValue()
            self.assertEqual(expected, result)


class TestColorCheckBox(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    @classmethod
    def setUpClass(cls):
        cls.app = wx.GetApp()

        if cls.app is None:
            cls.app = wx.App(False)

    @classmethod
    def tearDownClass(cls):
        if wx.GetApp():
            wx.GetApp().Destroy()

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.frame = FakeFrame()
        self.panel = FakePanel(self.frame)
        self.widget = ColorCheckBox(self.panel, label="Test Label",
                                    name="Test Name")
        self.panel.sizer.Add(self.widget, 0, wx.CENTER | wx.ALL, 10)

    def tearDown(self):
        self.widget = None
        self.panel = None
        self.frame.Destroy()
        self.frame = None

    def _make_paint_dc_mock(self, mock_dc_class, text_size=(40, 14)):
        mock_dc = mock_dc_class.return_value
        mock_dc.GetTextExtent.return_value = text_size
        return mock_dc

    def _setup_on_paint(self, pos, enabled, checked):
        self.widget.label = 'Red'
        self.widget.label_position = pos
        self.widget.enabled = enabled
        self.widget.checked = checked
        event = MagicMock()

        with (patch('wx.BufferedPaintDC') as mock_dc_class,
              patch('wx.Pen') as mock_pen):
            mock_dc = self._make_paint_dc_mock(mock_dc_class)
            self.widget.on_paint(event)

        return event, mock_dc, mock_pen

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_unchecked_enabled_label_right(self):
        """
        Test that the on_paint method paints correctly when unchecked.
        """
        event, mock_dc, mock_pen = self._setup_on_paint('right', True, False)
        mock_dc.Clear.assert_called_once()
        # 2 background/box rects drawn, no check-mark lines since unchecked
        self.assertEqual(mock_dc.DrawRectangle.call_count, 2)
        mock_dc.DrawLine.assert_not_called()
        mock_dc.DrawText.assert_called_once_with(self.widget.label, ANY, ANY)

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_checked_draws_check_mark(self):
        """
        Test that the on_paint method paints correctly when checked.
        """
        event, mock_dc, mock_pen = self._setup_on_paint('right', True, True)
        self.assertEqual(mock_dc.DrawLine.call_count, 2)

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_disabled_uses_disabled_colors(self):
        """
        Test that the on_paint method paints correctly when disabled.
        """
        event, mock_dc, mock_pen = self._setup_on_paint('right', False, False)
        # 2nd SetPen call (box border) should use disabled_color, not bb_color
        pen_calls = mock_pen.call_args_list
        self.assertEqual(pen_calls[1][0][0], self.widget.disabled_color)

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_label_left_positions_box_after_text(self):
        """
        Test that the on_paint method paints correctly after text entered.
        """
        event, mock_dc, mock_pen = self._setup_on_paint('left', True, False)
        text_x, text_y = mock_dc.DrawText.call_args[0][1:3]
        # second rect = checkbox
        box_x = mock_dc.DrawRectangle.call_args_list[1][0][0]
        self.assertEqual(text_x, 0)
        self.assertEqual(box_x, 40 + 6)  # text_width + margin

    def _setup_on_click(self, enabled, checked):
        self.widget.enabled = enabled
        self.widget.checked = checked

        with (patch.object(self.widget, 'Refresh') as mock_refresh,
              patch('wx.PostEvent') as mock_post):
            self.widget.on_click(MagicMock())

        return mock_refresh, mock_post

    #@unittest.skip("Temporarily skipped")
    def test_on_click_toggles_and_posts_event(self):
        """
        Test that the on_click method toggles and posts events.
        """
        mock_refresh, mock_post = self._setup_on_click(True, False)
        self.assertTrue(self.widget.checked)
        mock_refresh.assert_called_once()
        mock_post.assert_called_once()
        posted_target, posted_event = mock_post.call_args[0]
        self.assertIs(posted_target, self.widget)
        self.assertEqual(posted_event.GetInt(), 1)

    #@unittest.skip("Temporarily skipped")
    def test_on_click_toggles_back_to_unchecked(self):
        """
        Test that the on_click method toggles to unchecked.
        """
        mock_refresh, mock_post = self._setup_on_click(True, True)
        self.assertFalse(self.widget.checked)
        posted_event = mock_post.call_args[0][1]
        self.assertEqual(posted_event.GetInt(), 0)

    #@unittest.skip("Temporarily skipped")
    def test_on_click_disabled_does_nothing(self):
        """
        Test that the on_click method disables clicking.
        """
        mock_refresh, mock_post = self._setup_on_click(False, False)
        self.assertFalse(self.widget.checked)
        mock_refresh.assert_not_called()

    #@unittest.skip("Temporarily skipped")
    def test_notify_posts_event_with_current_value(self):
        """
        Test that the Notify method posts event with current value.
        """
        with (patch.object(self.widget, 'GetValue',
                           return_value=True) as mock_getvalue,
              patch('wx.PostEvent') as mock_post):
            self.widget.Notify()

        mock_getvalue.assert_called_once()
        mock_post.assert_called_once()
        posted_target, posted_event = mock_post.call_args[0]
        self.assertIs(posted_target, self.widget)
        self.assertTrue(posted_event.state)

    #@unittest.skip("Temporarily skipped")
    def test_SetReadOnly(self):
        """
        Test that the SetReadOnly method sets the read_only flag and sets
        the Enable method to False.
        """
        data = (
            (True, False, (True, False)),
            (False, False, (False, False)),
            )
        msg = "Expected '{}', found '{}'."

        for set_value, enable_value, expected in data:
            self.widget.Enable(True)
            self.widget.SetReadOnly(set_value)
            result = self.widget.read_only
            self.assertEqual(expected[0], result, msg.format(
                expected[0], result))
            result = self.widget.enabled
            self.assertEqual(expected[1], result, msg.format(
                expected[1], result))

    #@unittest.skip("Temporarily skipped")
    def test_GetValue_and_SetValue(self):
        """
        Test that the GetValue and SetValue methods sets and gets the
        value in various situations.
        """
        data = (
            (False, False, False),
            (False, True, False),
            (True, False, True),
            (True, True, False),
            )
        msg = "Expected '{}', found '{}'."

        for set_value, read_only, expected in data:
            self.widget.checked = False
            self.widget.read_only = read_only
            self.widget.SetValue(set_value)
            result = self.widget.GetValue()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_IsEditable(self):
        """
        Test that the IsEditable method correctly determines if the widget
        is editable.
        """
        data = (
            (True, False),
            (False, True),
            )
        msg = "Expected '{}', found '{}'."

        for read_only, expected in data:
            self.widget.read_only = read_only
            result = self.widget.IsEditable()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_Enable_and_IsEnabled(self):
        """
        Test that the Enable and IsEnabled method determine if the widget
        is editable.
        """
        data = (
            (False, False),
            (True, True),
            )
        msg = "Expected '{}', found '{}'."

        for set_value, expected in data:
            self.widget.Enable(set_value)
            result = self.widget.IsEnabled()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_SetSize(self):
        """
        Test that the SetSize method sets a cusom size or the default.
        """
        data = (
            (None, (120, 24)),
            ((200, 34), (200, 34)),
            )
        msg = "Expected '{}', found '{}'."

        for set_value, expected in data:
            if set_value:
                self.widget.SetSize(set_value)
            else:
                self.widget.SetSize()

            result = self.widget.GetMinSize()
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test_GetLabelText(self):
        """
        Test that the GetLabelText method returns the widget label.
        """
        msg = "Expected '{}', found '{}'."
        expected = self.widget.label
        result = self.widget.GetLabelText()
        self.assertEqual(expected, result, msg.format(expected, result))


class TestFlatArrowClickEvent(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)

    #@unittest.skip("Temporarily skipped")
    def test_GetDirection(self):
        """
        Test that the GetBadiDate method returns the Badi date.
        """
        data = ('left', 'right')

        for direction in data:
            face = FlatArrowClickEvent(direction)
            result = face.GetDirection()
            self.assertEqual(direction, result)


class TestFlatArrowButton(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    @classmethod
    def setUpClass(cls):
        cls.app = wx.GetApp()

        if cls.app is None:
            cls.app = wx.App(False)

    @classmethod
    def tearDownClass(cls):
        if wx.GetApp():
            wx.GetApp().Destroy()

    def setUp(self):
        check_flag(self.__class__.__name__)
        self.frame = FakeFrame()
        self.panel = FakePanel(self.frame)
        self.widget = FlatArrowButton(self.panel)
        self.panel.sizer.Add(self.widget, 0, wx.CENTER | wx.ALL, 10)

    def tearDown(self):
        self.widget = None
        self.panel = None
        self.frame.Destroy()
        self.frame = None

    #@unittest.skip("Temporarily skipped")
    def test_on_enter_sets_hover_true(self):
        """
        Test that the on_enter method sets hover to True.
        """
        self.widget.hover = False

        with patch.object(self.widget, 'Refresh') as mock_refresh:
            self.widget.on_enter(MagicMock())

        self.assertTrue(self.widget.hover)
        mock_refresh.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_leave_sets_hover_false(self):
        """
        Test that the on_leave method sets hover to False.
        """
        self.widget.hover = True

        with patch.object(self.widget, 'Refresh') as mock_refresh:
            self.widget.on_leave(MagicMock())

        self.assertFalse(self.widget.hover)
        mock_refresh.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_click_posts_event_with_direction(self):
        """
        Test that the on_click method posts an event direction.
        """
        self.widget.direction = 'up'

        with patch('wx.PostEvent') as mock_post:
            self.widget.on_click(MagicMock())

        mock_post.assert_called_once()
        posted_target, posted_event = mock_post.call_args[0]
        self.assertIs(posted_target, self.widget)
        self.assertEqual(posted_event.direction, 'up')

    def _setup_on_paint(self, hover, label='▲'):
        self.widget.hover = hover
        self.widget.label = label
        event = MagicMock()

        with (patch('wx.AutoBufferedPaintDC') as mock_dc_class,
              patch('wx.Brush') as mock_brush,
              patch('wx.Font')):
            mock_dc = mock_dc_class.return_value
            mock_dc.GetTextExtent.return_value = (14, 20)
            self.widget.on_paint(event)

        return mock_brush, mock_dc

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_hover_background(self):
        """
        Test that the on_paint method creates a background when the
        mouse is hovering.
        """
        mock_brush, mock_dc = self._setup_on_paint(True)
        mock_brush.assert_called_once_with(wx.Colour(220, 220, 220))
        mock_dc.DrawRectangle.assert_called_once_with(
            self.widget.GetClientRect())
        mock_dc.DrawText.assert_called_once()

    #@unittest.skip("Temporarily skipped")
    def test_on_paint_not_hover_background(self):
        """
        Test that the on_paint method creates a background when the
        mouse is not hovering.
        """
        mock_brush, mock_dc = self._setup_on_paint(False)
        mock_brush.assert_called_once_with(wx.Colour(222, 237, 230))

    #@unittest.skip("Temporarily skipped")
    def test_GetLabelText(self):
        """
        Test that the GetLabelText method returns the current label.
        """
        data = (
            ("→", "→"),
            ("←", "←")
            )
        msg = "Expected '{}', found '{}'."

        for set_value, expected in data:
            self.widget.label = set_value
            result = self.widget.GetLabelText()
            self.assertEqual(expected, result, msg.format(expected, result))
