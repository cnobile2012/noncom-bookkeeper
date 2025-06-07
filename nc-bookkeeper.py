#!/usr/bin/env python
#
# nc-bookkeeper.py
#

import os
import sys
import argparse

from src import Logger
from src.config import Settings, TomlPanelConfig, TomlAppConfig
from src.main_frame import MainFrame

import wx


class CheckAppConfig(TomlAppConfig):
    """
    Check that the app config file has valid data. Create a new one
    if necessary.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def has_valid_data(self):
        """
        Does the static app config exist and is the data valid?
        """
        return self.is_valid


if __name__ == "__main__":
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
    options = parser.parse_args()
    settings = Settings()
    status = 0

    if not options.debug and options.file_dump:  # -F (Must be used with -D)
        options.file_dump = False
        print("If using -F or --file-dump, -D or --debug must also be used.",
              file=sys.stderr)

    if options.debug:
        print(f"DEBUG--options: {options}", file=sys.stderr)
        settings.debug = True

    if options.run:
        settings.create_dirs()
        Logger().config(logger_name=settings.logger_name,
                        file_path=settings.user_log_fullpath)
        tpc = TomlPanelConfig()
        tac = TomlAppConfig()

        if not tpc.is_valid:
            print(tpc.get_err_msg, file=sys.stderr)
            print(f"See {tpc.user_log_fullpath}, for more information.",
                  file=sys.stderr)
            status = 1
        elif not tac.is_valid:
            print(tac.get_err_msg, file=sys.stderr)
            print(f"See {tac.user_log_fullpath}, for more information.",
                  file=sys.stderr)
            status = 2
        else:
            # Try to run application.
            app = wx.App()
            mf = MainFrame(options=options)
            icon_path = os.path.join(settings.base_dir(), 'images',
                                     'bookkeeper-48x48.ico')
            mf.SetIcon(wx.Icon(icon_path))
            mf.Show(True)
            app.MainLoop()
    else:
        parser.print_help()

    sys.exit(status)
