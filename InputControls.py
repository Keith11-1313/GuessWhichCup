"""Keyboard binding, click hitboxes and state-dependent navigation."""

from NamingCompatibility import WriteAttribute

import sys as Sys
from GameConfig import Difficulties, ResultButtonBounds
import CupCollection as Collection
from RunProgress import RunStates


def PointInRectangle(X, Y, Bounds):
    X1, Y1, X2, Y2 = Bounds
    return X1 <= X <= X2 and Y1 <= Y <= Y2


class InputControls:
    """Route input through explicit view, round and cabinet dependencies."""

    def __init__(Self, Session, Views, Rounds, Cabinet):
        Self.Session = Session
        Self.Views = Views
        Self.Rounds = Rounds
        Self.Cabinet = Cabinet
        Self.ActiveSlider = None

    def DragSetting(Self, X, Y):
        if Self.Session.State != "settings" or Self.ActiveSlider is None:
            return
        Self.Session.Settings.Slider(Self.ActiveSlider, X)

    def ButtonAt(Self, X, Y):
        """Find the first visible button whose bounds contain the click."""
        for Name, Bounds in list(Self.Session.Buttons.items()):
            if PointInRectangle(X, Y, Bounds):
                Self.Session.PlayTone("click")
                return Name
        return None

    def OnClick(Self, X, Y):
        """Route a click according to the current screen or round phase."""
        for Action, Bounds in Self.Session.FooterActions.items():
            if PointInRectangle(X, Y, Bounds):
                Handlers = {
                    "advance": Self.Advance,
                    "help": Self.Views.ShowHowToPlay,
                    "escape": Self.Escape,
                    "menu": Self.RequestMenu,
                    "pause": Self.TogglePause,
                    "sound": Self.ToggleSound,
                    "settings": Self.Session.Settings.Open,
                }
                Handlers[Action]()
                return
        if Self.Session.State == "settings":
            Button = Self.ButtonAt(X, Y)
            if Button and Button.startswith("slider:"):
                Self.ActiveSlider = Button.split(":", 1)[1]
                Self.Session.Settings.Slider(Self.ActiveSlider, X)
            elif Button and Button.startswith("setting:"):
                Self.Session.Settings.Action(Button.split(":", 1)[1])
            return
        if Self.Session.State == "paused":
            Button = Self.ButtonAt(X, Y)
            if Button == "resume":
                Self.Session.PauseMenu.Resume()
            elif Button == "restart":
                Self.Restart()
            elif Button == "settings":
                Self.Session.Settings.Open()
            elif Button in ("save_menu", "save_exit"):
                Self.Session.PauseMenu.SaveAndLeave(ExitApp=Button == "save_exit")
            return
        if Self.Session.State == "select":
            for Cup in Self.Session.Cups:
                if Cup.Contains(X, Y):
                    Self.Rounds.Choose(Cup.Slot)
                    return
        elif Self.Session.State == "over":
            Button = Self.ButtonAt(X, Y)
            if Button == "play_again":
                Self.Advance()
            elif Button == "game_menu":
                Self.Views.ShowMenu()
        elif Self.Session.State in ("result", "retry", "victory"):
            if PointInRectangle(X, Y, ResultButtonBounds):
                Self.Advance()
        else:
            Button = Self.ButtonAt(X, Y)
            if Button is None:
                return
            if Self.Session.State in ("menu", "menu_setup"):
                Self.MenuAction(Button)
            elif Self.Session.State in (
                "story",
                "cabinet",
                "odds",
                "gacha_reveal",
                "batch_reveal",
            ):
                Self.CollectionAction(Button)
            elif Self.Session.State == "how_to_play" and Button == "back":
                Self.Views.ShowMenu()

    def MenuAction(Self, Button):
        """Apply one menu choice and redraw only when its setting changes."""
        Setup = Self.Session.State == "menu_setup"
        if Button == "new_game_setup":
            Self.Views.ShowMenu(NewGame=True)
        elif Button == "back_saved":
            Self.Views.ShowMenu()
        elif Button.startswith("mode:"):
            if Button == "mode:Endless" and not Self.Session.Profile.get(
                "story_completed", False
            ):
                return
            Self.Session.Mode = Button.split(":", 1)[1]
            Self.Views.ShowMenu(NewGame=Setup)
        elif Button.startswith("diff:"):
            Self.Session.Difficulty = Button.split(":", 1)[1]
            Self.Views.ShowMenu(NewGame=Setup)
        elif Button == "start":
            Self.Rounds.StartGame()
        elif Button == "resume_run":
            if not Self.Session.Progress.Restore():
                Self.Views.ShowMenu()
        elif Button == "cabinet":
            Self.Cabinet.ShowCabinet()
        elif Button == "settings":
            Self.Session.Settings.Open()
        elif Button == "quit":
            Self.Session.Close()
        elif Button == "howto":
            Self.Views.ShowHowToPlay()

    def OpenCabinetFromMenu(Self):
        if Self.Session.State == "menu":
            Self.Cabinet.ShowCabinet()

    def Advance(Self):
        if Self.Session.State == "last_reveal":
            if Self.Session.DeathFrames >= 30:
                Self.Views.ShowGameOver()
            return
        if Self.Session.State == "paused":
            Self.Session.PauseMenu.Resume()
            return
        if Self.Session.State == "menu_setup":
            Self.Rounds.StartGame()
        elif Self.Session.State == "menu":
            if Self.Session.SavedRun:
                if not Self.Session.Progress.Restore():
                    Self.Views.ShowMenu()
            else:
                Self.Rounds.StartGame()

        elif Self.Session.State == "how_to_play":
            Self.Views.ShowMenu()

        elif Self.Session.State == "story":
            Self.Rounds.StartLevel()

        elif Self.Session.State == "gacha_reveal":
            if Self.Cabinet.DuplicatePending:
                Self.Cabinet.ConvertDuplicate()
            else:
                Self.Cabinet.ShowCabinet()

        elif Self.Session.State == "gacha_opening":
            Self.Cabinet.RevealDraw()
        elif Self.Session.State == "batch_reveal":
            Self.Cabinet.NextBatch()

        elif Self.Session.State == "cabinet":
            Self.Cabinet.DrawCup()

        elif Self.Session.State in ("over", "victory"):
            if Self.Session.State == "victory" and Self.Session.StoryUnlockPending:
                Self.Rounds.RetryStoryUnlock()
            elif Self.Session.State == "victory":
                Self.Cabinet.ShowCabinet()
            else:
                Self.Rounds.StartGame()

        elif Self.Session.State == "result":
            Self.Session.Level += 1
            Self.Rounds.BeginChapter()

        elif Self.Session.State == "retry":
            Self.Rounds.StartLevel()

    def Restart(Self):
        if Self.Session.State == "victory" and Self.Session.StoryUnlockPending:
            Self.Rounds.RetryStoryUnlock()
            if Self.Session.StoryUnlockPending:
                return
        if Self.Session.State in ("settings", "last_reveal"):
            return
        if Self.Session.State == "paused":
            Self.Session.PauseMenu.Resume()
        Self.Rounds.StartGame()

    def RequestHelp(Self):
        if Self.Session.State in ("settings", "last_reveal"):
            return
        if Self.Session.State in RunStates or Self.Session.State == "paused":
            Self.Session.PauseMenu.Open()
        else:
            Self.Views.ShowHowToPlay()

    def ToggleSound(Self):
        Self.Session.SoundEnabled = not Self.Session.SoundEnabled
        Settings = Self.Session.Settings
        if Self.Session.SoundEnabled:
            Settings.Values["master"] = Settings.LastMaster
        else:
            Settings.LastMaster = Settings.Values["master"] or Settings.LastMaster
            Settings.Values["master"] = 0
        Self.Session.Mixer.Apply()
        if Self.Session.SoundEnabled and Self.Session.AudioActive:
            Self.Session.Music.Start()
        else:
            Self.Session.Music.Stop()
            Self.Session.Mixer.Stop()
            if Sys.platform == "win32":
                import winsound as Winsound

                Winsound.PlaySound(None, 0)
        Self.Session.Screen.title(
            "Guess Which Cup | Lantern House | Sound "
            + ("on" if Self.Session.SoundEnabled else "off")
        )
        Self.Views.DrawFooter()
        Self.Session.Settings.Save()
        if Self.Session.State == "settings":
            Self.Session.Settings.Draw()

    def CycleMode(Self):
        if not Self.Session.Profile.get("story_completed", False):
            return
        if Self.Session.State == "menu" and Self.Session.SavedRun:
            return
        if Self.Session.State in ("menu", "menu_setup"):
            Setup = Self.Session.State == "menu_setup"
            Self.Session.Mode = "Endless" if Self.Session.Mode == "Story" else "Story"
            Self.Views.ShowMenu(NewGame=Setup)

    def AdjustMusicVolume(Self, Step):
        Self.Session.Music.SetVolume(Self.Session.Music.Volume + Step)
        Self.Views.DrawFooter()
        Self.Session.Settings.Save()
        if Self.Session.State == "settings":
            Self.Session.Settings.Draw()

    def CycleDifficulty(Self, Direction=1):
        if Self.Session.State == "menu" and Self.Session.SavedRun:
            return
        if Self.Session.State in ("menu", "menu_setup"):
            Setup = Self.Session.State == "menu_setup"
            Names = list(Difficulties)
            Self.Session.Difficulty = Names[
                (Names.index(Self.Session.Difficulty) + Direction) % len(Names)
            ]
            Self.Views.ShowMenu(NewGame=Setup)

    def RequestMenu(Self):
        if Self.Session.State == "victory" and Self.Session.StoryUnlockPending:
            Self.Rounds.RetryStoryUnlock()
            if Self.Session.StoryUnlockPending:
                return
        if Self.Session.State == "last_reveal":
            return
        if Self.Session.State == "settings":
            Self.Session.Settings.Close()
            return
        if Self.Session.State in RunStates or Self.Session.State == "paused":
            Self.Session.PauseMenu.Open()
        else:
            Self.Views.ShowMenu()

    def TogglePause(Self):
        if Self.Session.State == "paused":
            Self.Session.PauseMenu.Resume()
        else:
            Self.Session.PauseMenu.Open()

    def Escape(Self):
        if Self.Session.State == "victory" and Self.Session.StoryUnlockPending:
            Self.RequestMenu()
            return
        if Self.Session.State == "last_reveal":
            return
        if Self.Session.State == "settings":
            Self.Session.Settings.Close()
        elif Self.Session.State == "paused":
            Self.Session.PauseMenu.Resume()
        elif Self.Session.State in RunStates:
            Self.Session.PauseMenu.Open()
        elif Self.Session.State == "menu":
            Self.Session.Close()
        elif Self.Session.State in ("odds", "gacha_reveal", "gacha_opening"):
            Self.Cabinet.ShowCabinet()
        else:
            Self.Views.ShowMenu()

    def BindControls(Self):
        Self.Session.Screen.onclick(Self.OnClick)
        Self.Session.Screen.listen()
        from GameObjects import InputCanvas

        Canvas = InputCanvas(Self.Session.Screen)
        Canvas.bind(
            "<B1-Motion>",
            lambda Event: Self.DragSetting(
                Canvas.canvasx(Event.x), -Canvas.canvasy(Event.y)
            ),
            add="+",
        )
        Canvas.bind(
            "<ButtonRelease-1>",
            lambda Event: WriteAttribute(Self, "active_slider", None),
            add="+",
        )
        Canvas.bind(
            "<Motion>",
            lambda Event: Self.Session.Motion.Pointer(
                Canvas.canvasx(Event.x), -Canvas.canvasy(Event.y)
            ),
            add="+",
        )
        Self.Session.Screen.onkeypress(Self.Session.Settings.Open, "o")
        Self.Session.Screen.onkeypress(Self.Session.Settings.Open, "O")
        Self.Session.Screen.onkeypress(Self.Session.Settings.Fullscreen, "F11")

        for Key in ("Return", "space"):
            Self.Session.Screen.onkeypress(Self.Advance, Key)

        for Key in ("m", "M"):
            Self.Session.Screen.onkeypress(Self.RequestMenu, Key)

        for Key in ("h", "H"):
            Self.Session.Screen.onkeypress(Self.RequestHelp, Key)

        for Key in ("r", "R"):
            Self.Session.Screen.onkeypress(Self.Restart, Key)

        for N in range(1, 7):
            Self.Session.Screen.onkeypress(
                lambda Number=N: Self.Rounds.Choose(Number - 1), str(N)
            )

        Self.Session.Screen.onkeypress(Self.Escape, "Escape")
        Self.Session.Screen.onkeypress(Self.TogglePause, "p")
        Self.Session.Screen.onkeypress(Self.ToggleSound, "s")
        Self.Session.Screen.onkeypress(Self.TogglePause, "P")
        Self.Session.Screen.onkeypress(Self.ToggleSound, "S")
        Self.Session.Screen.onkeypress(lambda: Self.AdjustMusicVolume(-5), "minus")
        Self.Session.Screen.onkeypress(lambda: Self.AdjustMusicVolume(5), "equal")
        for Key in ("c", "C"):
            Self.Session.Screen.onkeypress(Self.OpenCabinetFromMenu, Key)
        Self.Session.Screen.onkeypress(Self.CycleMode, "Tab")
        Self.Session.Screen.onkeypress(lambda: Self.CycleDifficulty(-1), "Left")
        Self.Session.Screen.onkeypress(Self.CycleDifficulty, "Right")

    def CollectionAction(Self, Key):
        if Key == "convert_duplicate":
            Self.Cabinet.ConvertDuplicate()
        elif Key == "story_next":
            Self.Advance()
        elif Key == "draw":
            Self.Cabinet.DrawCup()
        elif Key == "draw10":
            Self.Cabinet.DrawCup(10)
        elif Key == "batch_next":
            Self.Cabinet.NextBatch()
        elif Key.startswith("page:"):
            Self.Cabinet.Page += 1 if Key.endswith("next") else -1
            Self.Cabinet.ShowCabinet()
        elif Key == "odds":
            Self.Cabinet.ShowOdds()
        elif Key == "back":
            Self.Views.ShowMenu()
        elif Key == "cabinet":
            Self.Cabinet.ShowCabinet()
        elif Key.startswith("equip:"):
            Skin = Key.split(":", 1)[1]
            if Collection.Equip(Self.Session.ProfilePath, Self.Session.Profile, Skin):
                Self.Session.PlayTone("equip")
                Self.Session.UpdateWindowIcon()
                Self.Cabinet.Page = next(
                    (I // 6 for I, Cup in enumerate(Collection.Cups) if Cup[0] == Skin),
                    0,
                )
                Self.Cabinet.ShowCabinet("Cup equipped.")
            else:
                Self.Cabinet.ShowCabinet("Could not save. Try again.")
