# -*- coding: utf-8 -*-
#
# test/test_exceptions.py
#
__docformat__ = "restructuredtext en"

import unittest

from . import log, check_flag

from src.exceptions import InvalidTomlException


def raise_exception(msg='', errors=None):
    raise InvalidTomlException(message=msg, errors=errors)


class TestExceptions(unittest.TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        check_flag(self.__class__.__name__)

    def test_InvalidTomlException_default_message(self):
        """
        Test that the exception is raised and returns the default message.
        """
        with self.assertRaises(InvalidTomlException) as cm:
            raise_exception()

        should_be = InvalidTomlException._DEFAULT_MSG
        ex = str(cm.exception)
        msg = f"Should have message '{should_be}' found '{ex}'."
        self.assertEquals(should_be, ex, msg)
        msg = f"Should have error '{None}' found '{cm.exception.errors}'."
        self.assertIsNone(cm.exception.errors, msg)

    def test_InvalidTomlException_custom_message(self):
        """
        Test that the exception is raised and returns the custom message.
        """
        should_be_msg = "This is a custom message"
        should_be_err = 999

        with self.assertRaises(InvalidTomlException) as cm:
            raise_exception(should_be_msg, should_be_err)

        ex = str(cm.exception)
        errors = cm.exception.errors
        msg = f"Should have message '{should_be_msg}' found '{ex}'."
        self.assertEquals(should_be_msg, ex, msg)
        msg = f"Should have error '{should_be_err}' found '{errors}'."
        self.assertEqual(should_be_err, errors, msg)
