# -*- coding: utf-8 -*-
#
# test/test_bases.py
#
__docformat__ = "restructuredtext en"

import unittest
import wx

from . import log, get_path, check_flag, FakeWidget, FakeEvent

from src.bases import find_dict, BasePanel, BaseGenerated


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
        self.assertEquals(len(dict_), 2, msg)

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
        self.assertEquals(fs._bg_color, bg_color, msg)

    #@unittest.skip("Temporarily skipped")
    def test__setup_sizer_height_correctly(self):
        """
        Test that the sizer SetMinSize() is updated correctly.
        """
        class FakeParent:

            @property
            def statusbar_size(self):
                return 530, 15

        class FakePanel(BasePanel):

            def __init__(self, parent, size):
                self.parent = parent
                self.sizer = wx.GridBagSizer(vgap=2, hgap=2)
                self.sizer.SetMinSize(size)
                self._setup_sizer_height_correctly(self.sizer)

        orig_size = (500, 50)
        fp = FakePanel(FakeParent(), orig_size)
        size = fp.sizer.GetMinSize()
        should_be = (500, 65)
        msg = f"Should have size of '{should_be}' found '{size}'"
        self.assertEqual(should_be, size, msg)

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
        self.assertEquals(len(dict_), 2, msg)

    #@unittest.skip("Temporarily skipped")
    def test_locality_prefix_do_event(self):
        """
        Test that returns the 'do_event' callback and the callback updates
        a widget.
        """
        class FakeFrame(wx.Frame):

            def __init__(self, parent=None, id=wx.ID_ANY,
                         pos=wx.DefaultPosition,
                         style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
                         **kwargs):
                super().__init__(parent, id=id, pos=pos, style=style)

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
        callback = panel.locality_prefix('widget_00')
        should_be = 'do_event'
        msg = f"Should be a callback '{should_be}' found '{callback}'"
        self.assertIn(should_be, str(callback), msg)
        # Test the do_event() callback.
        fake_event = FakeEvent(event_object=FakeWidget(
            selection=kwargs['selection']))
        callback(fake_event)




