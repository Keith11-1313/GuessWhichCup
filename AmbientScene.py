"""Slow lantern glow and a few background motes, behind the playable cups."""

import math as Math


class AmbientScene:
    def __init__(Self, Session):
        Self.Session = Session
        Self.Frame = 0

    def Update(Self):
        G = Self.Session
        Canvas = G.Screen.getcanvas()
        if G.State in ("paused", "settings"):
            return
        Self.Frame += 1
        if Self.Frame % 4:
            return
        Canvas.delete("ambient_art")
        if not G.Settings.Values["motion"]:
            return
        Phase = (Self.Frame // 70) % 4
        Glow = G.Assets["ambient_glow"][(0, 1, 2, 1)[Phase]]
        Lights = (
            ((-452, 100), (452, 115))
            if G.State in ("menu", "menu_setup")
            else ((-388, 155), (350, 135))
        )
        for X, Y in Lights:
            Canvas.create_image(X, -Y, image=Glow, tags=("ambient_art",))
        for I in range(6):
            Side = -1 if I % 2 else 1
            X = Side * (448 + I % 3 * 5) + Math.sin(Self.Frame / 170 + I) * 4
            Y = -125 - Math.sin(Self.Frame / 210 + I) * 22
            Canvas.create_rectangle(
                X, Y, X + 2, Y + 2, fill="#9b9578", width=0, tags=("ambient_art",)
            )
        if Canvas.find_withtag("background_art"):
            Canvas.tag_raise("ambient_art", "background_art")
