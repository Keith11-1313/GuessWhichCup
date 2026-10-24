"""Validated, atomic checkpoints for a paused run, separate from cup ownership."""

from NamingCompatibility import ReadAttribute, WriteAttribute

from NamingCompatibility import MigrateSave
import json as Json
import math as Math
import time as Time
import uuid as Uuid
from GameConfig import Difficulties, LevelSettings
from CupCollection import Persist

RunStates = ("story", "reveal", "shuffle", "select", "result", "retry")
Counters = (
    "reveal_frame",
    "reveal_frames",
    "swaps",
    "swap_duration",
    "completed_swaps",
    "swap_frame",
    "correct_id",
    "hint_frames",
)


def LoadRun(FilePath):
    if FilePath.name == "LanternRun.json":
        FilePath = MigrateSave(FilePath, "lantern_run.json")
    """Reject damaged checkpoints rather than partially restoring a board."""
    try:
        Data = Json.loads(FilePath.read_text(encoding="utf-8"))
        if not isinstance(Data, dict) or Data.get("version") != 1:
            return None
        if Data.get("state") not in RunStates or Data.get("mode") not in (
            "Story",
            "Endless",
        ):
            return None
        if Data.get("difficulty") not in Difficulties:
            return None
        for Key in ("level", "score", "lives", "combo") + Counters:
            if type(Data.get(Key)) is not int or not 0 <= Data[Key] <= 10**12:
                return None
        if not 1 <= Data["level"] <= 100000 or not 1 <= Data["lives"] <= 5:
            return None
        if Data["mode"] == "Story" and Data["level"] > 10:
            return None
        if type(Data.get("perfect")) is not bool:
            return None
        Uuid.UUID(hex=Data["run_id"])
        Count, Swaps, Duration, Reveal = LevelSettings(
            Data["level"], Data["difficulty"], Data["mode"]
        )
        Legacy = LevelSettings(Data["level"], Data["difficulty"])
        if (Data["swaps"], Data["swap_duration"], Data["reveal_frames"]) == Legacy[1:]:
            Count, Swaps, Duration, Reveal = Legacy
        if (Data["swaps"], Data["swap_duration"], Data["reveal_frames"]) != (
            Swaps,
            Duration,
            Reveal,
        ) and Data["state"] != "story":
            return None
        Cups = Data["cups"]
        for Key in ("answer_frames", "answer_total"):
            if type(Data.get(Key, 0)) is not int or not 0 <= Data.get(Key, 0) <= 10000:
                return None
        if Data.get("answer_frames", 0) > Data.get("answer_total", 0):
            return None
        if not isinstance(Cups, list) or len(Cups) != (
            0 if Data["state"] == "story" else Count
        ):
            return None
        if Cups:
            if any(type(C["slot"]) is not int for C in Cups):
                return None
            if sorted(C["slot"] for C in Cups) != list(range(Count)):
                return None
            if not 0 <= Data["correct_id"] < Count:
                return None
            for C in Cups:
                for Key in ("x", "y"):
                    Value = C[Key]
                    Limit = 450 if Key == "x" else 100
                    if (
                        type(Value) not in (int, float)
                        or not Math.isfinite(Value)
                        or abs(Value) > Limit
                    ):
                        return None
        Pair = Data.get("swap_pair")
        if Pair is not None:
            if (
                not isinstance(Pair, list)
                or len(Pair) != 4
                or any(type(V) is not int or not 0 <= V < Count for V in Pair)
            ):
                return None
            if Pair[0] == Pair[1] or Pair[2] == Pair[3]:
                return None
        return Data
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


class RunProgress:
    def __init__(Self, Session, FilePath):
        Self.Session = Session
        Self.FilePath = FilePath

    def Snapshot(Self):
        G = Self.Session
        Phase = G.PausedState if G.State == "paused" else G.State
        Data = {Key: ReadAttribute(G, Key) for Key in Counters}
        Data.update(
            {
                Key: ReadAttribute(G, Key)
                for Key in (
                    "mode",
                    "difficulty",
                    "level",
                    "score",
                    "lives",
                    "combo",
                    "perfect",
                    "run_id",
                )
            }
        )
        Data.update(
            version=1,
            state=Phase,
            answer_frames=G.AnswerFrames,
            answer_total=G.AnswerTotal,
            cups=[dict(slot=C.Slot, x=C.X, y=C.Y) for C in G.Cups],
            swap_pair=None,
        )
        if G.SwapPair is not None and G.Cups:
            A, B, Sa, Sb = G.SwapPair
            Data["swap_pair"] = [A.Cid, B.Cid, Sa, Sb]
        if Phase in ("result", "retry"):
            Lifted = {Cup.Cid for Cup, Ignored in G.Motion.Lifts}
            for Cup, Saved in zip(G.Cups, Data["cups"]):
                if Cup.Cid in Lifted or Cup.Cid == G.CorrectId:
                    Saved["y"] = 76
        return Data

    def Save(Self):
        Data = Self.Snapshot()
        if Data["state"] not in RunStates or not Persist(Self.FilePath, Data):
            return False
        Self.Session.SavedRun = Data
        return True

    def Clear(Self):
        Self.Session.SavedRun = None
        try:
            Self.FilePath.unlink(missing_ok=True)
        except OSError:
            pass

    def Restore(Self):
        Data = LoadRun(Self.FilePath)
        if Data is None:
            Self.Session.SavedRun = None
            return False
        G = Self.Session
        if Data["mode"] == "Endless" and not G.Profile.get("story_completed", False):
            G.SavedRun = None
            return False
        G.SavedRun = Data
        for Key in (
            "mode",
            "difficulty",
            "level",
            "score",
            "lives",
            "combo",
            "perfect",
            "run_id",
        ):
            WriteAttribute(G, Key, Data[Key])
        G.SaveFailed = G.RewardFailed = False
        if Data["state"] == "story":
            G.Views.ShowStory()
            return True
        G.Rounds.StartLevel(Refresh=False)
        for Key in Counters:
            WriteAttribute(G, Key, Data[Key])
        G.AnswerFrames = Data.get("answer_frames", 0)
        G.AnswerTotal = Data.get("answer_total", 0)
        if Data["state"] == "select" and not G.AnswerTotal:
            from GameConfig import AnswerSeconds, FrameMs

            G.AnswerTotal = round(
                AnswerSeconds(G.Level, G.Difficulty, G.Mode) * 1000 / FrameMs
            )
            G.AnswerFrames = G.AnswerTotal
        if len(G.Cups) != len(Data["cups"]):
            # Old Endless checkpoints used the former cup-count schedule.
            G.Cups = G.CupPool[: len(Data["cups"])]
            Spacing = min(150, 760 / max(1, len(G.Cups) - 1))
            G.Slots = [
                (I - (len(G.Cups) - 1) / 2) * Spacing for I in range(len(G.Cups))
            ]
            for I, Cup in enumerate(G.Cups):
                Cup.Reset(I, G.Slots[I], G.Profile["equipped"])
            G.Labels.clear()
            G.Screen.getcanvas().delete("choice_art")
            G.ArtLayer = "choice_art"
            from GameConfig import Colors

            for I, X in enumerate(G.Slots):
                G.Views.Rectangle(X - 15, -124, X + 15, -96, "#312331")
                G.Views.Write(G.Labels, X, -119, str(I + 1), 14, Colors["gold"])
            G.ArtLayer = "scene"
        for Cup, Saved in zip(G.Cups, Data["cups"]):
            Cup.Slot, Cup.X, Cup.Y = Saved["slot"], Saved["x"], Saved["y"]
            Cup.Render()
        Pair = Data["swap_pair"]
        G.SwapPair = (
            (G.Cups[Pair[0]], G.Cups[Pair[1]], Pair[2], Pair[3]) if Pair else None
        )
        G.State = Data["state"]
        if G.State in ("reveal", "result", "retry"):
            G.Coin.goto(G.Cups[G.CorrectId].X, -40)
            G.Coin.showturtle()
        else:
            G.Coin.hideturtle()
        Messages = {
            "reveal": ("Remember the coin", "Watch which cup holds it."),
            "shuffle": ("Follow the cup", ""),
            "select": ("Where is the coin?", G.Rounds.SelectionHint()),
            "result": ("Round complete", "Continue to the next table."),
            "retry": ("Not this cup", f"{G.Lives} lives left."),
        }
        G.Views.SetMessage(*Messages[G.State])
        G.Views.DrawAnswerTimer()
        if G.State == "select" and G.HintFrames:
            Remaining = G.HintFrames
            G.Views.ShowCoinHint()
            G.HintFrames = Remaining
        G.LastTick, G.FrameCredit = Time.monotonic(), 0.0
        G.Screen.update()
        return True
