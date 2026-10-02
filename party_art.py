"""Load PNG artwork and place it on the game canvas."""

from pathlib import Path
import tkinter
import turtle
from cup_collection import CUPS
from party_story import location

ASSET_FOLDER = Path(__file__).resolve().parent / "assets"
INK = "#1b1425"


def load_assets(screen):
    """Load once and retain image references for the lifetime of the game."""
    def load(relative_path):
        path = ASSET_FOLDER / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Required game image is missing: {path}")
        return tkinter.PhotoImage(data=path.read_bytes(), master=screen.getcanvas())

    skins = {}
    for skin, *_ in CUPS:
        base = load(f"cups/{skin}.png")
        skins[skin] = [base, base.zoom(2), base.zoom(3), base.zoom(5)]
        for suffix, image in zip(("preview", "cup", "hero"), skins[skin][1:]):
            screen.register_shape(skin + "_" + suffix, turtle.Shape("image", image))
    secret = load("cups/unknown.png").zoom(2)
    screen.register_shape("secret_preview", turtle.Shape("image", secret))
    spark = load("ui/spark.png")
    screen.register_shape("spark", turtle.Shape("image", spark))
    backgrounds = {
        name: load(f"backgrounds/{name}.png")
        for name in ("menu", "hall", "kitchen", "terrace", "dawn", "afterparty")
    }
    portraits = {
        name: load(f"characters/{name}.png").zoom(6)
        for name in ("mira", "theo", "jun")
    }
    return {
        "skins": skins,
        "secret": secret,
        "spark": spark,
        "backgrounds": backgrounds,
        "portraits": portraits,
        "title": load("ui/title.png"),
        "heart_full": load("ui/heart_full.png"),
        "heart_empty": load("ui/heart_empty.png"),
    }


def place_image(game, image, x, y):
    """x/y locate the top-left corner in Turtle coordinates."""
    game.session.screen.getcanvas().create_image(
        x, -y, image=image, anchor="nw", tags=(game.session.art_layer,)
    )


def scenery(game, menu=False):
    name = "menu" if menu else location(game.session.mode, game.session.level)
    game.session.scene_location = "hall" if menu else name
    right = -35 if menu else 470
    game.rectangle(-470, -174, right, 236, "#191522")
    place_image(game, game.session.assets["backgrounds"][name], -470, 236)
    if menu:
        # Text stays editable and crisp rather than being baked into the picture.
        pen = game.session.static
        game.write(pen, -170, 146, "LANTERN HOUSE", 13, "#e7c795")
        game.write(pen, -170, 123, "Est. after sundown", 10, "#b59aaf")
        game.write(pen, -252, -147, "Mira & Theo are saving you a seat.", 10, "#dfc3a8")


def draw_title(game, x, y):
    place_image(game, game.session.assets["title"], x, y)


def portrait(game, name, x, y):
    place_image(game, game.session.assets["portraits"][name.lower()], x, y + 138)


def frame(game, x1, y1, x2, y2, fill="#241d30", edge="#715166"):
    """Scalable UI borders remain code so buttons can fit their text."""
    r = game.rectangle
    r(x1 + 4, y1 - 4, x2 + 4, y2 - 4, INK)
    r(x1, y1, x2, y2, edge)
    r(x1 + 2, y1 + 2, x2 - 2, y2 - 2, fill)
    for x, y in (
        (x1 + 5, y1 + 5),
        (x2 - 8, y1 + 5),
        (x1 + 5, y2 - 8),
        (x2 - 8, y2 - 8),
    ):
        r(x, y, x + 3, y + 3, "#b08a72")
