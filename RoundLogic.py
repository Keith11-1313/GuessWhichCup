"""Round setup, shuffle animation, scoring and save operations."""

import math as Math
import random as Random
import uuid as Uuid
import time as Time
import CupCollection as Collection
from GameConfig import (
    Colors,
    Difficulties,
    StoryLevels,
    FrameMs,
    LevelSettings,
    AnswerSeconds,
)
from ScoreStore import SaveScore

Gold = Colors["gold"]


class RoundLogic:

    def __init__(Self, Session, Views):
        Self.Session = Session
        Self.Views = Views

    def SaveHighScore(Self):
        if Self.Session.Score > Self.Session.BestScore():
            Self.Session.SaveFailed = not SaveScore(
                Self.Session.ScorePath,
                Self.Session.Scores,
                Self.Session.BestKey(),
                Self.Session.Score,
            )

    def StartGame(Self):
        if Self.Session.Mode == "Endless" and not Self.Session.Profile.get(
            "story_completed", False
        ):
            Self.Session.Mode = "Story"
        Self.Session.StoryUnlockPending = False
        Self.Session.Progress.Clear()
        Self.Session.RunId = Uuid.uuid4().hex
        Self.Session.SaveFailed = False
        Self.Session.RewardFailed = False
        Self.Session.Score = 0
        Self.Session.Level = 1
        Self.Session.Lives = Difficulties[Self.Session.Difficulty]["lives"]

        # Reset combo/perfect for a new game
        Self.Session.Combo = 0
        Self.Session.Perfect = True

        Self.BeginChapter()

    def SelectionHint(Self):
        return f"Click a cup or press 1-{len(Self.Session.Cups)}."

    def StartLevel(Self, Refresh=True):
        Self.Session.State = "reveal"
        Self.Session.LastChoice = None
        Self.Session.ClearCups()
        Self.Session.SkinAnimation.BeginRound()
        Self.Views.DrawBackground()
        Self.Session.MenuText.clear()
        Self.Session.Buttons = {}
        Self.Views.DrawHud()

        (
            Count,
            Self.Session.Swaps,
            Self.Session.SwapDuration,
            Self.Session.RevealFrames,
        ) = LevelSettings(
            Self.Session.Level, Self.Session.Difficulty, Self.Session.Mode
        )

        Spacing = min(150, 760 / max(1, Count - 1))
        Self.Session.Slots = [(I - (Count - 1) / 2) * Spacing for I in range(Count)]

        Self.Session.Cups = Self.Session.CupPool[:Count]
        # cid stays with the cup; slot is its current numbered table position.
        for I, Cup in enumerate(Self.Session.Cups):
            Cup.Reset(I, Self.Session.Slots[I], Self.Session.Profile["equipped"])

        Self.Session.ArtLayer = "choice_art"
        for I, X in enumerate(Self.Session.Slots):
            Self.Views.Rectangle(X - 15, -124, X + 15, -96, "#312331")
            Self.Views.Write(Self.Session.Labels, X, -119, str(I + 1), 14, Gold)
        Self.Session.ArtLayer = "scene"

        Self.Session.CorrectId = Random.randrange(Count)
        Self.Session.RevealFrame = 0
        Self.Session.CompletedSwaps = 0
        Self.Session.SwapPair = None
        Self.Session.AnswerFrames = Self.Session.AnswerTotal = 0
        Self.Session.LastTick = Time.monotonic()
        Self.Session.FrameCredit = 0.0

        Special = Self.Session.Cups[Self.Session.CorrectId]
        Special.Y = 0 if Self.Session.Settings.Values["motion"] else 76
        Special.Render()

        Self.Session.Coin.goto(Special.X, -40)
        Self.Session.Coin.showturtle()

        Self.Views.SetMessage("Remember the coin", "Watch which cup holds it.")

        if Refresh:
            Self.Session.PlayTone("reveal")
        Self.Session.Screen.listen()
        if Refresh:
            Self.Session.Screen.update()

    def BeginShuffle(Self):
        Self.Session.State = "shuffle"
        Self.Session.Coin.hideturtle()

        for Cup in Self.Session.Cups:
            Cup.Y = 0
            Cup.Render()

        Self.Views.SetMessage("Follow the cup", "")

    def AnimateSwap(Self):
        if Self.Session.SwapPair is None:
            if Self.Session.CompletedSwaps >= Self.Session.Swaps:
                Self.Session.State = "select"
                Self.Session.AnswerTotal = round(
                    AnswerSeconds(
                        Self.Session.Level, Self.Session.Difficulty, Self.Session.Mode
                    )
                    * 1000
                    / FrameMs
                )
                Self.Session.AnswerFrames = Self.Session.AnswerTotal
                Self.Views.SetMessage("Where is the coin?", Self.SelectionHint())
                Self.Views.DrawAnswerTimer()
                if Self.Session.Mode == "Endless" and Self.Session.Level > 10:
                    Self.Views.ShowCoinHint()
                return

            A, B = Random.sample(Self.Session.Cups, 2)
            Self.Session.SwapPair = (A, B, A.Slot, B.Slot)
            Self.Session.SwapFrame = 0

        A, B, SlotA, SlotB = Self.Session.SwapPair
        Self.Session.SwapFrame += 1

        T = min(1.0, Self.Session.SwapFrame / Self.Session.SwapDuration)
        Eased = T * T * (3 - 2 * T)

        A.X = (
            Self.Session.Slots[SlotA]
            + (Self.Session.Slots[SlotB] - Self.Session.Slots[SlotA]) * Eased
        )

        B.X = (
            Self.Session.Slots[SlotB]
            + (Self.Session.Slots[SlotA] - Self.Session.Slots[SlotB]) * Eased
        )

        Arc = Math.sin(Math.pi * T) * 37
        A.Y = Arc
        B.Y = -Arc

        A.Render()
        B.Render()

        if T >= 1:
            A.Slot, B.Slot = SlotB, SlotA
            A.X, B.X = Self.Session.Slots[A.Slot], Self.Session.Slots[B.Slot]
            A.Y = B.Y = 0

            A.Render()
            B.Render()

            Self.Session.CompletedSwaps += 1
            Self.Session.SwapPair = None

    def Choose(Self, Slot):
        """Resolve one valid choice; ignore input outside the selection phase."""
        if Self.Session.State != "select":
            return
        Selected = next((Cup for Cup in Self.Session.Cups if Cup.Slot == Slot), None)
        if Selected is None:
            return

        # Lock input before rendering so a second click cannot score twice.
        Self.Session.State = "resolving"
        Self.Session.LastChoice = Selected.Slot
        Self.Session.Screen.getcanvas().delete("answer_timer")
        Self.Session.HintFrames = 0
        Self.Session.Screen.getcanvas().delete("coin_hint")
        Correct = Self.Session.Cups[Self.Session.CorrectId]
        Selected.Y = 76
        Selected.Render()
        Correct.Y = 76
        Correct.Render()
        Self.Session.Motion.Lift(
            [Selected] if Selected is Correct else [Selected, Correct]
        )
        Self.Session.Coin.goto(Correct.X, -40)
        Self.Session.Coin.showturtle()

        if Selected is Correct:
            Self.ResolveCorrectGuess()
        else:
            Self.ResolveWrongGuess()

    def Timeout(Self):
        G = Self.Session
        if G.State != "select":
            return
        G.State = "resolving"
        G.LastChoice = None
        G.Screen.getcanvas().delete("answer_timer")
        G.Screen.getcanvas().delete("coin_hint")
        G.HintFrames = 0
        Correct = G.Cups[G.CorrectId]
        Correct.Y = 76
        Correct.Render()
        G.Motion.Lift([Correct])
        G.Coin.goto(Correct.X, -40)
        G.Coin.showturtle()
        Self.ResolveWrongGuess(TimedOut=True)

    def ResolveCorrectGuess(Self):
        Self.Session.Motion.Feedback(True)
        """Award points and one eligible ticket, then show the next action."""
        Points = Self.Session.Level * 100 + (Self.Session.Lives - 1) * 20
        if Self.Session.Mode == "Endless":
            Self.Session.Combo += 1
            Points += Self.Session.Combo * 25

        RewardKey = None
        if Self.Session.Mode == "Story":
            RewardKey = f"{Self.Session.Difficulty}:{Self.Session.Level}"
        else:
            RewardKey = f"Endless:{Self.Session.RunId}:{Self.Session.Level}"
        Earned = Collection.Reward(
            Self.Session.ProfilePath, Self.Session.Profile, RewardKey
        )
        Self.Session.RewardFailed = Earned == -1
        EarnedText = " and 1 ticket" if Earned == 1 else ""

        Self.Session.Score += Points
        Self.SaveHighScore()
        Self.Views.DrawHud()
        Self.Session.PlayTone("correct")
        if Self.Session.Mode == "Story" and Self.Session.Level >= StoryLevels:
            Self.FinishStory()
        else:
            Self.Session.State = "result"
            Self.Views.SetMessage("Found it", f"+{Points} points{EarnedText}")
        Bonus = 1000 if Self.Session.State == "victory" and Self.Session.Perfect else 0
        Self.Session.Effects.Award(Points + Bonus, Earned == 1)

    def FinishStory(Self):
        """Complete the narrative and apply the perfect-run bonus once."""
        Self.Session.State = "victory"
        Self.Session.StoryUnlockPending = not Collection.CompleteStory(
            Self.Session.ProfilePath, Self.Session.Profile, Self.Session.Difficulty
        )
        Self.Session.RewardFailed = Self.Session.StoryUnlockPending
        if not Self.Session.StoryUnlockPending:
            Self.Session.Progress.Clear()
            Self.Session.UpdateWindowIcon()
        if Self.Session.Perfect:
            Self.Session.Score += 1000
            Self.SaveHighScore()
            Self.Views.SetMessage(
                (
                    "Story complete"
                    if Self.Session.StoryUnlockPending
                    else "Brass Keepsake earned"
                ),
                "Endless and Cup cabinet unlocked. Mira: You earned this cup.",
                Gold,
            )
            Self.Views.DrawHud()
            Self.Views.Write(
                Self.Session.Message,
                -442,
                -279,
                "+1,000 perfect bonus",
                10,
                Gold,
                "left",
            )
        else:
            Self.Views.SetMessage(
                (
                    "Story complete"
                    if Self.Session.StoryUnlockPending
                    else "Brass Keepsake earned"
                ),
                "Endless and Cup cabinet unlocked. Your new cup is equipped.",
            )
        Self.Session.PlayTone("win")

    def RetryStoryUnlock(Self):
        G = Self.Session
        if Collection.CompleteStory(G.ProfilePath, G.Profile, G.Difficulty):
            G.StoryUnlockPending = G.RewardFailed = False
            G.Progress.Clear()
            G.UpdateWindowIcon()
            Self.Views.SetMessage(
                "Brass Keepsake earned",
                "Endless and Cup cabinet unlocked. Your new cup is equipped.",
            )

    def ResolveWrongGuess(Self, TimedOut=False):
        Self.Session.Motion.Feedback(False)
        """Lose a life and either offer a retry or end the run."""
        Self.Session.Lives -= 1
        if Self.Session.Mode == "Endless":
            Self.Session.Combo = 0
        else:
            Self.Session.Perfect = False
        Self.Views.DrawHud()
        Self.Session.PlayTone("wrong")
        if Self.Session.Lives > 0:
            Self.Session.State = "retry"
            Self.Views.SetMessage(
                "Time's up" if TimedOut else "Not this cup",
                f"{Self.Session.Lives} lives left. Try this table again.",
            )
        else:
            Self.Session.Progress.Clear()
            Self.Session.State = "last_reveal"
            Self.Session.DeathFrames = 0
            Correct = Self.Session.Cups[Self.Session.CorrectId]
            Detail = f"The coin was under cup {Correct.Slot+1}."
            if Self.Session.LastChoice is not None:
                Detail = f"You opened cup {Self.Session.LastChoice+1}. " + Detail
            Self.Views.SetMessage("Time's up" if TimedOut else "One last look", Detail)

    def BeginChapter(Self):
        if Self.Session.Mode == "Story":
            Self.Views.ShowStory()
        else:
            Self.StartLevel()
