"""Load PNG artwork and place it on the game canvas."""

from pathlib import Path
from NamingCompatibility import AssetPath
import tkinter as Tkinter
import turtle as Turtle
from CupCatalog import AllCups
from PartyStory import Location

AssetFolder = Path(__file__).resolve().parent / "assets"
Ink = "#1b1425"


def LoadAssets(Screen):
    """Load once and retain image references for the lifetime of the game."""

    def Load(RelativePath):
        FilePath = AssetFolder / AssetPath(RelativePath)
        if not FilePath.is_file():
            raise FileNotFoundError(f"Required game image is missing: {FilePath}")
        return Tkinter.PhotoImage(data=FilePath.read_bytes(), master=Screen.getcanvas())

    Skins = {}
    SkinFrames = {}
    for Skin, *Ignored in AllCups:
        Base = Load(f"cups/{Skin}.png")
        Skins[Skin] = [Base, Base.zoom(2), Base.zoom(3), Base.zoom(5)]
        SkinFrames[Skin] = [Skins[Skin]]
        for Index in (1, 2, 3):
            Image = Load(f"cups/{Skin}_{Index}.png")
            SkinFrames[Skin].append(
                [Image, Image.zoom(2), Image.zoom(3), Image.zoom(5)]
            )
        for Suffix, Image in zip(("preview", "cup", "hero"), Skins[Skin][1:]):
            Screen.register_shape(Skin + "_" + Suffix, Turtle.Shape("image", Image))
    Secret = Load("cups/unknown.png").zoom(2)
    Screen.register_shape("secret_preview", Turtle.Shape("image", Secret))
    Coin = Load("ui/coin.png")
    Screen.register_shape("coin", Turtle.Shape("image", Coin))
    Backgrounds = {
        Name: Load(f"backgrounds/{Name}.png")
        for Name in ("menu", "hall", "kitchen", "terrace", "dawn", "afterparty")
    }
    return {
        "skins": Skins,
        "skin_frames": SkinFrames,
        "secret": Secret,
        "coin": Coin,
        "backgrounds": Backgrounds,
        "title": Load("ui/title.png"),
        "heart_full": Load("ui/heart_full.png"),
        "heart_empty": Load("ui/heart_empty.png"),
        "coin_hint": Load("ui/coin_hint.png"),
        "app_icon": Load("ui/app_icon.png"),
        "party_over": Load("backgrounds/party_over.png"),
        "menu_scene": Load("backgrounds/menu_scene.png"),
        "nav_panel": Load("ui/nav_panel.png"),
        "summary_panel": Load("ui/summary_panel.png"),
        "cabinet_reveal": Load("backgrounds/cabinet_reveal.png"),
        "ambient_glow": [Load(f"ui/ambient_glow_{I}.png") for I in range(3)],
        "lock_badge": Load("ui/lock_badge.png"),
        "ticket_reward": Load("ui/ticket.png").zoom(4),
        "draw_mystery": Load("cups/unknown.png").zoom(4),
        "unlock_frames": [Load(f"ui/unlock_{Index}.png").zoom(3) for Index in range(4)],
        "icons": {
            Name: Load(f"ui/{Name}.png")
            for Name in (
                "play",
                "book",
                "endless",
                "help",
                "cup",
                "ticket",
                "odds",
                "back",
                "home",
                "exit",
                "restart",
                "new_game",
                "settings",
                "audio",
                "display",
                "done",
                "lock",
                "batch",
                "music",
                "effects",
            )
        },
        "icons_dark": {
            Name: Load(f"ui/{Name}_dark.png")
            for Name in (
                "play",
                "book",
                "endless",
                "help",
                "cup",
                "ticket",
                "odds",
                "back",
                "home",
                "exit",
                "restart",
                "new_game",
                "settings",
                "audio",
                "display",
                "done",
                "lock",
                "batch",
                "music",
                "effects",
            )
        },
    }


def PlaceImage(Game, Image, X, Y):
    """x/y locate the top-left corner in Turtle coordinates."""
    return Game.Session.Screen.getcanvas().create_image(
        X, -Y, image=Image, anchor="nw", tags=(Game.Session.ArtLayer,)
    )


def PlaceSkin(Game, Skin, Size, X, Y, Anchor="nw", ExtraTags=()):
    return Game.Session.Screen.getcanvas().create_image(
        X,
        -Y,
        image=Game.Session.Assets["skins"][Skin][Size],
        anchor=Anchor,
        tags=(Game.Session.ArtLayer, "animated_skin", f"skin:{Skin}", f"size:{Size}")
        + ExtraTags,
    )


def Scenery(Game, Menu=False):
    Name = "menu" if Menu else Location(Game.Session.Mode, Game.Session.Level)
    Game.Session.scene_location = "hall" if Menu else Name
    Right = 470
    Game.Rectangle(-470, -174, Right, 236, "#191522")
    Item = PlaceImage(
        Game,
        (
            Game.Session.Assets["menu_scene"]
            if Menu
            else Game.Session.Assets["backgrounds"][Name]
        ),
        -470,
        236,
    )
    Game.Session.Screen.getcanvas().addtag_withtag("background_art", Item)


def DrawTitle(Game, X, Y):
    PlaceImage(Game, Game.Session.Assets["title"], X, Y)


def Frame(Game, X1, Y1, X2, Y2, Fill="#1b2430", Edge="#526071"):
    """One shared panel treatment with a quiet edge and a recessed shadow."""
    R = Game.Rectangle
    R(X1 + 2, Y1 - 3, X2 + 2, Y2 - 3, "#0c121b")
    R(X1, Y1, X2, Y2, Edge)
    R(X1 + 1, Y1 + 1, X2 - 1, Y2 - 1, Fill)
    R(X1 + 2, Y2 - 2, X2 - 2, Y2 - 1, "#70808b" if Edge == "#526071" else Edge)
