"""A pause overlay that freezes the current board and saves before leaving."""

import time as Time
from GameConfig import Colors
from PartyArt import Frame
from RunProgress import RunStates


class PauseMenu:
    def __init__(Self, Session):
        Self.Session = Session
        Self.PreviousButtons = {}

    def Open(Self):
        G = Self.Session
        if G.State == "paused" or G.State not in RunStates:
            return
        G.PausedState, G.State = G.State, "paused"
        Self.PreviousButtons = dict(G.Buttons)
        G.PlayTone("pause")
        Self.Draw()

    def Draw(Self, Error=""):
        G = Self.Session
        Canvas = G.Screen.getcanvas()
        Canvas.delete("pause_art")
        Canvas.create_rectangle(
            -500,
            -250,
            500,
            300,
            fill="#15121d",
            stipple="gray50",
            width=0,
            tags=("pause_art",),
        )
        G.ArtLayer = "pause_art"
        Frame(G.Views, -250, -198, 250, 174, "#211b2c")
        G.Views.CanvasLabel(-56, -126, "Paused", 24, Colors["gold"], ("pause_art",))
        G.Buttons = {}
        G.Views.DrawButton("settings", "Settings", 170, 126, 130)
        G.Views.DrawButton("resume", "Resume", 0, 58, 300, True)
        G.Views.DrawButton("restart", "Restart run", 0, 0, 300)
        G.Views.DrawButton("save_menu", "Save & Menu", 0, -58, 300)
        G.Views.DrawButton("save_exit", "Save & Exit", 0, -116, 300)
        if Error:
            G.Views.CanvasLabel(-205, 161, Error, 11, Colors["danger"], ("pause_art",))
        G.ArtLayer = "scene"
        G.Motion.Modal()
        G.Views.DrawFooter()

    def Resume(Self):
        G = Self.Session
        if G.State != "paused":
            return
        G.Screen.getcanvas().delete("pause_art")
        G.Buttons = Self.PreviousButtons
        G.State, G.PausedState = G.PausedState, None
        G.Views.DrawAnswerTimer()
        G.LastTick, G.FrameCredit = Time.monotonic(), 0.0
        G.Views.DrawFooter()

    def SaveAndLeave(Self, ExitApp=False):
        G = Self.Session
        if not G.Progress.Save():
            Self.Draw("Could not save. Your table is still paused.")
            return False
        Self.Resume()
        if ExitApp:
            G.Close()
        else:
            G.Views.ShowMenu()
        return True
