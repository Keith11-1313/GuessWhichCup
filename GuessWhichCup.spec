# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

Version = Path("Version").read_text(encoding="utf-8").strip()


AnalysisResult = Analysis(
    ["WhatTheCup.py"],
    pathex=[],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
Pyz = PYZ(AnalysisResult.pure)

Executable = EXE(
    Pyz,
    AnalysisResult.scripts,
    AnalysisResult.binaries,
    AnalysisResult.datas,
    [],
    name="GuessWhichCup-v" + Version,
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
    icon=["assets/ui/AppIcon.ico"],
)
