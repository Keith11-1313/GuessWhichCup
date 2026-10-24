"""Application setup and timer loop for Guess Which Cup.

Game owns session data and runtime resources. Explicit components handle
rendering, rounds, input and the cabinet without multiple inheritance.
"""

import time as Time
import tkinter as Tkinter
import turtle as Turtle
import uuid as Uuid
import sys as Sys
import ctypes as Ctypes
import CupCollection as Collection
from CollectionScreens import CupCabinet
from GameConfig import Colors, FrameMs, Height, SaveFile, Width
from GameObjects import Cup as CupSpriteClass, MakeWriter, Tone
from GameScreens import GameScreens
from InputControls import InputControls
from PartyArt import LoadAssets
from RoundLogic import RoundLogic
from ScoreStore import LoadScores
from GameTheme import LoadFont
from GameAudio import BackgroundMusic
from RunProgress import RunProgress, LoadRun
from PauseMenu import PauseMenu
from VisualEffects import VisualEffects
from GameSettings import GameSettings
from UiMotion import UiMotion
from GameViewport import GameViewport
from AmbientScene import AmbientScene
from SoundMixer import SoundMixer
from SkinAnimation import SkinAnimation

Bg = Colors["background"]
Muted = Colors["muted"]
Gold = Colors["gold"]


class Game:
    """Session and runtime with explicitly constructed behavior components."""

    def __init__(Self, RunLoop=True, ScorePath=None, ProfilePath=None, RunPath=None):
        LoadFont()
        if Sys.platform == "win32":
            # Give the source game its own taskbar identity instead of Python's.
            Ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "LanternHouse.GuessWhichCup"
            )
        Self.Screen = Turtle.Screen()
        Self.Screen.setup(Width, Height)
        Self.Screen.title("Guess Which Cup | Lantern House")
        Self.Screen.bgcolor(Bg)
        Self.Screen.tracer(0)
        Self.Assets = LoadAssets(Self.Screen)
        Self.Running = True
        Self.SoundEnabled = True
        Self.PausedState = None
        Self.LastTick = Time.monotonic()
        Self.FrameCredit = 0.0
        Root = Self.Screen.getcanvas().winfo_toplevel()
        Root.iconphoto(True, Self.Assets["app_icon"])
        Root.resizable(False, False)
        Root.protocol("WM_DELETE_WINDOW", Self.Close)

        Self.Static = MakeWriter()
        Self.Footer = MakeWriter()
        Self.MenuText = MakeWriter()
        Self.HudText = MakeWriter()
        Self.Message = MakeWriter()
        Self.Labels = MakeWriter(Muted)

        Self.Coin = Turtle.Turtle(visible=False)
        Self.Coin.speed(0)
        Self.Coin.penup()
        Self.Coin.shape("coin")
        Self.Coin.setheading(90)
        Self.Coin.color(Gold)

        # QA supplies temporary paths; normal play uses saves beside the game.
        Self.ScorePath = SaveFile if ScorePath is None else ScorePath
        Self.Scores = LoadScores(Self.ScorePath)
        Self.ProfilePath = (
            Collection.ProfileFile if ProfilePath is None else ProfilePath
        )
        Self.Profile = Collection.LoadProfile(Self.ProfilePath)
        Self.Progress = RunProgress(
            Self, RunPath or Self.ProfilePath.with_name("LanternRun.json")
        )
        Self.SavedRun = LoadRun(Self.Progress.FilePath)
        if (
            Self.SavedRun
            and Self.SavedRun["mode"] == "Endless"
            and not Self.Profile["story_completed"]
        ):
            Self.SavedRun = None
        Self.RunId = Uuid.uuid4().hex
        Self.IconSkin = None
        Self.SaveFailed = False
        Self.RewardFailed = False
        Self.PendingCup = None
        Self.DrawStatus = None
        Self.DrawFrame = 0
        Self.ArtLayer = "scene"
        Self.Mode = "Story"
        Self.Difficulty = "Normal"
        Self.Level = 1
        Self.Score = 0
        Self.Lives = 3

        # Endless combo and Story perfect tracking
        Self.Combo = 0
        Self.Perfect = True

        Self.State = "menu"
        Self.CupPool = [CupSpriteClass(I, 0) for I in range(6)]
        for Cup in Self.CupPool:
            Cup.Hide()
        Self.Cups = []
        Self.Slots = []
        Self.CorrectId = 0
        Self.RevealFrame = 0
        Self.RevealFrames = 0
        Self.Swaps = 0
        Self.SwapDuration = 30
        Self.CompletedSwaps = 0
        Self.SwapPair = None
        Self.SwapFrame = 0
        Self.Buttons = {}
        Self.FooterActions = {}
        Self.HintFrames = 0
        Self.AnswerFrames = Self.AnswerTotal = 0
        Self.DeathFrames = 0
        Self.LastChoice = None
        Self.StoryUnlockPending = False
        Self.Settings = GameSettings(
            Self, Self.ProfilePath.with_name("LanternSettings.json")
        )
        Self.Viewport = GameViewport(Self)
        Self.Ambient = AmbientScene(Self)
        Self.Motion = UiMotion(Self)
        Self.Effects = VisualEffects(Self)
        Self.SkinAnimation = SkinAnimation(Self)

        Self.Views = GameScreens(Self)
        Self.Rounds = RoundLogic(Self, Self.Views)
        Self.Cabinet = CupCabinet(Self, Self.Views)
        Self.Controls = InputControls(Self, Self.Views, Self.Rounds, Self.Cabinet)
        Self.PauseMenu = PauseMenu(Self)
        Self.Controls.BindControls()
        Self.Music = BackgroundMusic(Root)
        Self.Music.Volume = Self.Settings.Values["volume"]
        Self.SoundEnabled = (
            Self.Settings.Values["sound"] and Self.Settings.Values["master"] > 0
        )
        if not Self.SoundEnabled:
            Self.Settings.Values["master"] = 0
        Self.Mixer = SoundMixer(Self)
        Self.Mixer.Apply()
        Root.attributes("-fullscreen", Self.Settings.Values["fullscreen"])
        Self.AudioActive = RunLoop
        Self.Views.ShowMenu()
        Self.Screen.ontimer(Self.Update, FrameMs)
        if RunLoop:
            if Self.SoundEnabled:
                Self.Music.Start()
            Self.Screen.mainloop()

    def ClearCups(Self):
        Self.Screen.getcanvas().delete("answer_timer")
        Self.HintFrames = 0
        Self.Screen.getcanvas().delete("coin_hint")
        for Cup in Self.Cups:
            Cup.Hide()

        Self.Cups = []
        Self.Coin.hideturtle()
        Self.Labels.clear()

    def BestKey(Self):
        return f"{Self.Mode.lower()}_{Self.Difficulty.lower()}"

    def UpdateWindowIcon(Self):
        Skin = Self.Profile["equipped"]
        if Self.IconSkin != Skin:
            Self.WindowIcon = Self.Assets["skins"][Skin][0].zoom(2)
            Self.Screen.getcanvas().winfo_toplevel().iconphoto(True, Self.WindowIcon)
            Self.IconSkin = Skin

    def BestScore(Self):
        return int(Self.Scores.get(Self.BestKey(), 0))

    def PlayTone(Self, Kind):
        if Self.SoundEnabled:
            Self.Mixer.Play(Kind)

    def Close(Self):
        if not Self.Running:
            return
        Self.Running = False
        Self.Music.Stop()
        Self.Mixer.Stop()
        Self.Screen.bye()

    def Update(Self):
        if not Self.Running:
            return
        try:
            Now = Time.monotonic()
            # Use elapsed time so the difficulty does not depend on render speed.
            Self.FrameCredit += min(Now - Self.LastTick, 0.1) * 1000 / FrameMs
            Self.LastTick = Now
            Steps = int(Self.FrameCredit)
            Self.FrameCredit -= Steps
            for Ignored in range(Steps):
                Self.Ambient.Update()
                Self.SkinAnimation.Update()
                Self.Motion.Update()
                if Self.State not in ("paused", "settings"):
                    Self.Effects.Update()
                if Self.State == "reveal":
                    Self.RevealFrame += 1
                    if Self.Settings.Values["motion"]:
                        Cup = Self.Cups[Self.CorrectId]
                        Lift = min(
                            1,
                            Self.RevealFrame / 16,
                            max(0, Self.RevealFrames - Self.RevealFrame) / 12,
                        )
                        Cup.Y = 76 * Lift * Lift * (3 - 2 * Lift)
                        Cup.Render()
                    if Self.RevealFrame >= Self.RevealFrames:
                        Self.Rounds.BeginShuffle()
                elif Self.State == "shuffle":
                    Self.Rounds.AnimateSwap()
                elif Self.State == "gacha_opening":
                    Self.Cabinet.AnimateDraw()
                elif Self.State == "batch_reveal":
                    Self.Cabinet.AnimateBatch()
                elif Self.State == "last_reveal":
                    Self.DeathFrames += 1
                    if Self.DeathFrames >= 90:
                        Self.Views.ShowGameOver()
                elif Self.State == "select":
                    if Self.HintFrames:
                        Self.HintFrames -= 1
                        if Self.HintFrames == 0:
                            Self.Screen.getcanvas().delete("coin_hint")
                    if Self.AnswerFrames > 0:
                        Self.AnswerFrames -= 1
                        Self.Views.DrawAnswerTimer()
                        if Self.AnswerFrames == 0:
                            Self.Rounds.Timeout()
            Self.Screen.update()
            if Self.Running:
                Self.Screen.ontimer(Self.Update, FrameMs)
        except Turtle.Terminator:
            Self.Running = False
        except Tkinter.TclError:
            # Closing can cancel Tk work. Other Tk errors must remain debuggable.
            if Self.Running:
                raise


if __name__ == "__main__":
    Game()
