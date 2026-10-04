#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# scripts/update_config.py
#

import os
import sys
import argparse
import traceback

import tomlkit as tk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.bases import find_dict
from src.utilities import make_name


class UpdateConfig:
    INLINE_TABLES = ("locale_prefix", "order")

    def __init__(self, options):
        self._options = options
        self._doc = None
        self._new_doc = {}
        self._last_fn = ()

    def start(self):
        self._load_toml()
        self._dispatch_tables()
        self._write_new_toml()

    def _load_toml(self):
        try:
            with open(self._options.infile, 'r') as f:
                raw_doc = f.read()
        except FileNotFoundError as e:
            print("The file {self._options.infile} was not found.")
            raise e
        else:
            self._doc = tk.parse(raw_doc)

    def _dispatch_tables(self):
        for name, table in self._doc.items():
            if name == 'meta':
                self._process_meta(name, table)
            else:
                self._process_panels(name, table)

    def _process_meta(self, name, table):
        self._new_doc[name] = table

    def _process_panels(self, name, table):
        sub_table = self._new_doc.setdefault(name, {})
        order = {}

        for subname, subtable in table.items():
            section = sub_table.setdefault(subname, {})

            for wname, widget in subtable.items():
                section[wname] = widget
                dict_ = find_dict(widget)
                pos = dict_.get('pos')

                if pos:
                    dict_['pos'] = [pos[1]]

                if widget[0] in ('StaticText', 'RadioBox', 'ComboBox'):
                    label = dict_['args'][2]
                    field_name = make_name(label)
                    self._last_fn = (widget[0], field_name)
                    order.setdefault(field_name, [wname])
                elif widget[0] == 'StaticLine':
                    field_name = wname
                    self._last_fn = ()
                    order.setdefault(field_name, [wname])
                elif widget[0] == 'ColorCheckBox':
                    label = dict_['args'][2]
                    field_name = make_name(label)
                    order.setdefault(field_name, [wname])
                    self._last_fn = ()
                elif widget[0] in ('TextCtrl', 'BadiDatePickerCtrl'):
                    if self._last_fn[0] in ('StaticText', 'RadioBox'):
                        order.setdefault(self._last_fn[1]).append(wname)

                    self._last_fn = ()

        if sub_table.get('meta'):
            sub_table['meta']['order'] = order

    def _write_new_toml(self):
        def add_table(parent, name, values):
            tbl = tk.table()
            parent.add(name, tbl)

            for key, value in values.items():
                if isinstance(value, dict):
                    if key in self.INLINE_TABLES:
                        itbl = tk.inline_table()

                        for k, v in value.items():
                            itbl[k] = v

                        tbl.add(key, itbl)
                    else:
                        add_table(tbl, key, value)
                else:
                    tbl.add(key, value)

        doc = tk.document()
        # Create header
        doc.add(tk.comment("-*- coding: utf-8 -*-"))
        doc.add(tk.comment(""))
        doc.add(tk.comment("config/default_bahai.toml"))
        doc.add(tk.comment(""))
        doc.add(tk.comment("This file provides data for the definition "
                           "of fields used on"))
        doc.add(tk.comment("the specified panels."))
        doc.add(tk.comment(""))
        doc.add(tk.comment("TOML field definitions: "
                           "https://toml.io/en/v1.0.0"))
        doc.add(tk.comment(""))
        doc.add(tk.comment("Noncommercial Bookkeeper META data"))
        doc.add(tk.comment("=================================="))
        doc.add(tk.comment(""))
        doc.add(tk.nl())

        for key, value in self._new_doc.items():
            if isinstance(value, dict):
                add_table(doc, key, value)
            else:
                doc.add(key, value)

        self._write_file(tk.dumps(doc))
        #print(self._new_doc)

    def _write_file(self, data) -> None:
        try:
            with open(self._options.outfile, 'w') as f:
                f.write(data)
        except (OSError, PermissionError) as e:
            msg = (f"Could not create the {self._options.outfile} "
                   f"file, {str(e)}")
            print(msg)
            raise e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Update config files to new format."))
    parser.add_argument(
        '-i', '--infile', type=str, default=None, dest='infile',
        help="The full path to the incoming TOML config file.")
    parser.add_argument(
        '-o', '--outfile', type=str, default=None, dest='outfile',
        help="The full path to the outgoing TOML config file.")
    options = parser.parse_args()
    uc = UpdateConfig(options)
    ret = 0

    if options.infile and options.outfile:
        try:
            uc.start()
        except Exception:
            ret = 1
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
            print(f"{sys.exc_info()[0]}: {sys.exc_info()[1]}\n",
                  file=sys.stderr)
    else:
        print("You must supply the full path and filename for both "
              "the incoming and outgoing files.")

    sys.exit(ret)
