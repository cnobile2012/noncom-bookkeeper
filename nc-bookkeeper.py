#!/usr/bin/env python
#
# nc-bookkeeper.py
#

import os
import sys
import argparse

from src.main_frame import MainFrame
from src.ncb import CheckPanelConfig, CheckAppConfig
from src.config import Settings

import wx


def _parse_arguments():
    parser = argparse.ArgumentParser(
        description=("Non-commercial organization bookkeeping application."))
    parser.add_argument(
        '-r', '--run', action='store_true', default=True, dest='run',
        help="Normal running mode.")
    parser.add_argument(
        '-D', '--debug', action='store_true', default=False, dest='debug',
        help="Debugging mode.")
    parser.add_argument(
        '-F', '--file-dump', action='store_true', default=False,
        dest='file_dump', help=("Dump the generated panel factory files "
                                "(must be used with -D or --debug)."))
    return parser


if __name__ == "__main__":
    cpc = CheckPanelConfig()
    cac = CheckAppConfig()
    status = 0

    if not cpc.has_valid_data:
        status = 1
        print(f"Invalid data, see log file, exit status {status}")

    if status == 0 and cac.has_valid_data:
        # Try to run display.
        parser = _parse_arguments()
        options = parser.parse_args()

        if options.file_dump:  # -F (Must be used with -D)
            if not options.debug:
                options.file_dump = False
                print("Option -F must be used with -D.", file=sys.stderr)

        if options.debug:
            print(f"DEBUG--options: {options}", file=sys.stderr)

        if options.run:
            app = wx.App()
            mf = MainFrame(options=options)
            icon_path = os.path.join(Settings.base_dir(), 'images',
                                     'bookkeeper-48x48.ico')
            mf.SetIcon(wx.Icon(icon_path))
            mf.Show(True)
            app.MainLoop()
        else:
            parser.print_help()
    else:
        status = 2
        print(f"Programming error, see log file, exit status {status}")

    sys.exit(status)
