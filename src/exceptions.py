# -*- coding: utf-8 -*-
#
# src/exceptions.py
#
__docformat__ = "restructuredtext en"


class NCBookkeeperException(Exception):
    """
    Base NC Bookkeeper Exception.
    """
    def __init__(self, message):
        super().__init__(message)


class InvalidTomlException(NCBookkeeperException):
    """
    Exception raised with an invalid or unparseable TOML file.
    """
    _DEFAULT_MSG = "Unparseable TOML file."

    def __init__(self, message="", errors=None):
        if message == "":
            message = self._DEFAULT_MSG

        self._message = message
        self._errors = errors
        super().__init__(self._message)

    @property
    def errors(self):
        return self._errors
