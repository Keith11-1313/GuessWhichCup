"""Register the bundled pixel font for this process only."""

import ctypes
from pathlib import Path
import sys
import re
from tkinter import font

ASSETS = Path(__file__).resolve().parent / "assets"
FONT_FAMILY = "Pixelify Sans"


def load_font():
    """No system installation or administrator permissions are needed."""
    if sys.platform == "win32":
        path = ASSETS / "fonts" / "PixelifySans.ttf"
        if not ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0):
            raise RuntimeError(f"Could not load the bundled font: {path}")


def text_font(size, bold=False):
    return (FONT_FAMILY, size, "bold" if bold else "normal")


def label_runs(text, size, bold=False):
    """Keep pixel lettering, but use distinct, readable shapes for digits."""
    for part in re.split(r"(\d[\d,]*(?:\.\d+)?%?)", str(text)):
        if part:
            style = ("Consolas", size, "bold") if part[0].isdigit() else text_font(size, bold)
            yield part, style


def label_width(text, size, bold=False):
    return sum(font.Font(font=style).measure(part) for part, style in label_runs(text, size, bold))
