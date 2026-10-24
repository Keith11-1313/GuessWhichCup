"""Small, time-stepped presentation effects; never change game outcomes."""

from NamingCompatibility import ReadAttribute

import math as Math


class UiMotion:
    def __init__(Self, Session):
        Self.Session = Session
        Self.Hover = None
        Self.HoverValue = 0.0
        Self.Transition = 20
        Self.BurstFrame = 60
        Self.Good = True
        Self.Lifts = []
        Self.ModalStep = 16
        Self.ModalOffset = 0

    def Begin(Self):
        Self.Transition = 20 if ReadAttribute(Self, "suppress_transition", False) else 0
        Self.SuppressTransition = False
        Self.Hover = None
        Self.HoverValue = 0.0
        Self.BurstFrame = 60
        Self.Lifts = []
        Canvas = Self.Session.Screen.getcanvas()
        for Tag in ("ui_transition", "ui_hover", "ui_burst", "answer_timer"):
            Canvas.delete(Tag)

    def Feedback(Self, Good):
        Self.Good = Good
        Self.BurstFrame = 0

    def Modal(Self):
        Self.ModalStep = 0
        Self.ModalOffset = 12 if Self.Session.Settings.Values["motion"] else 0
        Self.Session.Screen.getcanvas().move("pause_art", 0, Self.ModalOffset)

    def Lift(Self, Cups):
        Self.Lifts = [(Cup, 0) for Cup in Cups]
        if Self.Session.Settings.Values["motion"]:
            for Cup, Ignored in Self.Lifts:
                Cup.Y = 0
                Cup.Render()

    def Pointer(Self, X, Y):
        Self.Hover = next(
            (
                Key
                for Key, (X1, Y1, X2, Y2) in Self.Session.Buttons.items()
                if X1 <= X <= X2 and Y1 <= Y <= Y2
            ),
            None,
        )
        if Self.Session.State == "select":
            Self.Hover = next(
                (f"cup:{Cup.Slot}" for Cup in Self.Session.Cups if Cup.Contains(X, Y)),
                None,
            )

    def Update(Self):
        G = Self.Session
        Canvas = G.Screen.getcanvas()
        for Tag in ("ui_transition", "ui_hover", "ui_burst"):
            Canvas.delete(Tag)
        if Self.ModalStep < 16:
            Self.ModalStep += 1
            Offset = (
                12 * (1 - Self.ModalStep / 16) ** 3
                if G.Settings.Values["motion"]
                else 0
            )
            Canvas.move("pause_art", 0, Offset - Self.ModalOffset)
            Self.ModalOffset = Offset
        if not G.Settings.Values["motion"]:
            Self.Transition = 20
            for Cup, Ignored in Self.Lifts:
                Cup.Y = 76
                Cup.Render()
            Self.Lifts = []
            return
        if G.State in ("result", "retry", "resolving", "last_reveal", "victory"):
            Pending = []
            for Cup, Step in Self.Lifts:
                Step = min(16, Step + 1)
                T = Step / 16
                Cup.Y = 76 * (1 - (1 - T) ** 3)
                Cup.Render()
                if Step < 16:
                    Pending.append((Cup, Step))
            Self.Lifts = Pending
        Self.Transition = min(20, Self.Transition + 1)
        Targets = dict(G.Buttons)
        if G.State == "select":
            Targets.update(
                {f"cup:{Cup.Slot}": (Cup.X - 45, -53, Cup.X + 45, 53) for Cup in G.Cups}
            )
        Self.HoverValue += (
            (1.0 if Self.Hover in Targets else 0.0) - Self.HoverValue
        ) * 0.25
        if Self.Hover in Targets:
            X1, Y1, X2, Y2 = Targets[Self.Hover]
            V = Self.HoverValue
            Color = "#%02x%02x%02x" % (
                int(113 + 129 * V),
                int(81 + 110 * V),
                int(102 + 2 * V),
            )
            Canvas.create_rectangle(
                X1 + 1,
                -Y2 + 1,
                X2 - 1,
                -Y1 - 1,
                outline=Color,
                width=2,
                tags=("ui_hover",),
            )
        if Self.BurstFrame < 40 and G.State not in ("paused", "settings"):
            Self.BurstFrame += 1
            T = Self.BurstFrame / 40
            Color = "#f3c66c" if Self.Good else "#e88a9a"
            for I in range(12):
                Angle = I * Math.tau / 12
                X = Math.cos(Angle) * (35 + T * 140)
                Y = Math.sin(Angle) * (20 + T * 65) + T * T * 35
                Size = max(1, 4 * (1 - T))
                Canvas.create_rectangle(
                    X - Size,
                    Y - Size,
                    X + Size,
                    Y + Size,
                    fill=Color,
                    width=0,
                    tags=("ui_burst",),
                )
        if Self.Transition < 14:
            # Two curtains reveal the newly painted scene over 238 ms.
            P = Self.Transition / 14
            Width = 470 * (1 - P) ** 3
            for X1, X2 in ((-470, -470 + Width), (470 - Width, 470)):
                Canvas.create_rectangle(
                    X1, -236, X2, 292, fill="#191522", width=0, tags=("ui_transition",)
                )
