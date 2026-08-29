#!/usr/bin/env python
#
# nc-bookkeeper.py
#

import os
import sys
import argparse
import wx

from src import Logger
from src.config import Settings, TomlPanelConfig, TomlAppConfig
from src.main_frame import MainFrame

import ctypes
import ctypes.util


# Module-level reference — must stay alive for the life of the process,
# otherwise the ctypes-wrapped callback gets garbage collected and GLib
# ends up calling into freed memory.
_glib_log_handler_ref = None


def suppress_gtk_style_context_warnings():
    """
    Install a GLib log handler that swallows the GTK-CRITICAL style-context
    assertion spam from wxWidgets 3.3.x's GTK3 theming code.

    Non-fatal, cosmetic bug in wxWidgets 3.3.x (gtk_style_context_add_provider
    called on an invalid/torn-down context). Safe to filter until upstream
    fixes it in a later 3.3.x point release.
    """
    global _glib_log_handler_ref
    glib_path = ctypes.util.find_library("glib-2.0")

    if not glib_path:
        return  # nothing to do on platforms without GLib (e.g. Windows/macOS)

    glib = ctypes.CDLL(glib_path)

    # GLogFunc signature: void (*)(const gchar *log_domain,
    #                              GLogLevelFlags log_level,
    #                              const gchar *message,
    #                              gpointer user_data)
    GLOG_FUNC = ctypes.CFUNCTYPE(
        None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)

    G_LOG_LEVEL_CRITICAL = 1 << 3  # from glib's gmessages.h

    def _null_log_handler(log_domain, log_level, message, user_data):
        # Swallow it. Return nothing (void) — this replaces the default
        # handler, so nothing gets printed to stderr for this domain/level.
        pass

    _glib_log_handler_ref = GLOG_FUNC(_null_log_handler)

    glib.g_log_set_handler(b"Gtk", G_LOG_LEVEL_CRITICAL,
                           _glib_log_handler_ref, None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Non-commercial organization bookkeeping application."))
    parser.add_argument(
        '-r', '--run', action='store_false', dest='run',
        help="Normal running mode.")
    parser.add_argument(
        '-D', '--debug', action='store_true', default=False, dest='debug',
        help="Debugging mode also moves the location of all start up files.")
    parser.add_argument(
        '-F', '--file-dump', action='store_true', default=False,
        dest='file_dump', help=("Dump the generated panel factory files."))
    options = parser.parse_args()
    settings = Settings()
    status = 0

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
            print(tpc.err_msg, file=sys.stderr)
            print(f"See {tpc.user_log_fullpath}, for more information.",
                  file=sys.stderr)
            status = 1
        elif not tac.is_valid:
            print(tac.err_msg, file=sys.stderr)
            print(f"See {tac.user_log_fullpath}, for more information.",
                  file=sys.stderr)
            status = 2
        else:
            suppress_gtk_style_context_warnings()
            # Run the application.
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
