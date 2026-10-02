"""Turtle cup sprites, text pens and custom WAV sound feedback."""

import sys
from pathlib import Path
import tkinter
import turtle
from game_config import COLORS

WHITE = COLORS["white"]


def input_canvas(screen):
    """Locate Turtle's input canvas through public Tk widget traversal."""
    pending = [screen.getcanvas().winfo_toplevel()]
    while pending:
        widget = pending.pop()
        if isinstance(widget, tkinter.Canvas):
            return widget
        pending.extend(widget.winfo_children())
    raise RuntimeError("Turtle's input canvas was not found")


def make_writer(color=WHITE):
    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.penup()
    t.color(color)
    return t


def tone(kind):
    """Play quiet custom WAV feedback without triggering system notifications."""
    if sys.platform == "win32":
        try:
            import winsound

            path = Path(__file__).resolve().parent / "assets" / "sounds" / f"{kind}.wav"
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
            return
        except (ImportError, RuntimeError, OSError):
            pass



class Cup:
    def __init__(self, cid, x, skin="normal"):
        self.sprite = turtle.Turtle(visible=False)
        self.sprite.speed(0)
        self.sprite.penup()
        self.reset(cid, x, skin)

    def reset(self, cid, x, skin):
        """Reuse this sprite for a new round without allocating another Turtle."""
        self.cid = cid
        self.slot = cid
        self.x = x
        self.y = 0
        shape_name = skin + "_cup"
        self.sprite.shape(shape_name)
        self.sprite.setheading(90)
        self.sprite.goto(x, 0)
        self.sprite.showturtle()

    def contains(self, x, y):
        """Both the sprite and its number chip are valid click targets."""
        distance = abs(x - self.x)
        inside_sprite = distance <= 48 and -51 <= y <= 51
        inside_number = distance <= 15 and -124 <= y <= -96
        return inside_sprite or inside_number

    def render(self):
        self.sprite.goto(self.x, self.y)

    def hide(self):
        self.sprite.hideturtle()
        self.sprite.clear()
