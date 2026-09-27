# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for "The Electronist's Guide".
#
# Build with:   pyinstaller electronist_guide.spec
# (run this ON the OS you want to build for - see BUILD.md)

import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_file = None
if sys.platform.startswith("win"):
    icon_file = "assets/icon.ico"
elif sys.platform == "darwin":
    icon_file = "assets/icon.icns"

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ElectronistGuide',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no terminal window behind the GUI
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ElectronistGuide',
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name='ElectronistGuide.app',
        icon='assets/icon.icns',
        bundle_identifier='guide.electronist.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '5.1',
        },
    )
