#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Build the package environment.
#
__docformat__ = "restructuredtext en"

import os
import re
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.config import Settings
from src.bases import version


DESKTOP = """[Desktop Entry]
Version={}
Terminal=False
Type=Application
Name={}
Comment=A bookkeeping application for non-commercial organizations.
Path={}
Exec={}
Icon={}
"""


class CreatePackage:
    _PACKAGE_DIR = 'package'
    _OPT_DIR = 'opt'
    _USR_DIR = 'usr'
    _SHARE_DIR = 'share'
    _APP_DIR = 'applications'
    _ICONS_DIR = 'icons'
    _HICOLOR_DIR = 'hicolor'
    _HIC_SUB_DIRS = ('16x16', '24x24', '32x32', '48x48', '64x64', '72x72')
    _RE_IMG = re.compile(r"^bookkeeper-(?P<rez>\d+x\d+)\.png$")
    _CONFIG_TYPES = {'bahai': 'bahai-bookkeeper', 'generic': 'nc-bookkeeper'}
    _APP_NAMES = {'bahai': "Bahá'í Bookkeeper", 'generic': "NonCom Bookkeeper"}

    def __init__(self, base_path=None):
        if base_path:
            self._base_path = base_path
        else:
            self._base_path = Settings.base_dir()

    def start(self):
        path = os.path.join(self._base_path, 'dist')
        assert os.path.exists(path), (f"The '{path}' path does not exist. "
                                      "Run 'make build-spec'.")
        icon_dirs = self.create_package_dirs()
        self.copy_images(icon_dirs)
        self.copy_app()
        self.copy_desktop_file()
        self.change_modes()

    def create_package_dirs(self):
        path = os.path.join(self._base_path, self._PACKAGE_DIR)
        if os.path.exists(path): shutil.rmtree(path)
        os. makedirs(os.path.join(path, self._OPT_DIR), mode=0o775)
        os. makedirs(os.path.join(path, self._USR_DIR, self._SHARE_DIR,
                                  self._APP_DIR), mode=0o775)
        icon_dirs = os.path.join(path, self._USR_DIR, self._SHARE_DIR,
                                 self._ICONS_DIR, self._HICOLOR_DIR)

        for dir_ in self._HIC_SUB_DIRS:
            new_dir = os.path.join(icon_dirs, dir_)
            os. makedirs(new_dir, mode=0o775)

        return icon_dirs

    def copy_images(self, icon_dirs):
        for dir_, fname in self._icon_file_names.items():
            head, tail = os.path.split(fname)
            new_name = tail.replace(f'-{dir_}', '')
            icon_file = os.path.join(icon_dirs, dir_, new_name)
            shutil.copy2(fname, icon_file)

    def copy_app(self):
        path = os.path.join(self._base_path, self._PACKAGE_DIR, self._OPT_DIR)
        shutil.copytree(self._dist_path, path, dirs_exist_ok=True)

    def copy_desktop_file(self):
        path = os.path.join(self._base_path, self._PACKAGE_DIR, self._USR_DIR,
                            self._SHARE_DIR, self._APP_DIR,
                            'nc-bookkeeper.desktop')

        with open(path, 'w') as f:
            f.write(self._desktop_data)

    def change_modes(self):
        path = os.path.join(self._base_path, self._PACKAGE_DIR)

        for root, dirs, files in os.walk(path):
            for name in files:
                path = os.path.join(root, name)

                if name == self._CONFIG_TYPES[self._dist_type]:
                    os.chmod(path, 0o755)
                else:
                    os.chmod(path, 0o644)

            for dir_ in dirs:
                path = os.path.join(root, dir_)
                os.chmod(path, 0o755)

    @property
    def _icon_file_names(self):
        path = os.path.join(self._dist_path, '_internal', 'images')
        names = [f for f in os.listdir(path) if f.endswith('.png')]
        result = {}

        for name in names:
            sre = self._RE_IMG.search(name)
            assert sre, f"The image path in '{name}' was not found"
            result[sre.group('rez')] = os.path.join(path, name)

        return result

    @property
    def _dist_type(self):
        return os.environ.get('NCB_TYPE', 'bahai')

    @property
    def _dist_path(self):
        return os.path.join(self._base_path, 'dist',
                            self._CONFIG_TYPES[self._dist_type])

    @property
    def _desktop_data(self):
        ver = version()
        name = self._APP_NAMES[self._dist_type]
        path = os.path.join('/', self._OPT_DIR)
        exec_ = os.path.join(path, self._CONFIG_TYPES[self._dist_type])
        icon = 'bookkeeper.png'
        return DESKTOP.format(ver, name, path, exec_, icon)


if __name__ == "__main__":
    CreatePackage().start()
