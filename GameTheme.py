"""Register the bundled pixel font for this process only."""

import ctypes as Ctypes
from pathlib import Path
import sys as Sys
import re as Re
from tkinter import font as Font

Assets = Path(__file__).resolve().parent / "assets"
FontFamily = "Pixelify Sans"


def LoadFont():
    """No system installation or administrator permissions are needed."""
    if Sys.platform == "win32":
        FilePath = Assets / "fonts" / "PixelifySans.ttf"
        if not Ctypes.windll.gdi32.AddFontResourceExW(str(FilePath), 0x10, 0):
            raise RuntimeError(f"Could not load the bundled font: {FilePath}")


def TextFont(Size, Bold=False):
    return (FontFamily, Size, "bold" if Bold else "normal")


def LabelRuns(Text, Size, Bold=False):
    """Keep pixel lettering, but use distinct, readable shapes for digits."""
    for Part in Re.split(r"(\d[\d,]*(?:\.\d+)?%?)", str(Text)):
        if Part:
            Style = (
                ("Consolas", Size, "bold")
                if Part[0].isdigit()
                else TextFont(Size, Bold)
            )
            yield Part, Style


def LabelWidth(Text, Size, Bold=False):
    return sum(
        Font.Font(font=Style).measure(Part)
        for Part, Style in LabelRuns(Text, Size, Bold)
    )
