"""Turtle cup sprites, text pens and optional system sound feedback."""

import sys
import turtle
from game_config import COLORS

WHITE = COLORS["white"]


def make_writer(color=WHITE):
    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.penup()
    t.color(color)
    return t


def tone(kind, screen):
    if sys.platform == "win32":
        try:
            import winsound

            winsound.MessageBeep(
                winsound.MB_OK
                if kind in ("correct", "win")
                else winsound.MB_ICONEXCLAMATION
            )
            return
        except (ImportError, RuntimeError, OSError):
            pass

    try:
        screen.getcanvas().bell()
    except Exception:
        pass


class Cup:
    def __init__(self, cid, x, skin="normal"):
        self.cid = cid
        self.slot = cid
        self.x = x
        self.y = 0
        self.sprite = turtle.Turtle(visible=False)
        self.sprite.speed(0)
        self.sprite.penup()
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
        try:
            if self.sprite in self.sprite.screen._turtles:
                self.sprite.screen._turtles.remove(self.sprite)
        except Exception:
            pass
