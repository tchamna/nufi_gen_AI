# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_nufi_windows_keyboard_customizable.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\android-keyboard\\app\\src\\main\\assets\\clafrica.json', 'android-keyboard\\app\\src\\main\\assets'), ('..\\android-keyboard\\app\\src\\main\\assets\\nufi_sms.json', 'android-keyboard\\app\\src\\main\\assets'), ('..\\android-keyboard\\app\\src\\main\\assets\\nufi_calendar.json', 'android-keyboard\\app\\src\\main\\assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Clafrica Plus Customizable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    uac_admin=False,
    uac_uiaccess=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
