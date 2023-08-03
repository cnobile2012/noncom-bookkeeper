# -*- coding: utf-8 -*-
#
# src/exceptions.py
#
__docformat__ = "restructuredtext en"


class NCBookkeeperException(Exception):
    """
    Base NC Bookkeeper Exception.
    """
    pass


class InvalidTomlException(NCBookkeeperException):
    """
    Exception raised with an invalid or unparseable TOML file.
    """
    _DEFAULT_MSG = "Unparseable TOML file."

    def __init__(self, message="", errors=None):
        if message != "":
            message = self._DEFAULT_MSG

        self.message = message
        self.errors = errors
        super().__init__(self.message)
