"""Turtle cup sprites, text pens and custom WAV sound feedback."""

import sys as Sys
from pathlib import Path
from NamingCompatibility import PascalName
import tkinter as Tkinter
import turtle as Turtle
from GameConfig import Colors

White = Colors["white"]


def InputCanvas(Screen):
    """Locate Turtle's input canvas through public Tk widget traversal."""
    Pending = [Screen.getcanvas().winfo_toplevel()]
    while Pending:
        Widget = Pending.pop()
        if isinstance(Widget, Tkinter.Canvas):
            return Widget
        Pending.extend(Widget.winfo_children())
    raise RuntimeError("Turtle's input canvas was not found")


def MakeWriter(Color=White):
    T = Turtle.Turtle(visible=False)
    T.speed(0)
    T.penup()
    T.color(Color)
    return T


def Tone(Kind):
    """Play quiet custom WAV feedback without triggering system notifications."""
    if Sys.platform == "win32":
        try:
            import winsound as Winsound

            FilePath = (
                Path(__file__).resolve().parent
                / "assets"
                / "sounds"
                / f"{PascalName(Kind)}.wav"
            )
            Winsound.PlaySound(
                str(FilePath),
                Winsound.SND_FILENAME | Winsound.SND_ASYNC | Winsound.SND_NODEFAULT,
            )
            return
        except (ImportError, RuntimeError, OSError):
            pass


class Cup:
    def __init__(Self, Cid, X, Skin="normal"):
        Self.Sprite = Turtle.Turtle(visible=False)
        Self.Sprite.speed(0)
        Self.Sprite.penup()
        Self.Reset(Cid, X, Skin)

    def Reset(Self, Cid, X, Skin):
        """Reuse this sprite for a new round without allocating another Turtle."""
        Self.Cid = Cid
        Self.Slot = Cid
        Self.X = X
        Self.Y = 0
        ShapeName = Skin + "_cup"
        Self.Sprite.shape(ShapeName)
        Self.Sprite.setheading(90)
        Self.Sprite.goto(X, 0)
        Self.Sprite.showturtle()

    def Contains(Self, X, Y):
        """Both the sprite and its number chip are valid click targets."""
        Distance = abs(X - Self.X)
        InsideSprite = Distance <= 48 and -51 <= Y <= 51
        InsideNumber = Distance <= 15 and -124 <= Y <= -96
        return InsideSprite or InsideNumber

    def Render(Self):
        Self.Sprite.goto(Self.X, Self.Y)

    def Hide(Self):
        Self.Sprite.hideturtle()
        Self.Sprite.clear()
