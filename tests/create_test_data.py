#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# tests/create_test_data.py
#
__docformat__ = "restructuredtext en"

import os
import re
import sys
import asyncio
import pprint

from io import StringIO

PWD = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PWD)
sys.path.append(BASE_DIR)

from src.bahai_database import Database
from src.prep_and_cache import Cache


class CreateTestData:

    def __init__(self, options, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = options
        self.db = Database()
        self.db.debug = True
        self.db.create_dirs()
        self._cache = Cache(self.db)

    def start(self):
        asyncio.run(self._create())

    async def _create(self):
        await self._cache.load()
        buff = StringIO()
        filename = self.options.output
        buff.write("# -*- coding: utf-8 -*-\n")
        buff.write(f"#\n# {filename}\n#\n")
        buff.write('__docformat__ = "restructuredtext en"\n\n')
        buff.write("import badidatetime\n\n\n")
        prefix = "ORG_FIELDS = "
        org_data = self._format_data(self._cache.ORG_FIELDS, prefix, width=70)
        buff.write(f"{org_data}\n")
        prefix = "BDG_FIELDS = "
        bdg_data = self._format_data(self._cache.get_bgt_fields, prefix,
                                     width=67)
        buff.write(f"{bdg_data}\n")
        buff.write(f"{await self._format_table_data()}")

        with open(filename, 'w') as f:
            f.write(buff.getvalue())
            buff.close()

    async def _format_table_data(self):
        def _fix_value(value):
            r = list(record)
            r[1] = value
            return tuple(r)

        query = "SELECT * from {};"
        data = {}

        for table in self.db._SCHEMA_TABLES.keys():
            values = await self.db._do_select_query(query.format(table))
            data.setdefault(table, values)

        # Take out personal info.
        config_data = data.get(self.db._T_DATA)

        if config_data:
            new_cd = []

            for idx, record in enumerate(config_data):
                value = record[1]

                if '/' in value:
                    record = _fix_value('America/New_York')
                elif re.match(r'^-?\d+(?:\.\d+)$', value) is not None:
                    v = float(value)

                    if v > 0:
                        record = _fix_value('40.7127281')
                    else:
                        record = _fix_value('-74.0060152')
                elif 'County' in value:
                    record = _fix_value('New York')
                elif 'Var' in value:
                    record = _fix_value('New York')
                elif 'J.' in value:
                    record = _fix_value('Joe Schmo')

                new_cd.append(record)

            data[self.db._T_DATA] = new_cd

        prefix = "TEST_DATA = "
        return self._format_data(data, prefix, width=70)

    def _format_data(self, data: dict, prefix: str, indent: int=1,
                     width: int=80):
        formatted = pprint.pformat(data, indent=indent, width=width,
                                   compact=True, sort_dicts=True)
        split_fmt = formatted.split('\n')
        indent = ' ' * len(prefix)
        new_format = ''

        for i, line in enumerate(split_fmt):
            if i == 0:
                new_format += prefix + line + '\n'
            else:
                new_format += indent + line + '\n'

        return new_format


if __name__ == '__main__':
    import argparse
    import traceback

    parser = argparse.ArgumentParser(description="Create test data.")
    parser.add_argument('-o', '--output', type=str, dest='output',
                        help=("The output file path and name. "
                              "(tests/sample_data.py)"))
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
        except Exception:
            ret = 1
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
            print("{}: {}".format(sys.exc_info()[0], sys.exc_info()[1]))

    sys.exit(ret)
