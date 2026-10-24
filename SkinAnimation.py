"""Shared skin animation clock. Every gameplay cup uses the same frame."""

import turtle as Turtle


class SkinAnimation:
    def __init__(Self, Session):
        Self.Session = Session
        Self.Tick = 0
        Self.Frame = -1

    def BeginRound(Self):
        G = Self.Session
        Skin = G.Profile["equipped"]
        G.Screen.register_shape(
            Skin + "_cup", Turtle.Shape("image", G.Assets["skins"][Skin][2])
        )
        Self.Tick = Self.Frame = 0

    def Update(Self):
        G = Self.Session
        if G.State in ("paused", "settings"):
            return
        Self.Tick += 1
        Frame = (Self.Tick // 12) % 4 if G.Settings.Values["motion"] else 0
        if Frame == Self.Frame:
            return
        Self.Frame = Frame
        Canvas = G.Screen.getcanvas()
        for Item in Canvas.find_withtag("animated_skin"):
            Tags = Canvas.gettags(Item)
            Skin = next(Tag[5:] for Tag in Tags if Tag.startswith("skin:"))
            Size = int(next(Tag[5:] for Tag in Tags if Tag.startswith("size:")))
            Canvas.itemconfigure(Item, image=G.Assets["skin_frames"][Skin][Frame][Size])
        if G.Cups:
            Skin = G.Profile["equipped"]
            Image = G.Assets["skin_frames"][Skin][Frame][2]
            G.Screen.register_shape(Skin + "_cup", Turtle.Shape("image", Image))
            for Cup in G.Cups:
                Cup.Sprite.shape(Skin + "_cup")
                Cup.Render()
