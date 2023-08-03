#!/usr/bin/env python

from pprint import pprint

from src.config import TomlConfig
from src.ncb import CheckAppData
from src.frame_factory import FrameFactory, BaseFrame

import wx


if __name__ == "__main__":
    import sys

    cad = CheckAppData()
    sf = FrameFactory()
    tc = TomlConfig()
    frames = {}
    status = 0

    if not cad.has_valid_data:
        status = 1
        print(f"Invalid data, see log file, exit status {status}")
    else:
        print("TOML doc:")
        klass, names = sf.parse()
        print(klass)  # *** TODO *** Remove later
        pprint(names) # *** TODO *** Remove later
        # Try to run display.
        app = wx.App()

        for key in sf.class_name_keys:
            klass_name = sf.get_class_name(key)
            exec(klass)
            frames[key] =  eval(klass_name)()

        frames['config'].Show()
        app.MainLoop()

    sys.exit(status)
