# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['nc-bookkeeper.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config'), ('images', 'images')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='bahai-bookkeeper',
    icon='images/logo-48x48.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bahai-bookkeeper',
)
# For the macOS
app = BUNDLE(
    coll,
    name='Bahai Bookkeeper.app',
    icon='images/logo-48x48.ico',
    bundle_identifier=None)
