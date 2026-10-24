"""Validated local preferences and an overlay that preserves the current board."""

from NamingCompatibility import MigrateSave
import json as Json
from CupCollection import Persist
from GameConfig import Colors
from PartyArt import Frame, PlaceImage

Defaults = dict(
    master=80, volume=20, effects=70, sound=True, fullscreen=False, motion=True
)


class GameSettings:
    def __init__(Self, Session, FilePath):
        if FilePath.name == "LanternSettings.json":
            FilePath = MigrateSave(FilePath, "lantern_settings.json")
        Self.Session, Self.FilePath = Session, FilePath
        Self.Values = dict(Defaults)
        Self.Previous = "menu"
        Self.PreviousButtons = {}
        Self.Tab = "audio"
        Self.Error = ""
        try:
            Saved = Json.loads(FilePath.read_text(encoding="utf-8"))
            for Key, Default in Defaults.items():
                Value = Saved.get(Key)
                if type(Value) is type(Default) and (
                    Key not in ("master", "volume", "effects") or 0 <= Value <= 100
                ):
                    Self.Values[Key] = Value
        except (OSError, ValueError, AttributeError):
            pass
        Self.LastMaster = Self.Values["master"] or 80

    def Save(Self):
        G = Self.Session
        Self.Values.update(volume=G.Music.Volume, sound=G.SoundEnabled)
        Self.Error = (
            "" if Persist(Self.FilePath, Self.Values) else "Could not save settings."
        )

    def Fullscreen(Self):
        Self.Values["fullscreen"] = not Self.Values["fullscreen"]
        Self.Session.Screen.getcanvas().winfo_toplevel().attributes(
            "-fullscreen", Self.Values["fullscreen"]
        )
        Self.Save()
        Self.Session.Screen.getcanvas().winfo_toplevel().after(
            100, Self.Session.Viewport.Resize
        )
        if Self.Session.State == "settings":
            Self.Draw()

    def Open(Self):
        G = Self.Session
        if G.State in ("settings", "last_reveal"):
            return
        if G.State in ("story", "reveal", "shuffle", "select", "result", "retry"):
            G.PauseMenu.Open()
        Self.Previous = G.State
        Self.PreviousButtons = dict(G.Buttons)
        G.State = "settings"
        Self.Draw(Animate=True)

    def Draw(Self, Animate=False):
        G = Self.Session
        Canvas = G.Screen.getcanvas()
        Canvas.delete("pause_art")
        Canvas.create_rectangle(
            -500,
            -270,
            500,
            300,
            fill="#101820",
            stipple="gray50",
            width=0,
            tags=("pause_art",),
        )
        G.ArtLayer = "pause_art"
        Frame(G.Views, -410, -238, 410, 238, "#1b2430")
        PlaceImage(G.Views, G.Assets["icons"]["settings"], -366, 204)
        G.Views.CanvasLabel(-328, -192, "Settings", 26, Colors["gold"], ("pause_art",))
        G.Buttons = {}
        for X, Tab, Title in ((-145, "audio", "Audio"), (145, "display", "Display")):
            G.Views.DrawButton(
                "setting:tab_" + Tab, Title, X, 126, 250, Self.Tab == Tab
            )
        if Self.Tab == "audio":
            for Y, Key, Title in (
                (58, "master", "Master"),
                (-8, "volume", "Music"),
                (-74, "effects", "Game sounds"),
            ):
                Value = G.Music.Volume if Key == "volume" else Self.Values[Key]
                Icon = {"master": "audio", "volume": "music", "effects": "effects"}[Key]
                PlaceImage(G.Views, G.Assets["icons"][Icon], -366, Y + 12)
                G.Views.CanvasLabel(
                    -330, -Y, Title, 14, Colors["white"], ("pause_art",)
                )
                G.Views.DrawButton("setting:" + Key + "_down", "-", -106, Y, 48)
                Canvas.create_rectangle(
                    -62,
                    -Y - 4,
                    222,
                    -Y + 4,
                    fill="#101820",
                    width=0,
                    tags=("pause_art",),
                )
                Canvas.create_rectangle(
                    -62,
                    -Y - 4,
                    -62 + 284 * Value / 100,
                    -Y + 4,
                    fill=Colors["gold"],
                    width=0,
                    tags=("pause_art",),
                )
                Canvas.create_rectangle(
                    -66 + 284 * Value / 100,
                    -Y - 11,
                    -58 + 284 * Value / 100,
                    -Y + 11,
                    fill=Colors["white"],
                    width=0,
                    tags=("pause_art",),
                )
                G.Buttons["slider:" + Key] = (-70, Y - 22, 230, Y + 22)
                G.Views.CanvasLabel(
                    240, -Y, f"{Value}%", 12, Colors["white"], ("pause_art",)
                )
                G.Views.DrawButton("setting:" + Key + "_up", "+", 342, Y, 48)
        elif Self.Tab == "display":
            for Y, Title, Key in (
                (52, "Full screen", "fullscreen"),
                (-24, "Background & UI motion", "motion"),
            ):
                G.Views.CanvasLabel(
                    -366, -Y, Title, 14, Colors["white"], ("pause_art",)
                )
                G.Views.DrawButton(
                    "setting:" + Key,
                    "On" if Self.Values[Key] else "Off",
                    240,
                    Y,
                    220,
                    Self.Values[Key],
                )
        G.Views.DrawButton("setting:back", "Done", 0, -177, 280, True)
        if Self.Error:
            G.Views.CanvasLabel(
                -366, 216, Self.Error, 10, Colors["danger"], ("pause_art",)
            )
        G.ArtLayer = "scene"
        if Animate:
            G.Motion.Modal()
        else:
            G.Motion.ModalStep = 16
            G.Motion.ModalOffset = 0
        G.Views.DrawFooter()

    def SetLevel(Self, Key, Value):
        Value = max(0, min(100, round(Value)))
        if Key == "master" and not Value and Self.Values["master"]:
            Self.LastMaster = Self.Values["master"]
        if Key == "volume":
            Self.Session.Music.SetVolume(Value)
        else:
            Self.Values[Key] = Value
        Self.Session.Mixer.Apply()
        if Key == "master":
            Self.Session.SoundEnabled = Value > 0
            if Value and Self.Session.AudioActive:
                Self.Session.Music.Start()
            elif not Value:
                Self.Session.Music.Stop()
                Self.Session.Mixer.Stop()
        Self.Save()
        Self.Draw()

    def Slider(Self, Key, X):
        Self.SetLevel(Key, (X + 62) / 284 * 100)

    def Action(Self, Key):
        G = Self.Session
        if Key == "back":
            Self.Close()
            return
        if Key.startswith("tab_"):
            Self.Tab = Key[4:]
        elif Key == "fullscreen":
            Self.Fullscreen()
        elif Key == "motion":
            Self.Values[Key] = not Self.Values[Key]
        elif Key == "sound":
            G.Controls.ToggleSound()
        elif Key.endswith(("_up", "_down")):
            Level, Direction = Key.rsplit("_", 1)
            Value = G.Music.Volume if Level == "volume" else Self.Values[Level]
            Self.SetLevel(Level, Value + (5 if Direction == "up" else -5))
            return
        Self.Save()
        Self.Draw()

    def Close(Self):
        G = Self.Session
        G.Screen.getcanvas().delete("pause_art")
        G.State = Self.Previous
        G.Buttons = Self.PreviousButtons
        if G.State == "paused":
            G.PauseMenu.Draw()
        else:
            G.Views.DrawFooter()
