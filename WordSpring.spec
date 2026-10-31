# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

datas = [
    ('THIRD_PARTY_NOTICES.md', '.'),
    ('store/Licenses/LGPL-3.0.txt', 'Licenses'),
]
binaries = []
hiddenimports = ['pyttsx3.drivers.sapi5', 'pythoncom', 'pywintypes', 'win32com.client']
tmp_ret = collect_all('pyttsx3')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=['PySide6.QtVirtualKeyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)

def exclude_qt_virtual_keyboard(entries):
    excluded_icu = {"icuuc.dll", "icuin.dll"}
    return [
        entry for entry in entries
        if "virtualkeyboard" not in entry[0].replace("\\", "/").casefold()
        and os.path.basename(entry[0]).casefold() not in excluded_icu
        and not os.path.basename(entry[0]).casefold().startswith("icudt")
    ]

a.binaries = exclude_qt_virtual_keyboard(a.binaries)
a.datas = exclude_qt_virtual_keyboard(a.datas)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WordSpring',
    icon=['store/Assets/WordSpring.ico'],
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
