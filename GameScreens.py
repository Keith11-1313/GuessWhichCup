"""Menu, story, HUD and drawing helpers for the shared Game session."""

from GameConfig import (
    Colors,
    Difficulties,
    ResultButtonBounds,
    StoryLevels,
    FrameMs,
)
import math as Math
from tkinter import font as Font
from GameTheme import TextFont, LabelRuns, LabelWidth
from PartyArt import Scenery, Frame, DrawTitle, PlaceImage, PlaceSkin
import CupCollection as Collection
from PartyStory import Chapters, LocationNames, Location

White = Colors["white"]
Muted = Colors["muted"]
Gold = Colors["gold"]


class GameScreens:

    def __init__(Self, Session):
        Self.Session = Session

    def Write(Self, Pen, X, Y, Text, Size=16, Color=White, Align="center"):
        Pen.color(Color)
        Width = LabelWidth(Text, Size, Size >= 16)
        Cursor = (
            X - Width / 2 if Align == "center" else X - Width if Align == "right" else X
        )
        for Part, Style in LabelRuns(Text, Size, Size >= 16):
            Pen.goto(Cursor, Y)
            Pen.write(Part, align="left", font=Style)
            Cursor += Font.Font(font=Style).measure(Part)

    def CanvasLabel(Self, X, Y, Text, Size, Color, Tags):
        """Draw mixed-font labels from their left edge, vertically centered."""
        Canvas = Self.Session.Screen.getcanvas()
        for Part, Style in LabelRuns(Text, Size):
            Canvas.create_text(
                X, Y, text=Part, anchor="w", font=Style, fill=Color, tags=Tags
            )
            X += Font.Font(font=Style).measure(Part)

    def WriteFitted(Self, Pen, X, Y, Text, Width, Size=12, Color=White):
        """Measure the actual mixed-font label before placing it in a fixed area."""
        while Size > 9 and LabelWidth(Text, Size, Size >= 16) > Width:
            Size -= 1
        Self.Write(Pen, X, Y, Text, Size, Color, "left")

    def WriteWrapped(Self, Pen, X, Y, Text, Width, Size=12, Color=Muted):
        """Wrap dialogue before its action button, preserving readable text."""
        Measure = lambda Text: LabelWidth(Text, Size)
        Lines = []
        Line = ""
        for Word in Text.split():
            Candidate = f"{Line} {Word}".strip()
            if Line and Measure(Candidate) > Width:
                Lines.append(Line)
                Line = Word
            else:
                Line = Candidate
        Lines.append(Line)
        for Index, Line in enumerate(Lines):
            Self.Write(Pen, X, Y - Index * 21, Line, Size, Color, "left")

    def Rectangle(Self, X1, Y1, X2, Y2, Fill, Outline=None):
        Self.Session.Screen.getcanvas().create_rectangle(
            X1,
            -Y2,
            X2,
            -Y1,
            fill=Fill,
            outline=Outline or Fill,
            width=0 if Outline is None else 1,
            tags=(Self.Session.ArtLayer,),
        )

    def DrawBackground(Self, View="game"):
        Self.Session.Motion.Begin()
        Self.Session.Effects.Clear()
        Self.Session.Static.clear()
        Canvas = Self.Session.Screen.getcanvas()
        for Layer in (
            "scene",
            "hud_art",
            "choice_art",
            "message_art",
            "draw_fx",
            "pause_art",
            "batch_action",
        ):
            Canvas.delete(Layer)
        Self.Session.ArtLayer = "scene"
        Scenery(Self, Menu=View == "menu")
        Self.Session.Viewport.RefreshBackdrop()
        DrawTitle(Self, -466, 306)
        Self.Write(Self.Session.Static, 467, 288, "Lantern House", 16, Gold, "right")
        Self.Write(
            Self.Session.Static, 467, 266, "A night to remember", 10, Muted, "right"
        )
        Self.Rectangle(-470, 255, 470, 257, "#43515f")
        if View != "menu":
            Frame(Self, -470, -292, 470, -184, "#1b2430")
        Self.DrawFooter()
        # Pooled cup sprites already exist when this new scenery is painted.
        # Keep the scenery behind them; movement alone does not raise images.
        Canvas.tag_lower("scene")

    def DrawButton(Self, Name, Text, X, Y, Width, Active=False):
        Fill = Gold if Active else "#283645"
        Frame(
            Self,
            X - Width / 2,
            Y - 22,
            X + Width / 2,
            Y + 22,
            Fill,
            "#ffe0a0" if Active else "#526071",
        )
        IconName = {
            "start": "play",
            "story_next": "play",
            "mode:Story": "book",
            "play_again": "restart",
            "game_menu": "back",
            "resume": "play",
            "resume_run": "play",
            "new_game_setup": "new_game",
            "back_saved": "back",
            "save_menu": "home",
            "save_exit": "exit",
            "restart": "restart",
            "convert_duplicate": "play",
            "mode:Endless": "endless",
            "howto": "help",
            "cabinet": "cup" if Text == "Cup cabinet" else "back",
            "settings": "settings",
            "setting:back": "done",
            "setting:tab_audio": "audio",
            "setting:tab_display": "display",
            "locked_cabinet": "lock",
            "draw10": "batch",
            "batch_next": "play",
            "page:previous": "back",
            "page:next": "play",
            "draw": "ticket",
            "odds": "odds",
            "back": "back",
        }.get(Name)
        if Name.startswith("equip:"):
            IconName = "cup"
        if Name == "batch_next" and Text == "Done":
            IconName = "done"
        Palette = "icons_dark" if Active else "icons"
        Icon = Self.Session.Assets[Palette][IconName] if IconName else None
        Offset = Icon.width() + 10 if Icon is not None else 0
        Size = 12
        while Size > 9 and LabelWidth(Text, Size) + Offset > Width - 28:
            Size -= 1
        TextWidth = LabelWidth(Text, Size)
        Left = X - (TextWidth + Offset) / 2
        if IconName:
            PlaceImage(Self, Icon, Left, Y + Icon.height() / 2)
        Self.CanvasLabel(
            Left + Offset,
            -Y,
            Text,
            Size,
            "#17202b" if Active else White,
            (Self.Session.ArtLayer,),
        )
        Self.Session.Buttons[Name] = (X - Width / 2, Y - 22, X + Width / 2, Y + 22)

    def ShowHowToPlay(Self):
        Self.Session.State = "how_to_play"
        Self.Session.ClearCups()
        Self.DrawBackground()
        Self.Session.MenuText.clear()
        Self.Session.HudText.clear()
        Self.Session.Message.clear()
        Self.Session.Buttons = {}
        Frame(Self, -365, -156, 365, 224, "#1b2430")
        Self.Write(
            Self.Session.MenuText, -330, 177, "A little party trick", 24, Gold, "left"
        )
        Self.Write(
            Self.Session.MenuText,
            -330,
            140,
            "Three moments. One lucky coin to keep safe.",
            12,
            Muted,
            "left",
        )
        for Y, Title, Detail in (
            (80, "Remember", "Look for the coin underneath the lifted cup."),
            (8, "Follow", "Track that cup as the table shuffles."),
            (-64, "Choose", "Click its cup or press the matching number."),
        ):
            Self.Rectangle(-330, Y - 16, -326, Y + 20, Gold)
            Self.Write(Self.Session.MenuText, -306, Y, Title, 16, White, "left")
            Self.Write(Self.Session.MenuText, -306, Y - 26, Detail, 12, Muted, "left")
        Self.Write(
            Self.Session.MenuText,
            -330,
            -132,
            "Correct picks earn points. Mistakes and timeouts cost one life.",
            11,
            Muted,
            "left",
        )
        Self.SetMessage(
            "Take your time",
            "P pauses. O opens Settings. F11 full screen. - and = music volume.",
        )
        Self.DrawButton("back", "Back to the party", 312, -260, 242, True)
        Self.Session.Screen.update()

    def ShowMenu(Self, NewGame=False):
        G = Self.Session
        G.Motion.SuppressTransition = G.State == ("menu_setup" if NewGame else "menu")
        G.UpdateWindowIcon()
        G.State = "menu_setup" if NewGame else "menu"
        G.ClearCups()
        Self.DrawBackground(View="menu")
        G.MenuText.clear()
        G.HudText.clear()
        G.Message.clear()
        G.Buttons = {}
        if not G.Profile.get("story_completed", False):
            G.Mode = "Story"
        if G.SavedRun and not NewGame:
            Self.DrawSavedRunMenu()
        else:
            Self.DrawNewGameMenu(NewGame)
        Self.Rectangle(-470, -287, 470, -241, "#101820")
        Item = PlaceSkin(Self, G.Profile["equipped"], 0, -438, -246)
        G.Screen.getcanvas().addtag_withtag("menu_cup", Item)
        Self.Write(
            G.MenuText,
            -390,
            -272,
            f"{sum(Cup[0] in G.Profile['owned'] for Cup in Collection.Cups)} of {len(Collection.Cups)} cups",
            12,
            White,
            "left",
        )
        PlaceImage(Self, G.Assets["icons"]["ticket"], -225, -252)
        Self.Write(
            G.MenuText, -193, -272, f"{G.Profile['tickets']} tickets", 12, Gold, "left"
        )
        if not G.SavedRun or NewGame:
            Unlocked = G.Profile.get("story_completed", False)
            Self.DrawButton(
                "cabinet" if Unlocked else "locked_cabinet",
                "Cup cabinet" if Unlocked else "Finish Story to unlock",
                320,
                -259,
                236,
            )
            if not Unlocked:
                G.Buttons.pop("locked_cabinet", None)
        else:
            Self.Write(
                G.MenuText,
                438,
                -272,
                "Your collection stays with you.",
                11,
                Muted,
                "right",
            )
        G.Screen.update()

    def DrawChoiceCard(
        Self, Name, Title, Detail, X, Bottom, Width, Height, Selected, Hearts=0
    ):
        """The entire card is clickable; a tick distinguishes selection from Start."""
        Fill = "#2b3a46" if Selected else "#1b2835"
        Edge = Gold if Selected else "#526071"
        Frame(Self, X, Bottom, X + Width, Bottom + Height, Fill, Edge)
        if Selected:
            Self.Rectangle(X + 2, Bottom + 2, X + 5, Bottom + Height - 2, Gold)
            Canvas = Self.Session.Screen.getcanvas()
            Cx, Cy = X + Width - 19, -(Bottom + Height - 17)
            Canvas.create_line(
                Cx - 5,
                Cy,
                Cx - 1,
                Cy + 4,
                Cx + 6,
                Cy - 5,
                fill=Gold,
                width=2,
                tags=(Self.Session.ArtLayer,),
            )
        Self.WriteFitted(
            Self.Session.MenuText,
            X + 14,
            Bottom + Height - 42,
            Title,
            Width - 55,
            17 if Hearts else 20,
            Gold if Selected else White,
        )
        if Hearts:
            for Index in range(Hearts):
                PlaceImage(
                    Self,
                    Self.Session.Assets["heart_full"],
                    X + 22 + Index * 27,
                    Bottom + 48,
                )
            Self.WriteFitted(
                Self.Session.MenuText,
                X + 22,
                Bottom + 12,
                Detail,
                Width - 44,
                10,
                Muted,
            )
        else:
            Self.WriteFitted(
                Self.Session.MenuText,
                X + 22,
                Bottom + 22,
                Detail,
                Width - 44,
                12,
                Muted,
            )
        Self.Session.Buttons[Name] = (X, Bottom, X + Width, Bottom + Height)

    def DrawNewGameMenu(Self, NewGame):
        G, Pen = Self.Session, Self.Session.MenuText
        Self.Rectangle(-470, 151, 470, 236, "#17202b")
        Self.Rectangle(-470, -233, 470, -146, "#17202b")
        Self.Write(Pen, -438, 193, "New game", 27, Gold, "left")
        Self.DrawButton(
            "back_saved" if NewGame else "settings",
            "Back" if NewGame else "Settings",
            366,
            204,
            144,
        )
        Self.Write(Pen, -438, 160, "Choose your evening", 12, Muted, "left")
        for X, Mode, Detail in (
            (-438, "Story", "Earn Brass Keepsake in 10 tables."),
            (18, "Endless", "Keep the coin. Beat your best score."),
        ):
            Locked = Mode == "Endless" and not G.Profile.get("story_completed", False)
            Self.DrawChoiceCard(
                "mode:" + Mode,
                Mode,
                "Finish Story to unlock." if Locked else Detail,
                X,
                39,
                420,
                105,
                G.Mode == Mode,
            )
            if Locked:
                PlaceImage(Self, G.Assets["icons"]["lock"], X + 370, 128)
                G.Buttons.pop("mode:Endless", None)
        Self.Write(Pen, -438, 7, "Choose the challenge", 12, Muted, "left")
        for X, Difficulty, Detail in (
            (-438, "Easy", "Slower shuffles"),
            (-138, "Normal", "Balanced speed"),
            (162, "Hard", "Faster shuffles"),
        ):
            Self.DrawChoiceCard(
                "diff:" + Difficulty,
                Difficulty,
                Detail,
                X,
                -125,
                276,
                111,
                G.Difficulty == Difficulty,
                Difficulties[Difficulty]["lives"],
            )
        Self.Write(
            Pen,
            -438,
            -170,
            f"Best {G.Mode} score  {G.BestScore():,}",
            12,
            Muted,
            "left",
        )
        if G.SavedRun:
            Self.WriteFitted(
                Pen,
                -438,
                -204,
                "Starting replaces the saved run. Back keeps it.",
                520,
                11,
                "#e4bc88",
            )
        else:
            Self.Write(
                Pen,
                -438,
                -204,
                "Watch the coin. Follow the cup. Make your pick.",
                11,
                Muted,
                "left",
            )
        Self.DrawButton("start", "Start " + G.Mode, 288, -190, 300, True)

    def DrawSavedRunMenu(Self):
        G, Pen = Self.Session, Self.Session.MenuText
        Saved = G.SavedRun
        PlaceImage(Self, G.Assets["nav_panel"], -470, 236)
        Self.Write(Pen, -438, 186, "The Last Lantern", 25, Gold, "left")
        Self.Write(
            Pen, -438, 151, "A coin. Ten tables. One keepsake.", 12, White, "left"
        )
        for Key, Label, Y, Active in (
            ("resume_run", "Resume " + Saved["mode"], 79, True),
            ("new_game_setup", "New game", 17, False),
            ("cabinet", "Cup cabinet", -45, False),
            ("settings", "Settings", -107, False),
            ("howto", "How to play", -169, False),
        ):
            Locked = Key == "cabinet" and not G.Profile.get("story_completed", False)
            Self.DrawButton(
                "locked_cabinet" if Locked else Key,
                "Cabinet locked" if Locked else Label,
                -265,
                Y,
                344,
                Active,
            )
            if Locked:
                G.Buttons.pop("locked_cabinet", None)
        PlaceImage(Self, G.Assets["summary_panel"], -30, 236)
        Self.Rectangle(-30, 231, 470, 236, "#a3d4bb")
        Self.Write(Pen, 2, 190, "Your saved game", 17, "#a3d4bb", "left")
        PlaceImage(
            Self,
            G.Assets["icons"]["book" if Saved["mode"] == "Story" else "endless"],
            2,
            156,
        )
        Self.Write(Pen, 32, 134, Saved["mode"], 26, White, "left")
        Self.Write(Pen, 438, 142, Saved["difficulty"], 13, Muted, "right")
        Self.Write(
            Pen,
            2,
            100,
            LocationNames[Location(Saved["mode"], Saved["level"])],
            13,
            Muted,
            "left",
        )
        Self.Rectangle(2, 76, 438, 77, "#43515f")
        Self.Write(
            Pen,
            2,
            41,
            "Chapter" if Saved["mode"] == "Story" else "Round",
            12,
            Muted,
            "left",
        )
        Self.Write(Pen, 248, 41, "Saved score", 12, Muted, "left")
        Self.Write(Pen, 2, -3, str(Saved["level"]), 30, White, "left")
        Self.WriteFitted(Pen, 248, -3, f"{Saved['score']:,}", 190, 28, White)
        Self.Write(Pen, 2, -55, "Lives remaining", 12, Muted, "left")
        for Index in range(Difficulties[Saved["difficulty"]]["lives"]):
            Icon = "heart_full" if Index < Saved["lives"] else "heart_empty"
            PlaceImage(Self, G.Assets[Icon], 248 + Index * 31, -35)
        if Saved["mode"] == "Story":
            Self.Write(
                Pen,
                2,
                -116,
                f"{Saved['level']-1} of 10 table marks earned",
                12,
                Gold,
                "left",
            )
            for Index in range(10):
                Self.Rectangle(
                    2 + Index * 44,
                    -143,
                    38 + Index * 44,
                    -133,
                    Gold if Index < Saved["level"] - 1 else "#43515f",
                )
        else:
            Self.Write(Pen, 2, -116, "The afterparty continues.", 15, Gold, "left")
        Self.WriteWrapped(
            Pen,
            2,
            -188,
            "Resume picks up at your saved table. New game keeps your cups and tickets.",
            420,
            11,
            Muted,
        )

    def ShowGameOver(Self):
        """Dedicated end-of-run scene; displaying it never changes saved progress."""
        Self.Session.State = "over"
        Self.Session.ClearCups()
        Self.Session.MenuText.clear()
        Self.Session.HudText.clear()
        Self.Session.Message.clear()
        Self.Session.Buttons = {}
        Self.DrawBackground()
        Frame(Self, -470, -292, 470, 236, "#141d27")
        PlaceImage(Self, Self.Session.Assets["party_over"], -468, 234)
        Pen = Self.Session.MenuText
        Self.Write(Pen, 0, -62, "Party over", 28, Gold)
        Self.Write(
            Pen,
            0,
            -91,
            "The coin slipped away. There is still a seat for you.",
            12,
            White,
        )
        Progress = "Chapter" if Self.Session.Mode == "Story" else "Round"
        for X, Label, Value in (
            (-268, "Final score", f"{Self.Session.Score:,}"),
            (0, "Best score", f"{Self.Session.BestScore():,}"),
            (268, Progress, str(Self.Session.Level)),
        ):
            Self.Write(Pen, X, -132, Label, 11, Muted)
            Self.Write(Pen, X, -164, Value, 20, White)
        Warning = Self.Session.SaveFailed or Self.Session.RewardFailed
        if Warning:
            Self.Write(
                Pen,
                0,
                -197,
                "Save failed. Check folder permissions.",
                11,
                Colors["danger"],
            )
        Self.DrawButton("play_again", "Restart run", -128, -246, 224, True)
        Self.DrawButton("game_menu", "Menu", 128, -246, 224)
        Self.DrawFooter()
        Self.Session.Screen.update()

    def DrawHud(Self):
        Self.Session.HudText.clear()
        Self.Session.Screen.getcanvas().delete("hud_art")
        Self.Session.ArtLayer = "hud_art"
        Self.Rectangle(-470, 174, 470, 236, "#141d27")
        Self.Rectangle(-470, 174, -466, 236, Gold)
        Self.Write(
            Self.Session.HudText,
            -445,
            209,
            f"{Self.Session.Mode}   {Self.Session.Difficulty}",
            12,
            White,
            "left",
        )
        TotalLives = Difficulties[Self.Session.Difficulty]["lives"]
        for Index in range(TotalLives):
            Name = "heart_full" if Index < Self.Session.Lives else "heart_empty"
            PlaceImage(Self, Self.Session.Assets[Name], -445 + Index * 29, 201)
        Title = (
            f"Chapter {Self.Session.Level} of {StoryLevels}"
            if Self.Session.Mode == "Story"
            else f"Round {Self.Session.Level}   Combo {Self.Session.Combo}"
        )
        Self.Write(Self.Session.HudText, -12, 207, Title, 13, Gold)
        Chapter = LocationNames[Location(Self.Session.Mode, Self.Session.Level)]
        Self.Write(Self.Session.HudText, -12, 185, Chapter, 10, Muted)
        Self.Write(
            Self.Session.HudText,
            443,
            207,
            f"Score  {Self.Session.Score:,}",
            16,
            Gold,
            "right",
        )
        Self.Write(
            Self.Session.HudText,
            443,
            185,
            f"Best  {Self.Session.BestScore():,}",
            10,
            Muted,
            "right",
        )
        Self.Session.ArtLayer = "scene"

    def SetMessage(Self, Text, Detail="", Color=White):
        Self.Session.Message.clear()
        Self.Session.Screen.getcanvas().delete("message_art")
        Self.Write(Self.Session.Message, -442, -222, Text, 18, Color, "left")
        if Self.Session.State in ("result", "retry", "over", "victory") and (
            Self.Session.SaveFailed or Self.Session.RewardFailed
        ):
            Detail = "Save failed. Check folder permissions."
        if Detail:
            Self.WriteWrapped(
                Self.Session.Message,
                -442,
                -251,
                Detail,
                (
                    650
                    if Self.Session.State in ("result", "retry", "over", "victory")
                    else 880
                ),
            )
        if Self.Session.State in ("result", "retry", "over", "victory"):
            Label = (
                "Next"
                if Self.Session.State == "result"
                else (
                    "Retry"
                    if Self.Session.State == "retry"
                    else (
                        "Retry save"
                        if Self.Session.State == "victory"
                        and Self.Session.StoryUnlockPending
                        else (
                            "Cup cabinet"
                            if Self.Session.State == "victory"
                            else "Restart run"
                        )
                    )
                )
            )
            Self.Session.ArtLayer = "message_art"
            Frame(Self, *ResultButtonBounds, Gold, "#ffe0a0")
            Self.Session.ArtLayer = "scene"
            Self.Write(Self.Session.Message, 340, -269, Label, 12, "#17202b")
        Self.DrawFooter()

    def DrawFooter(Self):
        Self.Session.Footer.clear()
        Self.Session.Screen.getcanvas().delete("footer_art")
        Self.Session.FooterActions = {}
        State = Self.Session.State
        if State == "settings":
            Left, Right = [], ("escape", "Esc  Back")
        elif State == "menu_setup":
            Left = [("advance", "Enter  Start " + Self.Session.Mode)]
            Right = ("escape", "Esc  Back")
        elif State == "menu":
            Left = [
                (
                    "advance",
                    "Enter  Resume saved" if Self.Session.SavedRun else "Enter  Play",
                ),
                ("help", "H  Help"),
            ]
            Right = ("escape", "Esc  Quit")
        elif State == "paused":
            Left = [
                ("pause", "P  Resume"),
                (
                    "sound",
                    "S  Sound on" if Self.Session.SoundEnabled else "S  Sound off",
                ),
            ]
            Right = ("escape", "Esc  Resume")
        elif State in ("reveal", "shuffle", "select"):
            Pause = "P  Resume" if State == "paused" else "P  Pause"
            Sound = "S  Sound on" if Self.Session.SoundEnabled else "S  Sound off"
            Left = [("pause", Pause), ("sound", Sound)]
            Right = ("menu", "M  Menu")
        elif State == "story":
            Left, Right = [("advance", "Enter  Play")], ("menu", "M  Menu")
        elif State == "last_reveal":
            Left, Right = [], ("advance", "Enter  Continue")
        elif State == "over":
            Left, Right = [("advance", "Enter  Restart run")], ("menu", "M  Menu")
        elif State in ("result", "retry", "victory"):
            Left, Right = [("advance", "Enter  Continue")], ("menu", "M  Menu")
        elif State in ("cabinet", "gacha_opening", "gacha_reveal", "batch_reveal"):
            Label = "Enter  Draw" if State == "cabinet" else "Enter  Reveal"
            if State == "gacha_reveal":
                Label = (
                    "Enter  Next"
                    if Self.Session.Cabinet.DuplicatePending
                    else "Enter  Cabinet"
                )
            if State == "batch_reveal":
                Label = (
                    "Enter  Next"
                    if Self.Session.Cabinet.BatchPending
                    else "Enter  Done"
                )
            Left, Right = [("advance", Label)], ("escape", "Esc  Back")
        else:
            Left, Right = [], ("escape", "Esc  Back")
        if not any(Action == "sound" for Action, Ignored in Left):
            Left.append(
                (
                    "sound",
                    "S  Sound on" if Self.Session.SoundEnabled else "S  Sound off",
                )
            )
        if State in ("menu", "menu_setup", "paused"):
            Left.append(("settings", "O  Settings"))
        if Self.Session.SoundEnabled:
            Left = [
                (
                    Action,
                    (
                        f"S  Master {Self.Session.Settings.Values['master']}%"
                        if Action == "sound"
                        else Label
                    ),
                )
                for Action, Label in Left
            ]
        Measure = lambda Text: LabelWidth(Text, 11)
        OldLayer = Self.Session.ArtLayer
        Self.Session.ArtLayer = "footer_art"
        X = -464
        for Action, Label in Left:
            Key, Caption = Label.split("  ", 1)
            Width = max(28, Measure(Key) + 14) + 10 + Measure(Caption)
            Self.FooterLink(Action, Label, X, Width)
            X += Width + 22
        Action, Label = Right
        Key, Caption = Label.split("  ", 1)
        Width = max(28, Measure(Key) + 14) + 10 + Measure(Caption)
        Self.FooterLink(Action, Label, 464 - Width, Width)
        Self.Session.ArtLayer = OldLayer

    def FooterLink(Self, Action, Label, X, Width):
        Key, Caption = Label.split("  ", 1)
        KeyWidth = max(28, Font.Font(font=TextFont(11)).measure(Key) + 14)
        Self.Rectangle(X, -334, X + KeyWidth, -308, "#100e19")
        Self.Rectangle(X, -331, X + KeyWidth, -307, "#76576c")
        Self.Rectangle(X + 2, -328, X + KeyWidth - 2, -309, "#283645")
        Canvas = Self.Session.Screen.getcanvas()
        Canvas.create_text(
            X + KeyWidth / 2,
            319,
            text=Key,
            font=TextFont(11),
            fill=White,
            tags=("footer_art",),
        )
        Self.CanvasLabel(X + KeyWidth + 10, 320, Caption, 11, Muted, ("footer_art",))
        Self.Session.FooterActions[Action] = (X - 4, -335, X + Width + 4, -304)

    def ShowCoinHint(Self):
        """Briefly show a small muted glint beneath the tracked cup."""
        Cup = Self.Session.Cups[Self.Session.CorrectId]
        Canvas = Self.Session.Screen.getcanvas()
        Canvas.delete("coin_hint")
        Canvas.create_image(
            Cup.X - 4,
            58,
            anchor="nw",
            image=Self.Session.Assets["coin_hint"],
            tags=("coin_hint",),
        )
        Self.Session.HintFrames = 53

    def DrawAnswerTimer(Self):
        G = Self.Session
        Canvas = G.Screen.getcanvas()
        Canvas.delete("answer_timer")
        if G.State != "select" or not G.AnswerTotal:
            return
        Ratio = max(0, G.AnswerFrames / G.AnswerTotal)
        Color = "#ed8c9c" if Ratio <= 0.25 else "#f3c66c"
        Canvas.create_rectangle(
            -205, 156, 205, 165, fill="#141d27", width=0, tags=("answer_timer",)
        )
        if Ratio > 0:
            Canvas.create_rectangle(
                -205,
                156,
                -205 + 410 * Ratio,
                165,
                fill=Color,
                width=0,
                tags=("answer_timer",),
            )
        Text = f"Choose in {Math.ceil(G.AnswerFrames * FrameMs / 1000)}s"
        Self.CanvasLabel(
            -LabelWidth(Text, 10) / 2, 144, Text, 10, Color, ("answer_timer",)
        )

    def ShowStory(Self):
        Self.Session.State = "story"
        Self.Session.ClearCups()
        Self.DrawBackground()
        Self.Session.MenuText.clear()
        Self.Session.HudText.clear()
        Self.Session.Message.clear()
        Self.Session.Buttons = {}
        ChapterTitle, Setting, Speaker, Dialogue = Chapters[Self.Session.Level - 1]
        Frame(Self, -470, 174, 470, 236, "#141d27")
        Self.Write(
            Self.Session.MenuText,
            -440,
            197,
            f"Chapter {Self.Session.Level}",
            14,
            Gold,
            "left",
        )
        Self.Write(
            Self.Session.MenuText,
            440,
            197,
            LocationNames[Setting],
            14,
            White,
            "right",
        )
        TitleHalfWidth = LabelWidth(ChapterTitle, 24, True) / 2 + 26
        Frame(Self, -TitleHalfWidth, 110, TitleHalfWidth, 160, "#1b2430")
        Self.Write(
            Self.Session.MenuText,
            0,
            121,
            ChapterTitle,
            24,
            White,
        )
        for Index in range(10):
            Self.Rectangle(
                -173 + Index * 35,
                86,
                -149 + Index * 35,
                92,
                Gold if Index < Self.Session.Level - 1 else "#526071",
            )
        Self.Write(Self.Session.Message, -442, -220, Speaker, 16, Gold, "left")
        Self.WriteWrapped(
            Self.Session.Message,
            -442,
            -246,
            Dialogue,
            650,
            13,
            White,
        )
        Self.DrawButton(
            "story_next",
            "Play table",
            340,
            -260,
            202,
            True,
        )
        Self.DrawFooter()
        Self.Session.Screen.update()
