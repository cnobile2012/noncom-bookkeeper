#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# tests/create_test_data.py
#
__docformat__ = "restructuredtext en"

import os
import sys
import asyncio
import pprint

PWD = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PWD)
sys.path.append(BASE_DIR)

from src.bahai_database import Database


class CreateTestData:

    def __init__(self, options, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = options
        self.db = Database()
        self.db.debug = True
        self.db.create_dirs()

    def start(self):
        asyncio.run(self._create())

    async def _create(self):
        query = "SELECT * from {};"
        data = {}

        for table in self.db._SCHEMA_TABLES.keys():
            values = await self.db._do_select_query(query.format(table))
            data.setdefault(table, values)

        self._pretty_print(data)

    def _pretty_print(self, data):
        pp = pprint.pformat(data, indent=1, compact=True, sort_dicts=True)
        print(pp)



if __name__ == '__main__':
    import argparse
    import traceback

    parser = argparse.ArgumentParser(description="Create test data.")
    parser.add_argument('-o', '--output', type=str, dest='output',
                        help=("The output file path and name. "
                              "(tests/test_data.py)"))
    parser.add_argument('-D', '--debug', action='store_true', default=False,
                        dest='debug', help="Run in debug mode.")
    options = parser.parse_args()
    ret = 0

    if options.debug:
        print("Options: {}".format(options))

    if not options.output:
        parser.print_help()
        ret = 1
    else:
        try:
            ctd = CreateTestData(options)
            ctd.start()
        except Exception as e:
            ret = 1
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
            print("{}: {}".format(sys.exc_info()[0], sys.exc_info()[1]))

    sys.exit(ret)
