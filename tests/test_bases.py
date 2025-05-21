# -*- coding: utf-8 -*-
#
# test/test_bases.py
#
__docformat__ = "restructuredtext en"

import os
import re
import unittest
import wx

from . import check_flag, FakeFrame, FakeWidget, FakeEvent

from src.bases import find_dict, version, BasePanel, BaseGenerated


class TestBases(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)

    def tearDown(self):
        if hasattr(self, 'widget_00'):
            setattr(self, 'widget_00', None)

    #@unittest.skip("Temporarily skipped")
    def test_find_dict_found(self):
        """
        Test that a dict that is arbitrarily placed in a list can be found.
        """
        list_ = ['stuff', 'more_stuff', {'a': 'A', 'b': 'B'}, 'yet_more_stuff']
        dict_ = find_dict(list_)
        msg = f"Should find a 'dict' found {type(dict_)}"
        self.assertTrue(isinstance(dict_, dict), msg)
        msg = f"Should find a 'dict' of non zero length found {dict_}"
        self.assertEqual(len(dict_), 2, msg)

    #@unittest.skip("Temporarily skipped")
    def test_find_dict_not_found(self):
        """
        Test that a dict that is arbitrarily placed in a list can not be found.
        """
        list_ = ['stuff', 'mors_stuff', 'yet_more_stuff']
        dict_ = find_dict(list_)
        msg = f"Should find a 'dict' found {type(dict_)}"
        self.assertTrue(isinstance(dict_, dict), msg)
        msg = f"Should find a 'dict' of zero length found {dict_}"
        self.assertFalse(dict_, msg)

    #@unittest.skip("Temporarily skipped")
    def test_version(self):
        """
        Test that the application version is returned properly.
        """
        os.environ['PR_TAG'] = 'rc1'
        ver = version()
        sre = re.search(r"(\d*)\.(\d*)\.(\d*)(\w{2}\d*)", ver)
        ver_list = sre.groups()
        msg = "Should be an integer found {}."

        for idx, v in enumerate([int(v) for v in ver_list[:-1]], start=1):
            self.assertTrue(isinstance(v, int), msg.format(v))

        msg = f"Should have three integer parts to version found {idx}"
        self.assertEqual(3, idx, msg)
        msg = f"Should find pre-release (rc#) found {ver_list[-1]}"
        self.assertEqual(os.environ['PR_TAG'], ver_list[-1], msg)

    #@unittest.skip("Temporarily skipped")
    def test_background_color(self):
        """
        Test that the background color can be returned from the subclass.
        """
        class FakeSubclass(BasePanel):

            def __init__(self):
                self._bg_color = (232, 213, 149)

        fs = FakeSubclass()
        bg_color = fs.background_color
        msg = f"Should return RGB color '{fs._bg_color}' found '{bg_color}'."
        self.assertEqual(fs._bg_color, bg_color, msg)

    #@unittest.skip("Temporarily skipped")
    def test__find_dict_found(self):
        """
        This is a test of the same function above. It is a redirect
        in the BasePanel class. We do not repeat the whole test.
        """
        bp = BasePanel()
        list_ = ['stuff', 'more_stuff', {'a': 'A', 'b': 'B'}, 'yet_more_stuff']
        dict_ = bp._find_dict(list_)
        msg = f"Should find a 'dict' found {type(dict_)}"
        self.assertTrue(isinstance(dict_, dict), msg)
        msg = f"Should find a 'dict' of non zero length found {dict_}"
        self.assertEqual(len(dict_), 2, msg)

    #@unittest.skip("Temporarily skipped")
    def test_locality_prefix_do_event(self):
        """
        Test that returns the 'do_event' callback and the callback updates
        a widget.
        """
        class FakePanel(BaseGenerated):

            def __init__(self, parent, **kwargs):
                selection = kwargs.pop('selection', '')
                super().__init__(parent)
                text = kwargs.get('text', '')
                self.locale_prefix = {selection: text}
                self.widget_00 = FakeWidget()

        app = wx.App()
        kwargs = {'selection': 'my_selecttion', 'text': "String of text."}
        frame = FakeFrame()
        panel = FakePanel(frame, **kwargs)
        # Test the locality_prefix() method.
        dirty_flag = True
        callback = panel.locality_prefix('widget_00', dirty_flag)
        should_be = 'do_event'
        msg = f"Should be a callback '{should_be}' found '{callback}'"
        self.assertIn(should_be, str(callback), msg)
        # Test the do_event() callback.
        fake_event = FakeEvent(event_object=FakeWidget(
            selection=kwargs['selection']))
        callback(fake_event)
        # Test dirty_flag
        msg = f"Should have dirty_flag set to {dirty_flag} found {panel.dirty}"
        self.assertTrue(panel.dirty, msg)

    #@unittest.skip("Temporarily skipped")
    def test_set_dirty_flag(self):
        """
        Test that the dirty_flag gets set in the event callback.
        """
        class FakePanel01(BaseGenerated):

            def __init__(self, parent, *args, **kwargs):
                super().__init__(parent, *args, **kwargs)
                self.widget_00 = wx.TextCtrl(self, wx.ID_ANY, '')
                self.widget_00.Bind(wx.EVT_TEXT, self.set_dirty_flag)

        class FakePanel02(FakePanel01):

            def __init__(self, parent, *args, **kwargs):
                super().__init__(parent, *args, **kwargs)

            #def set_dirty(self, value):  # This is just for testing.
            #    self.dirty = value

            def get_selection(self, event):
                pass

        app = wx.App()
        frame = FakeFrame()
        data = (
            # panel,             value,       init,  sel,   expect
            (FakePanel01(frame), "",          False, False, True),
            (FakePanel01(frame), "",          True,  False, False),
            (FakePanel01(frame), "Something", False, False, True),
            (FakePanel01(frame), "Something", True,  False, False),
            (FakePanel02(frame), "",          False, True,  True),
            (FakePanel02(frame), "",          True,  True,  False),
            (FakePanel02(frame), '182',       False, True,  True),
            (FakePanel02(frame), '182',       True,  True,  False),
            )

        msg = ("The dirty_flag should be {} with initializing {}, selected {} "
               "and value '{}', found {}.")

        for panel, value, initializing, selected, expected_result in data:
            panel.initializing = initializing
            panel.selected = selected
            panel.widget_00.SetValue(value)
            result = panel.dirty
            self.assertEqual(expected_result, result, msg.format(
                expected_result, initializing, selected, value, result))
