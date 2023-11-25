# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

from .config import BaseSystemData


class Database(BaseSystemData):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def has_org_info(self):
        """
        Check that the db has the Organization Information.
        """
        ret = False
        # For now return false.
        return ret



# Store currency values as integers.
# Example $1952.14 in the db is 195214.
