"""Short canvas animations. Rewards are saved by gameplay, never by animation."""

from GameTheme import LabelWidth


class VisualEffects:
    def __init__(Self, Session):
        Self.Session = Session
        Self.Kind = None
        Self.Frame = 0

    def Clear(Self):
        Self.Session.Screen.getcanvas().delete("reward_fx")
        Self.Kind = None
        Self.Frame = 0

    def Award(Self, Points, Ticket):
        Self.Clear()
        Self.Kind = "award"
        Self.Points, Self.Ticket = Points, Ticket
        Self.Draw()

    def Duplicate(Self, Skin):
        Self.Clear()
        Self.Kind = "duplicate"
        Self.Skin = Skin
        Self.Draw()

    def Update(Self):
        if Self.Kind:
            Self.Frame += 1
            Self.Draw()

    def Label(Self, Text, Y, Size, Color):
        X = -LabelWidth(Text, Size) / 2
        Self.Session.Views.CanvasLabel(X, -Y, Text, Size, Color, ("reward_fx",))

    def Draw(Self):
        G = Self.Session
        Canvas = G.Screen.getcanvas()
        Canvas.delete("reward_fx")
        if Self.Kind == "award":
            if Self.Frame >= 100:
                Self.Clear()
                return
            Rise = min(42, Self.Frame * 0.55)
            Canvas.create_rectangle(
                -143,
                40 - Rise,
                143,
                119 - Rise,
                fill="#211b2c",
                outline="#947454",
                tags=("reward_fx",),
            )
            Canvas.create_image(
                -116, 64 - Rise, image=G.Assets["coin"], tags=("reward_fx",)
            )
            Self.Label(f"+{Self.Points:,} points", -64 + Rise, 18, "#ffe1a0")
            if Self.Ticket:
                Canvas.create_image(
                    -105,
                    96 - Rise,
                    image=G.Assets["icons"]["ticket"],
                    tags=("reward_fx",),
                )
                Self.Label("+1 ticket", -96 + Rise, 14, "#a9d7ab")
        elif Self.Kind == "duplicate":
            if Self.Frame < 45:
                Size = max(0, 3 - Self.Frame // 12)
                Image = G.Assets["skins"][Self.Skin][Size]
                Canvas.create_image(0, -60, image=Image, tags=("reward_fx",))
            else:
                Image = G.Assets["ticket_reward"]
                Canvas.create_image(
                    0,
                    -60 - min(12, (Self.Frame - 45) * 0.3),
                    image=Image,
                    tags=("reward_fx",),
                )
                Self.Label("+1 ticket", -118, 18, "#a9d7ab")
            if Self.Frame >= 100:
                Self.Kind = None  # Keep the converted ticket visible until navigation.
