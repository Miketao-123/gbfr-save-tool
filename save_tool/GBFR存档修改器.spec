# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gbfr_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('catalog.json', '.'), ('catalog_chars.json', '.'), ('catalog_gem.json', '.'), ('catalog_sigils_full.json', '.'), ('catalog_summon.json', '.'), ('chara_names.json', '.'), ('gem_legality.json', '.'), ('gem_mix_pool.json', '.'), ('gbfr-save-editor/GBFR-Save-Editor-main/gbfr_editor/core', 'gbfr-save-editor/GBFR-Save-Editor-main/gbfr_editor/core')],
    hiddenimports=['gbfr_cheat_tool', 'gbfr_save', 'hashing', 'gui_theme'],
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
    name='GBFR存档修改器',
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
