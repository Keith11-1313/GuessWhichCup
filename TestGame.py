"""Regression tests. All score writes use a temporary directory."""

from GameObjects import InputCanvas
from pathlib import Path
import random as Random
import sys as Sys
from collections import Counter
import copy as Copy
import tempfile as Tempfile
import unittest as Unittest
import wave as Wave
from array import array as Array
from unittest.mock import patch as Patch

import WhatTheCup as App
import CupCollection as Collection
import PartyArt
import GameObjects
from RunProgress import LoadRun
from GameAudio import BackgroundMusic
from GameTheme import FontFamily, TextFont
from CollectionScreens import DrawFrames
from GameConfig import Difficulties, StoryLevels, LevelSettings
from ScoreStore import LoadScores, SaveScore


class StorageTests(Unittest.TestCase):
    def TestLegacySaveMigrationPreservesContents(Self):
        from NamingCompatibility import MigrateSave

        with Tempfile.TemporaryDirectory() as Folder:
            for LegacyName, CurrentName in (
                ("lantern_profile.json", "LanternProfile.json"),
                ("lantern_run.json", "LanternRun.json"),
                ("lantern_settings.json", "LanternSettings.json"),
            ):
                LegacyPath = Path(Folder) / LegacyName
                CurrentPath = Path(Folder) / CurrentName
                Contents = b'{"saved":123,"name":"kept"}'
                LegacyPath.write_bytes(Contents)
                Self.assertEqual(MigrateSave(CurrentPath, LegacyName), CurrentPath)
                Self.assertEqual(CurrentPath.read_bytes(), Contents)
                Self.assertFalse(LegacyPath.exists())
                LegacyPath.write_bytes(b'{"older":true}')
                Self.assertEqual(MigrateSave(CurrentPath, LegacyName), CurrentPath)
                Self.assertEqual(CurrentPath.read_bytes(), Contents)
                Self.assertTrue(LegacyPath.exists())

    def TestPascalCaseScoresLoadLegacyWithoutLosingProgress(Self):
        with Tempfile.TemporaryDirectory() as Folder:
            Legacy = Path(Folder) / "what_the_cup_scores.json"
            Current = Path(Folder) / "WhatTheCupScores.json"
            Legacy.write_text('{"story_normal":180}')
            Scores = LoadScores(Current)
            Self.assertEqual(Scores, {"story_normal": 180})
            Self.assertTrue(SaveScore(Current, Scores, "story_normal", 200))
            Self.assertEqual(LoadScores(Current), {"story_normal": 200})
            Self.assertEqual(LoadScores(Legacy), {"story_normal": 180})

    def TestInvalidSaves(Self):
        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "scores.json"
            Self.assertEqual(LoadScores(FilePath), {})
            for Content in ("broken", "[]", '{"x":null,"y":true,"z":-1,"good":42}'):
                FilePath.write_text(Content)
                Self.assertEqual(
                    LoadScores(FilePath), {"good": 42} if "good" in Content else {}
                )

    def TestAtomicBestScore(Self):
        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "scores.json"
            Scores = {}
            Self.assertTrue(SaveScore(FilePath, Scores, "story_normal", 120))
            Self.assertFalse(SaveScore(FilePath, Scores, "story_normal", 100))
            Self.assertEqual(LoadScores(FilePath), Scores)
            with Patch("ScoreStore.Os.replace", side_effect=OSError("denied")):
                Self.assertFalse(SaveScore(FilePath, Scores, "story_normal", 200))
            Self.assertEqual(LoadScores(FilePath)["story_normal"], 120)
            Self.assertEqual(Scores["story_normal"], 120)
            Self.assertEqual(list(Path(Folder).glob("*.tmp")), [])

    def TestDifficultyScales(Self):
        for Difficulty in Difficulties:
            Previous = LevelSettings(1, Difficulty)
            for Level in range(2, 100):
                Current = LevelSettings(Level, Difficulty)
                Self.assertTrue(3 <= Current[0] <= 6)
                Self.assertGreater(Current[1], Previous[1])
                Self.assertLessEqual(Current[2], Previous[2])
                Self.assertLessEqual(Current[3], Previous[3])
                Previous = Current


class CollectionTests(Unittest.TestCase):
    def TestExactOddsAndAllBoundaries(Self):
        Counts = Counter(Collection.PickSkin(I) for I in range(10000))
        Self.assertEqual(
            Counts,
            {
                Skin: Weight
                for Skin, Ignored, Ignored, Weight, Ignored in Collection.Cups
            },
        )
        with Self.assertRaises(ValueError):
            Collection.PickSkin(10000)

    def TestDrawEquipReloadDuplicateAndInsufficientFunds(Self):
        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "profile.json"
            Profile = Collection.FreshProfile()
            Self.assertTrue(Collection.CompleteStory(FilePath, Profile))
            Profile["tickets"] = 30
            Rng = Random.Random()
            for Skin, Roll in zip(
                ("normal", "uncommon", "rare", "epic", "legendary", "mythic"),
                (0, 5000, 7700, 9200, 9800, 9980),
            ):
                Before = Profile["tickets"]
                with (
                    Patch.object(Rng, "randrange", return_value=Roll),
                    Patch.object(Rng, "choice", side_effect=lambda Items: Items[0]),
                ):
                    Result, Status = Collection.Draw(FilePath, Profile, Rng)
                Self.assertEqual(Result, Skin)
                Self.assertEqual(
                    Profile["tickets"], Before - (2 if Skin == "normal" else 3)
                )
                Self.assertTrue(Collection.Equip(FilePath, Profile, Skin))
                Self.assertEqual(Collection.LoadProfile(FilePath), Profile)
            Self.assertEqual(Profile["draws"], 6)
            Profile["tickets"] = 2
            Original = Copy.deepcopy(Profile)
            Self.assertIsNone(Collection.Draw(FilePath, Profile)[0])
            Self.assertEqual(Profile, Original)
            Self.assertFalse(Collection.Equip(FilePath, Profile, "unknown"))

    def TestFailedWriteRollsBackAndRewardsOnce(Self):
        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "profile.json"
            Profile = Collection.FreshProfile()
            Self.assertTrue(Collection.CompleteStory(FilePath, Profile))
            Original = Copy.deepcopy(Profile)
            with Patch("CupCollection.Os.replace", side_effect=OSError("denied")):
                Self.assertIsNone(Collection.Draw(FilePath, Profile)[0])
                Self.assertEqual(Collection.Reward(FilePath, Profile, "Normal:1"), -1)
                Self.assertFalse(Collection.Equip(FilePath, Profile, "normal"))
            Self.assertEqual(Profile, Original)
            Self.assertEqual(list(Path(Folder).glob("*.tmp")), [])
            Self.assertEqual(Collection.Reward(FilePath, Profile, "Normal:1"), 1)
            Self.assertEqual(Collection.Reward(FilePath, Profile, "Normal:1"), 0)
            Self.assertEqual(Collection.LoadProfile(FilePath)["tickets"], 4)

    def TestInvalidProfileIsSafe(Self):
        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "profile.json"
            for Text in (
                "broken",
                "[]",
                "null",
                '{"tickets":true,"draws":-3,"owned":[{},"bad","mythic"],"equipped":"bad","rewards":[null,"x"]}',
            ):
                FilePath.write_text(Text)
                Profile = Collection.LoadProfile(FilePath)
                Self.assertEqual(Profile["tickets"], 3)
                Self.assertEqual(Profile["equipped"], "starter")
                Self.assertIn("starter", Profile["owned"])

    def TestStarterStoryGrantAndLockedTransactions(Self):
        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "profile.json"
            Profile = Collection.FreshProfile()
            Self.assertEqual(Profile["owned"], ["starter"])
            Self.assertEqual(Profile["equipped"], "starter")
            Before = Copy.deepcopy(Profile)
            Self.assertIsNone(Collection.Draw(FilePath, Profile)[0])
            Self.assertFalse(Collection.Equip(FilePath, Profile, "normal"))
            Self.assertEqual(Profile, Before)
            with Patch("CupCollection.Persist", return_value=False):
                Self.assertFalse(Collection.CompleteStory(FilePath, Profile, "Normal"))
            Self.assertEqual(Profile, Before)
            Self.assertTrue(Collection.CompleteStory(FilePath, Profile, "Normal"))
            Self.assertTrue(Profile["story_completed"])
            Self.assertEqual(Profile["equipped"], "normal")
            Self.assertEqual(Profile["tickets"], 4)
            Self.assertTrue(Collection.CompleteStory(FilePath, Profile, "Normal"))
            Self.assertEqual(Profile["tickets"], 4)
            Self.assertEqual(Profile["owned"].count("normal"), 1)
            Self.assertEqual(Collection.LoadProfile(FilePath), Profile)

    def TestOldProfilesKeepCollectionAndInferStoryCompletion(Self):
        import json as Json

        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "profile.json"
            Data = dict(
                version=1,
                tickets=42,
                owned=["normal", "rare"],
                equipped="rare",
                rewards=[],
            )
            FilePath.write_text(Json.dumps(Data))
            Profile = Collection.LoadProfile(FilePath)
            Self.assertFalse(Profile["story_completed"])
            Self.assertEqual(Profile["equipped"], "starter")
            Self.assertIn("rare", Profile["owned"])
            Self.assertEqual(Profile["tickets"], 42)
            Data["rewards"] = ["Easy:10"]
            FilePath.write_text(Json.dumps(Data))
            Profile = Collection.LoadProfile(FilePath)
            Self.assertTrue(Profile["story_completed"])
            Self.assertEqual(Profile["equipped"], "rare")

    def TestTenPullBoostsRaritiesAndRollsBackAsOneTransaction(Self):
        RarityOf = {Cup[0]: Cup[2] for Cup in Collection.Cups}
        Counts = Counter(
            RarityOf[Collection.PickSkin(I, Boosted=True)] for I in range(10000)
        )
        Self.assertEqual(
            Counts,
            {
                Rarity: Boosted
                for Rarity, Ignored, Boosted, Ignored in Collection.Rarities
            },
        )

        class Rng:
            def randrange(Self, N):
                return 0

            def choice(Self, Items):
                return "wood"

        with Tempfile.TemporaryDirectory() as Folder:
            FilePath = Path(Folder) / "profile.json"
            Profile = Collection.FreshProfile()
            Collection.CompleteStory(FilePath, Profile)
            Profile["tickets"] = 30
            Before = Copy.deepcopy(Profile)
            with Patch("CupCollection.Persist", return_value=False):
                Self.assertIsNone(Collection.DrawMany(FilePath, Profile, 10, Rng())[0])
            Self.assertEqual(Profile, Before)
            Results, Error = Collection.DrawMany(FilePath, Profile, 10, Rng())
            Self.assertEqual(Error, "")
            Self.assertEqual(len(Results), 10)
            Self.assertEqual(Results[0], ("wood", "new"))
            Self.assertEqual(Results[1:], [("wood", "duplicate")] * 9)
            Self.assertEqual(Profile["tickets"], 9)
            Self.assertEqual(Profile["draws"], 10)
            Self.assertEqual(Collection.LoadProfile(FilePath), Profile)
            Before = Copy.deepcopy(Profile)
            Self.assertIsNone(Collection.DrawMany(FilePath, Profile, 10)[0])
            Self.assertEqual(Profile, Before)


class GameTests(Unittest.TestCase):
    @classmethod
    def setUpClass(Class):
        Class.Folder = Tempfile.TemporaryDirectory()
        Class.Game = App.Game(
            RunLoop=False,
            ScorePath=Path(Class.Folder.name) / "scores.json",
            ProfilePath=Path(Class.Folder.name) / "profile.json",
        )
        Class.Game.SoundEnabled = False

    @classmethod
    def tearDownClass(Class):
        Class.Game.Close()
        Class.Folder.cleanup()

    def setUp(Self):
        Random.seed(27)
        Self.Game.Progress.Clear()
        Self.Game.Profile = Collection.FreshProfile()
        Collection.CompleteStory(Self.Game.ProfilePath, Self.Game.Profile)
        Self.Game.Cabinet.Page = 0
        Self.Game.Cabinet.Batch = []
        Self.Game.Cabinet.BatchPending = False
        Chooser = Patch(
            "CupCollection.Random.choice", side_effect=lambda Items: Items[0]
        )
        Chooser.start()
        Self.addCleanup(Chooser.stop)
        Self.Game.RewardFailed = False
        Self.Game.Mode = "Story"
        Self.Game.Difficulty = "Normal"
        Self.Game.Settings.Values.update(motion=True, fullscreen=False)
        Self.Game.AnswerFrames = Self.Game.AnswerTotal = 0
        Self.Game.Views.ShowMenu()

    def EnterRound(Self):
        while Self.Game.State == "story":
            Self.Game.Controls.Advance()

    def StartGameplay(Self):
        Self.Game.Rounds.StartGame()
        Self.EnterRound()

    def FinishShuffle(Self):
        Self.EnterRound()
        G = Self.Game
        G.Rounds.BeginShuffle()
        for Ignored in range(G.Swaps * (G.SwapDuration + 1) + 2):
            if G.State == "select":
                break
            G.Rounds.AnimateSwap()
        Self.assertEqual(G.State, "select")
        Self.assertEqual(sorted(C.Slot for C in G.Cups), list(range(len(G.Cups))))
        for Cup in G.Cups:
            Self.assertEqual(Cup.X, G.Slots[Cup.Slot])
            Self.assertEqual(Cup.Y, 0)

    def ClickButton(Self, Name):
        X1, Y1, X2, Y2 = Self.Game.Buttons[Name]
        Self.Game.Controls.OnClick((X1 + X2) / 2, (Y1 + Y2) / 2)

    def TestContextualCupInstructions(Self):
        G = Self.Game
        for Level, Count in ((1, 3), (4, 4), (7, 5), (10, 6)):
            G.Level = Level
            G.Rounds.StartLevel()
            Self.FinishShuffle()
            Text = "".join(
                G.Screen.getcanvas().itemcget(I, "text")
                for I in G.Screen.getcanvas().find_all()
                if G.Screen.getcanvas().type(I) == "text"
            )
            Self.assertIn(f"press 1-{Count}", Text)
            if Count != 6:
                Self.assertNotIn("1-6", Text)
            Score, Lives = G.Score, G.Lives
            G.Rounds.Choose(Count)
            Self.assertEqual((G.Score, G.Lives, G.State), (Score, Lives, "select"))
            G.Controls.TogglePause()
            G.Controls.TogglePause()
            Self.assertEqual(
                G.Rounds.SelectionHint(), f"Click a cup or press 1-{Count}."
            )

    def TestNewScreensTextBoundsAndActionSpacing(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()

        def Verify():
            G.Screen.update()
            for Bounds in G.Buttons.values():
                Self.assertGreaterEqual(
                    Bounds[1], -282, "Action touches bottom panel border"
                )
            for Item in Canvas.find_all():
                if Canvas.type(Item) != "text":
                    continue
                Label = Canvas.itemcget(Item, "text")
                Left, Top, Right, Bottom = Canvas.bbox(Item)
                Self.assertGreaterEqual(Left, -490, Label)
                Self.assertLessEqual(Right, 490, Label)
                Self.assertGreaterEqual(Top, -345, Label)
                Self.assertLessEqual(Bottom, 345, Label)
                for Key, (X1, Y1, X2, Y2) in G.Buttons.items():
                    if Key.startswith("equip:") and G.State == "cabinet":
                        continue  # A card deliberately contains its own text.
                    Intersects = Left < X2 and Right > X1 and Top < -Y1 and Bottom > -Y2
                    if Intersects:
                        Self.assertTrue(
                            X1 <= Left and Right <= X2 and -Y2 <= Top and Bottom <= -Y1,
                            (G.State, Key, Label, "text overlaps action"),
                        )

        G.Views.ShowMenu()
        Verify()
        for Mode in ("Story", "Endless"):
            for Difficulty in Difficulties:
                G.Mode, G.Difficulty = Mode, Difficulty
                G.Views.ShowMenu(NewGame=True)
                Verify()
                for Item in Canvas.find_all():
                    if Canvas.type(Item) != "text":
                        continue
                    Left, Top, Right, Bottom = Canvas.bbox(Item)
                    for Key, (X1, Y1, X2, Y2) in G.Buttons.items():
                        if (
                            Key.startswith(("mode:", "diff:"))
                            and X1 <= Left < X2
                            and -Y2 <= Top < -Y1
                        ):
                            Self.assertGreaterEqual(Left, X1 + 8)
                            Self.assertLessEqual(
                                Right, X2 - 8, Canvas.itemcget(Item, "text")
                            )
        Self.StartGameplay()
        G.Controls.RequestMenu()
        G.PauseMenu.SaveAndLeave()
        G.SavedRun["score"] = 999_999_999_999
        G.Views.ShowMenu()
        Verify()
        G.Progress.Clear()
        G.Views.ShowHowToPlay()
        Verify()
        for Level in range(1, 11):
            G.Level = Level
            G.Rounds.BeginChapter()
            Verify()
            G.Controls.Advance()
            Verify()
        G.Cabinet.ShowCabinet()
        Verify()
        G.Cabinet.ShowOdds()
        Verify()
        for Skin, Roll in zip(
            ("normal", "uncommon", "rare", "epic", "legendary", "mythic"),
            (0, 5000, 7700, 9200, 9800, 9980),
        ):
            G.Profile["tickets"] = 3
            G.Cabinet.ShowCabinet()
            with Patch("CupCollection.Random.randrange", return_value=Roll):
                G.Cabinet.DrawCup()
            G.Controls.Advance()
            Verify()
        G.Mode = "Endless"
        G.Rounds.StartGame()
        Verify()

    def TestRealMouseEventSelectsNumberButton(Self):
        G = Self.Game
        Self.StartGameplay()
        Self.FinishShuffle()
        Canvas = InputCanvas(G.Screen)
        Root = Canvas.winfo_toplevel()
        Cup = G.Cups[G.CorrectId]
        Canvas.event_generate(
            "<Button-1>",
            x=round(Cup.X - Canvas.canvasx(0)),
            y=round(110 - Canvas.canvasy(0)),
        )
        Root.update()
        Self.assertEqual(G.State, "result")
        Self.assertGreater(G.Score, 0)

    def TestStoryDialogueAndLocationsArePlayable(Self):
        G = Self.Game
        Settings = []
        for Level in range(1, 11):
            G.Level = Level
            G.Rounds.BeginChapter()
            Self.assertEqual(G.State, "story")
            Self.assertEqual(G.Cups, [])
            Settings.append(G.scene_location)
            G.Rounds.Choose(0)
            Self.assertEqual(G.State, "story")
            Self.ClickButton("story_next")
            Self.assertEqual(G.State, "reveal")
            Self.assertEqual(G.scene_location, Settings[-1])
        Self.assertEqual(
            Settings, ["hall"] * 3 + ["kitchen"] * 3 + ["terrace"] * 3 + ["dawn"]
        )
        G.Mode = "Endless"
        G.Rounds.StartGame()
        Self.assertEqual((G.State, G.scene_location), ("reveal", "afterparty"))

    def TestCabinetDrawAnimationEquipAndFairCups(Self):
        G = Self.Game
        G.Profile["tickets"] = 30
        Self.ClickButton("cabinet")
        Self.assertEqual(G.State, "cabinet")
        Self.ClickButton("odds")
        Self.assertEqual(G.State, "odds")
        G.Controls.Escape()
        for Skin, Roll in zip(
            ("normal", "uncommon", "rare", "epic", "legendary", "mythic"),
            (0, 5000, 7700, 9200, 9800, 9980),
        ):
            with Patch("CupCollection.Random.randrange", return_value=Roll):
                Self.ClickButton("draw")
            Self.assertEqual(G.State, "gacha_opening")
            Tickets = G.Profile["tickets"]
            G.Cabinet.DrawCup()
            Self.assertEqual(G.Profile["tickets"], Tickets)
            for Ignored in range(DrawFrames):
                if G.State == "gacha_opening":
                    G.Cabinet.AnimateDraw()
            Self.assertEqual(G.State, "gacha_reveal")
            Self.assertEqual(G.PendingCup, Skin)
            if G.Cabinet.DuplicatePending:
                Self.ClickButton("convert_duplicate")
                Self.ClickButton("cabinet")
            Self.ClickButton("equip:" + Skin)
            Self.assertEqual(G.Profile["equipped"], Skin)
            Self.assertEqual(Collection.LoadProfile(G.ProfilePath)["equipped"], Skin)
            Self.StartGameplay()
            Self.assertEqual({Cup.Sprite.shape() for Cup in G.Cups}, {Skin + "_cup"})
            G.Cabinet.ShowCabinet()
        G.Profile["tickets"] = 0
        G.Cabinet.ShowCabinet()
        Self.ClickButton("draw")
        Self.assertEqual(G.State, "cabinet")
        Self.assertEqual(G.Profile["tickets"], 0)

    def TestLockOverlayUnlockPhasesAndDuplicateBehavior(Self):
        G = Self.Game
        G.Profile = Collection.FreshProfile()
        Collection.CompleteStory(G.ProfilePath, G.Profile)
        G.Cabinet.Page = 0
        G.Profile["tickets"] = 12
        G.Cabinet.ShowCabinet()
        Canvas = G.Screen.getcanvas()
        Self.assertEqual(len(Canvas.find_withtag("cup_lock")), 5)
        Self.assertFalse(Canvas.find_withtag("lock:normal"))
        Self.assertFalse(
            any(
                Canvas.type(Item) == "text"
                and Canvas.itemcget(Item, "text") == "Locked"
                for Item in Canvas.find_all()
            )
        )
        with Patch("CupCollection.Random.randrange", return_value=7700):
            G.Cabinet.DrawCup()
        Self.assertEqual(G.DrawStatus, "new")
        SavedTickets = G.Profile["tickets"]
        Seen = set()
        for Ignored in range(DrawFrames):
            for Item in Canvas.find_withtag("unlock_lock"):
                Seen.add(Canvas.itemcget(Item, "image"))
            if G.State == "gacha_opening":
                G.Cabinet.AnimateDraw()
        Self.assertEqual(len(Seen), 4)
        Self.assertEqual(G.State, "gacha_reveal")
        Self.assertFalse(Canvas.find_withtag("unlock_lock"))
        Self.assertEqual(G.Profile["tickets"], SavedTickets)
        G.Cabinet.ShowCabinet()
        Self.assertFalse(Canvas.find_withtag("lock:rare"))

        Self.assertEqual(len(Canvas.find_withtag("cup_lock")), 5)
        with Patch("CupCollection.Random.randrange", return_value=7700):
            G.Cabinet.DrawCup()
        Self.assertEqual(G.DrawStatus, "duplicate")
        Self.assertFalse(Canvas.find_withtag("unlock_lock"))
        G.Controls.Advance()
        G.Cabinet.ShowCabinet()
        Self.assertFalse(Canvas.find_withtag("lock:rare"))

    def TestMenuCupReflectsEquippedSkin(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()
        G.Profile["owned"] = [Cup[0] for Cup in Collection.Cups]
        for Skin, *Ignored in Collection.Cups:
            Self.assertTrue(Collection.Equip(G.ProfilePath, G.Profile, Skin))
            G.Views.ShowMenu()
            Images = Canvas.find_withtag("menu_cup")
            Self.assertEqual(len(Images), 1)
            Self.assertIn(
                Canvas.itemcget(Images[0], "image"),
                {str(Frames[0]) for Frames in G.Assets["skin_frames"][Skin]},
            )
            Self.assertEqual(Canvas.coords(Images[0]), [-438.0, 246.0])
            Self.StartGameplay()
            Self.assertEqual({Cup.Sprite.shape() for Cup in G.Cups}, {Skin + "_cup"})

    def TestMusicVolumeIsClampedAndSeparateFromMute(Self):
        G = Self.Game
        WasEnabled = G.SoundEnabled
        G.Music.SetVolume(20)
        G.Controls.AdjustMusicVolume(-5)
        Self.assertEqual(G.Music.Volume, 15)
        G.Controls.AdjustMusicVolume(-100)
        Self.assertEqual(G.Music.Volume, 0)
        G.Controls.AdjustMusicVolume(200)
        Self.assertEqual(G.Music.Volume, 100)
        Self.assertEqual(G.SoundEnabled, WasEnabled)
        G.Music.SetVolume(20)

    def TestPerfectStoryAllDifficulties(Self):
        G = Self.Game
        for Difficulty in Difficulties:
            G.Difficulty = Difficulty
            Self.StartGameplay()
            Expected = 1000
            for Level in range(1, StoryLevels + 1):
                Self.FinishShuffle()
                Expected += Level * 100 + (G.Lives - 1) * 20
                G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
                Score = G.Score
                G.Rounds.Choose(0)  # Repeated input must not award points twice.
                Self.assertEqual(G.Score, Score)
                if Level < StoryLevels:
                    Self.assertEqual(G.State, "result")
                    G.Controls.Advance()
            Self.assertEqual(G.State, "victory")
            Self.assertEqual(G.Score, Expected)
            Self.assertGreaterEqual(G.BestScore(), Expected)

    def TestPauseCheckpointRestoresExactMidShuffleBoard(Self):
        G = Self.Game
        Self.StartGameplay()
        G.Rounds.BeginShuffle()
        G.Rounds.AnimateSwap()
        Board = [(C.Cid, C.Slot, C.X, C.Y) for C in G.Cups]
        Pair = (G.SwapPair[0].Cid, G.SwapPair[1].Cid, *G.SwapPair[2:])
        Frames = (G.CompletedSwaps, G.SwapFrame)
        G.Controls.RequestMenu()
        Self.assertEqual(G.State, "paused")
        G.Update()
        Self.assertEqual(Board, [(C.Cid, C.Slot, C.X, C.Y) for C in G.Cups])
        Self.ClickButton("save_menu")
        Self.assertEqual(G.State, "menu")
        Self.assertIsNotNone(LoadRun(G.Progress.FilePath))
        Self.ClickButton("resume_run")
        Self.assertEqual(G.State, "shuffle")
        Self.assertEqual(Board, [(C.Cid, C.Slot, C.X, C.Y) for C in G.Cups])
        Self.assertEqual(Pair, (G.SwapPair[0].Cid, G.SwapPair[1].Cid, *G.SwapPair[2:]))
        Self.assertEqual(Frames, (G.CompletedSwaps, G.SwapFrame))
        Self.FinishShuffle()
        Self.assertEqual(G.State, "select")

    def TestSavedMenuSettingsDoNotChangeTheCheckpoint(Self):
        G = Self.Game
        G.Mode, G.Difficulty = "Endless", "Hard"
        Self.StartGameplay()
        G.Controls.RequestMenu()
        Self.ClickButton("save_menu")
        Original = G.Progress.FilePath.read_bytes()
        Self.assertNotIn("mode:Story", G.Buttons)
        Self.assertNotIn("diff:Easy", G.Buttons)
        Self.ClickButton("new_game_setup")
        Self.assertEqual(G.State, "menu_setup")
        G.Controls.CycleDifficulty()
        Self.assertEqual(G.State, "menu_setup")
        with Patch.object(G.Views, "Write", wraps=G.Views.Write) as Write:
            Self.ClickButton("mode:Story")
            Self.ClickButton("diff:Easy")
            Labels = [Call.args[3] for Call in Write.call_args_list]
        Self.assertIn("New game", Labels)
        Self.assertNotIn("resume_run", G.Buttons)
        Self.assertEqual(G.Progress.FilePath.read_bytes(), Original)
        Self.ClickButton("back_saved")
        Self.assertEqual(G.State, "menu")
        Self.ClickButton("resume_run")
        Self.assertEqual((G.Mode, G.Difficulty), ("Endless", "Hard"))

    def TestPauseRestartResetsRunAndUsesDistinctIcons(Self):
        G = Self.Game
        G.Mode, G.Difficulty = "Endless", "Normal"
        Self.StartGameplay()
        G.Score, G.Level, G.Lives = 500, 3, 1
        PreviousRun = G.RunId
        G.Controls.RequestMenu()
        Self.assertEqual(
            set(G.Buttons), {"resume", "restart", "save_menu", "save_exit", "settings"}
        )
        Bounds = sorted(
            (B for K, B in G.Buttons.items() if K != "settings"),
            key=lambda Item: Item[1],
        )
        for Lower, Upper in zip(Bounds, Bounds[1:]):
            Self.assertLess(Lower[3], Upper[1])
        Canvas = G.Screen.getcanvas()
        Images = [
            Canvas.itemcget(I, "image")
            for I in Canvas.find_withtag("pause_art")
            if Canvas.type(I) == "image"
        ]
        for Icon in ("restart", "home", "exit"):
            Self.assertIn(str(G.Assets["icons"][Icon]), Images)
        Self.ClickButton("restart")
        Self.assertEqual((G.State, G.Score, G.Level, G.Lives), ("reveal", 0, 1, 3))
        Self.assertNotEqual(G.RunId, PreviousRun)
        Self.assertIsNone(G.PausedState)
        Self.assertFalse(Canvas.find_withtag("pause_art"))

    def TestAnswerTimeoutCostsOneLifeAndPauseSettingsFreezeIt(Self):
        G = Self.Game
        Self.StartGameplay()
        Self.FinishShuffle()
        Self.assertGreater(G.AnswerFrames, 0)
        G.AnswerFrames = 2
        G.Controls.TogglePause()
        G.Settings.Open()
        Self.assertEqual(G.State, "settings")
        with Patch("WhatTheCup.Time.monotonic", return_value=G.LastTick + 0.08):
            G.Update()
        Self.assertEqual(G.AnswerFrames, 2)
        G.Controls.Escape()
        Self.assertEqual(G.State, "paused")
        G.Controls.TogglePause()
        Before = G.Lives
        with Patch("WhatTheCup.Time.monotonic", return_value=G.LastTick + 0.08):
            G.Update()
        Self.assertEqual((G.State, G.Lives), ("retry", Before - 1))
        G.Rounds.Timeout()
        Self.assertEqual(G.Lives, Before - 1)

    def TestCountdownCheckpointIsPreservedAndTimerIsAutomatic(Self):
        G = Self.Game
        G.Mode = "Endless"
        Self.StartGameplay()
        Self.FinishShuffle()
        G.AnswerFrames = 123
        G.Controls.RequestMenu()
        Self.ClickButton("save_menu")
        Self.ClickButton("resume_run")
        Self.assertEqual((G.State, G.AnswerFrames), ("select", 123))
        G.Settings.Open()
        Self.assertNotIn("setting:timer", G.Buttons)
        Self.assertNotIn("setting:tab_gameplay", G.Buttons)
        Self.assertNotIn("setting:sound", G.Buttons)
        G.Settings.Close()
        G.PauseMenu.Resume()
        Self.assertEqual(G.AnswerFrames, 123)

    def TestSettingsPersistAndFullscreenIsExplicit(Self):
        from GameSettings import GameSettings

        G = Self.Game
        G.Settings.Open()
        Self.assertEqual(G.State, "settings")
        G.Settings.Action("motion")
        Self.assertFalse(G.Settings.Values["motion"])
        Root = G.Screen.getcanvas().winfo_toplevel()
        with Patch.object(Root, "attributes") as Attributes:
            G.Settings.Fullscreen()
            Attributes.assert_called_once_with("-fullscreen", True)
        Loaded = GameSettings(G, G.Settings.FilePath)
        Self.assertTrue(Loaded.Values["fullscreen"])
        Self.assertFalse(Loaded.Values["motion"])
        G.Settings.Close()
        Self.assertEqual(G.State, "menu")

    def TestEndlessCurveHasGradualCupsAndBoundedShuffles(Self):
        for Difficulty in Difficulties:
            Previous = LevelSettings(1, Difficulty, "Endless")
            for Level in range(2, 201):
                Current = LevelSettings(Level, Difficulty, "Endless")
                Self.assertGreaterEqual(Current[0], Previous[0])
                Self.assertLessEqual(Current[1], 24)
                Self.assertGreaterEqual(Current[2], 18)
                Self.assertGreaterEqual(Current[3], 75)
                Previous = Current
        Self.assertEqual(
            [
                LevelSettings(Level, "Normal", "Endless")[0]
                for Level in (1, 5, 6, 10, 11, 15, 16, 200)
            ],
            [3, 3, 4, 4, 5, 5, 6, 6],
        )

    def TestMotionFinishesAndReducedMotionRemovesOverlays(Self):
        G = Self.Game
        G.Motion.Begin()
        G.Motion.Pointer(0, 0)
        G.Motion.Feedback(True)
        for Ignored in range(80):
            G.Motion.Update()
        Canvas = G.Screen.getcanvas()
        Self.assertFalse(Canvas.find_withtag("ui_transition"))
        Self.assertFalse(Canvas.find_withtag("ui_burst"))
        G.Settings.Values["motion"] = False
        G.Motion.Begin()
        G.Motion.Update()
        Self.assertFalse(Canvas.find_withtag("ui_transition"))

    def TestLegacyEndlessCheckpointKeepsItsFourCups(Self):
        import json as Json

        G = Self.Game
        G.Level = 4
        G.Rounds.StartLevel()
        Self.FinishShuffle()
        G.Mode = "Endless"
        Data = G.Progress.Snapshot()
        Data.pop("answer_frames")
        Data.pop("answer_total")
        Self.assertTrue(Collection.Persist(G.Progress.FilePath, Data))
        Self.assertEqual(len(LoadRun(G.Progress.FilePath)["cups"]), 4)
        Self.assertTrue(G.Progress.Restore())
        Self.assertEqual(len(G.Cups), 4)
        Self.assertGreater(G.AnswerFrames, 0)
        Self.assertEqual(sorted(Cup.Slot for Cup in G.Cups), [0, 1, 2, 3])

    def TestSettingsButtonsAndLabelsFitTheOverlay(Self):
        G = Self.Game
        G.Settings.Open()
        Canvas = G.Screen.getcanvas()
        for Item in Canvas.find_withtag("pause_art"):
            if Canvas.type(Item) == "text":
                Left, Top, Right, Bottom = Canvas.bbox(Item)
                Self.assertGreaterEqual(Left, -380)
                Self.assertLessEqual(Right, 380, Canvas.itemcget(Item, "text"))
                Self.assertGreaterEqual(Top, -232)
                Self.assertLessEqual(Bottom, 246)
        G.Settings.Close()

    def TestFullscreenViewportScalesArtTextAndInverseMouseCoordinates(Self):
        G = Self.Game
        View = G.Viewport
        Canvas = G.Screen.getcanvas()
        Item = Canvas.create_image(25, -30, image=G.Assets["heart_full"])
        Label = Canvas.create_text(25, 0, text="Scaled text", font=TextFont(12))
        try:
            G.Settings.Values["fullscreen"] = True
            with (
                Patch.object(View.Widget, "winfo_width", return_value=1920),
                Patch.object(View.Widget, "winfo_height", return_value=1080),
            ):
                View.Resize()
            Self.assertGreater(View.Factor, 1.5)
            Self.assertAlmostEqual(Canvas.coords(Item)[0], 25, places=3)
            Self.assertAlmostEqual(
                View.Raw["coords"](Item)[0], 25 * View.Factor, places=3
            )
            Self.assertAlmostEqual(
                Canvas.canvasx(100), View.Raw["canvasx"](100) / View.Factor
            )
            Self.assertTrue(Canvas.find_withtag("viewport_backdrop"))
            Scaled = View.ScaledImages[(str(G.Assets["heart_full"]), View.Factor)]
            Self.assertEqual(Scaled.width(), round(24 * View.Factor))
        finally:
            G.Settings.Values["fullscreen"] = False
            View.Resize()
            Canvas.delete(Item, Label)
        Self.assertEqual(View.Factor, 1)

    def TestMasterMusicAndGameSoundLevelsAreIndependent(Self):
        G = Self.Game
        with Patch.object(G.Mixer, "Command", return_value=0) as Command:
            G.Settings.Values.update(master=50, effects=60)
            G.Mixer.Channels["click"] = "test_click"
            G.Music.SetVolume(40)
            G.Mixer.Apply()
            Self.assertEqual(G.Music.Volume, 40)
            Self.assertEqual(G.Music.Master, 50)
            Command.assert_called_with("setaudio test_click volume to 300")
            G.Settings.SetLevel("effects", 0)
            Self.assertEqual(G.Music.Volume, 40)
            Self.assertEqual(G.Settings.Values["master"], 50)
            Command.assert_called_with("setaudio test_click volume to 0")
            G.Mixer.Channels.clear()
        G.Settings.Values.update(master=80, effects=70)
        G.Music.SetVolume(20)
        G.Mixer.Apply()

    def TestBackgroundAnimationIsBoundedAndRespectsReducedMotion(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()
        for Ignored in range(300):
            G.Ambient.Update()
        Self.assertLessEqual(len(Canvas.find_withtag("ambient_art")), 8)
        Self.assertGreater(len(Canvas.find_withtag("ambient_art")), 0)
        G.Settings.Values["motion"] = False
        for Ignored in range(4):
            G.Ambient.Update()
        Self.assertFalse(Canvas.find_withtag("ambient_art"))

    def TestLockedStoryProfileCannotEnterEndlessOrCabinet(Self):
        G = Self.Game
        G.Profile = Collection.FreshProfile()
        G.Views.ShowMenu()
        Self.assertNotIn("mode:Endless", G.Buttons)
        Self.assertNotIn("cabinet", G.Buttons)
        G.Controls.MenuAction("mode:Endless")
        Self.assertEqual(G.Mode, "Story")
        Self.assertFalse(G.Cabinet.ShowCabinet())
        G.Mode = "Endless"
        G.Rounds.StartGame()
        Self.assertEqual((G.Mode, G.State), ("Story", "story"))
        Self.assertEqual(G.Profile["equipped"], "starter")

    def TestStoryUnlockSaveRetryDoesNotAwardScoreTwice(Self):
        G = Self.Game
        G.Profile = Collection.FreshProfile()
        G.Mode, G.Level = "Story", 10
        G.Rounds.StartLevel()
        Self.FinishShuffle()
        with Patch("CupCollection.Persist", return_value=False):
            G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
        Self.assertEqual(G.State, "victory")
        Self.assertTrue(G.StoryUnlockPending)
        Self.assertFalse(G.Profile["story_completed"])
        Score = G.Score
        G.Controls.Advance()
        Self.assertEqual(G.Score, Score)
        Self.assertFalse(G.StoryUnlockPending)
        Self.assertTrue(G.Profile["story_completed"])
        Self.assertEqual(G.Profile["equipped"], "normal")
        Self.assertEqual(G.Profile["tickets"], 4)

    def TestTenDrawWaitsForNextBeforeConvertingDuplicates(Self):
        G = Self.Game
        G.Profile["tickets"] = 30
        G.Cabinet.ShowCabinet()
        with Patch("CupCollection.Random.randrange", return_value=0):
            Self.ClickButton("draw10")
        G.Controls.Advance()
        Self.assertEqual(G.State, "batch_reveal")
        Self.assertTrue(G.Cabinet.BatchPending)
        Self.assertFalse(G.Cabinet.BatchConverting)
        Self.assertEqual(len(G.Cabinet.Batch), 10)
        Before = G.Profile["tickets"]
        for Ignored in range(60):
            G.Cabinet.AnimateBatch()
        Self.assertFalse(G.Cabinet.BatchConverting)
        Self.ClickButton("batch_next")
        Self.assertTrue(G.Cabinet.BatchConverting)
        for Ignored in range(45):
            G.Cabinet.AnimateBatch()
        Self.assertFalse(G.Cabinet.BatchPending)
        Self.assertEqual(G.Profile["tickets"], Before)
        Canvas = G.Screen.getcanvas()
        Tickets = [
            I
            for I in Canvas.find_all()
            if Canvas.type(I) == "image"
            and Canvas.itemcget(I, "image") == str(G.Assets["ticket_reward"])
        ]
        Self.assertEqual(len(Tickets), 10)
        G.Controls.Advance()
        Self.assertEqual(G.State, "cabinet")

    def TestLastHeartRevealsBothCupsBeforeGameOver(Self):
        G = Self.Game
        Self.StartGameplay()
        Self.FinishShuffle()
        G.Lives = 1
        Wrong = next(C for C in G.Cups if C.Cid != G.CorrectId)
        G.Rounds.Choose(Wrong.Slot)
        Self.assertEqual((G.State, G.Lives), ("last_reveal", 0))
        G.Controls.Advance()
        G.Controls.RequestMenu()
        G.Controls.Escape()
        Self.assertEqual(G.State, "last_reveal")
        for Ignored in range(16):
            G.Motion.Update()
        Self.assertEqual(Wrong.Y, 76)
        Self.assertEqual(G.Cups[G.CorrectId].Y, 76)
        Self.assertTrue(G.Coin.isvisible())
        G.DeathFrames = 89
        with Patch("WhatTheCup.Time.monotonic", return_value=G.LastTick + 0.025):
            G.Update()
        Self.assertEqual(G.State, "over")
        Self.ClickButton("play_again")
        Self.assertEqual((G.Level, G.Score, G.Lives), (1, 0, 3))

    def TestSkinFramesAreSynchronisedForAllPlayableCups(Self):
        G = Self.Game
        Self.StartGameplay()
        Self.FinishShuffle()
        for Ignored in range(12):
            G.SkinAnimation.Update()
        G.Screen.update()
        Image = str(G.Assets["skin_frames"][G.Profile["equipped"]][1][2])
        Canvas = G.Screen.getcanvas()
        Images = [
            I
            for I in Canvas.find_all()
            if Canvas.type(I) == "image" and Canvas.itemcget(I, "image") == Image
        ]
        Self.assertEqual(len(Images), len(G.Cups))
        Self.assertEqual(
            {Cup.Sprite.shape() for Cup in G.Cups}, {G.Profile["equipped"] + "_cup"}
        )
        Self.assertEqual(len(G.Assets["skin_frames"]), 19)
        Self.assertTrue(
            all(len(Frames) == 4 for Frames in G.Assets["skin_frames"].values())
        )

    def TestPauseSaveFailureStaysOpenAndExitSavesFirst(Self):
        G = Self.Game
        Self.StartGameplay()
        Self.FinishShuffle()
        G.Controls.Escape()
        with (
            Patch("RunProgress.Persist", return_value=False),
            Patch.object(G, "Close") as Close,
        ):
            Self.ClickButton("save_exit")
            Close.assert_not_called()
            Self.assertEqual(G.State, "paused")
        with Patch.object(G, "Close") as Close:
            Self.ClickButton("save_exit")
            Close.assert_called_once()
            Self.assertEqual(LoadRun(G.Progress.FilePath)["state"], "select")

    def TestCheckpointReplayDoesNotDuplicateEndlessTickets(Self):
        G = Self.Game
        G.Mode = "Endless"
        Self.StartGameplay()
        Self.FinishShuffle()
        G.Controls.TogglePause()
        Self.assertTrue(G.Progress.Save())
        G.Controls.TogglePause()
        Before = G.Profile["tickets"]
        G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
        Self.assertEqual(G.Profile["tickets"], Before + 1)
        Self.assertTrue(G.Effects.Ticket)
        Self.assertTrue(G.Progress.Restore())
        G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
        Self.assertEqual(G.Profile["tickets"], Before + 1)
        Self.assertFalse(G.Effects.Ticket)

    def TestDuplicateConversionIsVisualAndNeverAwardsTwice(Self):
        G = Self.Game
        G.Cabinet.ShowCabinet()
        with Patch("CupCollection.Random.randrange", return_value=0):
            G.Cabinet.DrawCup()
        G.Cabinet.RevealDraw()
        Self.assertIsNone(G.Effects.Kind)
        Self.assertTrue(G.Cabinet.DuplicatePending)
        for Ignored in range(110):
            G.Effects.Update()
        Self.assertIsNone(G.Effects.Kind)
        Bounds = G.Buttons["convert_duplicate"]
        G.Controls.OnClick((Bounds[0] + Bounds[2]) / 2, (Bounds[1] + Bounds[3]) / 2)
        Self.assertEqual(G.Effects.Kind, "duplicate")
        Self.assertFalse(G.Cabinet.DuplicatePending)
        G.Cabinet.ConvertDuplicate()
        Self.assertEqual(G.Profile["tickets"], 1)
        for Ignored in range(110):
            G.Effects.Update()
        Self.assertEqual(G.Profile["tickets"], 1)
        Canvas = G.Screen.getcanvas()
        Images = [
            Canvas.itemcget(I, "image")
            for I in Canvas.find_withtag("reward_fx")
            if Canvas.type(I) == "image"
        ]
        Self.assertIn(str(G.Assets["ticket_reward"]), Images)
        G.Cabinet.ShowCabinet()
        Self.assertFalse(Canvas.find_withtag("reward_fx"))

    def TestCoinAndEquippedWindowIcon(Self):
        G = Self.Game
        Self.assertEqual(G.Coin.shape(), "coin")
        Self.assertEqual(
            (G.Assets["coin"].width(), G.Assets["coin"].height()), (24, 24)
        )
        G.Profile["owned"].append("legendary")
        G.IconSkin = None
        Root = G.Screen.getcanvas().winfo_toplevel()
        with Patch.object(Root, "iconphoto", wraps=Root.iconphoto) as Icon:
            G.Controls.CollectionAction("equip:legendary")
            Self.assertEqual(G.IconSkin, "legendary")
            Icon.assert_called_once_with(True, G.WindowIcon)

    def TestInvalidCheckpointIsIgnored(Self):
        G = Self.Game
        Self.StartGameplay()
        G.Controls.TogglePause()
        Self.assertTrue(G.Progress.Save())
        Valid = LoadRun(G.Progress.FilePath)
        Self.assertIsNotNone(Valid)
        for Key, Value in (
            ("correct_id", 99),
            ("lives", -1),
            ("mode", "bad"),
            ("cups", []),
        ):
            Data = Copy.deepcopy(Valid)
            Data[Key] = Value
            import json as Json

            G.Progress.FilePath.write_text(Json.dumps(Data))
            Self.assertIsNone(LoadRun(G.Progress.FilePath))
        G.Progress.FilePath.write_text("broken JSON")
        Self.assertIsNone(LoadRun(G.Progress.FilePath))

    def TestWrongRetryGameOver(Self):
        G = Self.Game
        Self.StartGameplay()
        for Lives in (2, 1, 0):
            Self.FinishShuffle()
            Wrong = next(C.Slot for C in G.Cups if C.Cid != G.CorrectId)
            G.Rounds.Choose(Wrong)
            Self.assertEqual(G.Lives, Lives)
            Self.assertFalse(G.Perfect)
            Self.assertEqual(G.State, "retry" if Lives else "last_reveal")
            if Lives:
                G.Controls.Advance()
                Self.assertEqual(G.Level, 1)
        G.DeathFrames = 30
        G.Controls.Advance()
        Self.assertEqual(G.State, "over")
        G.Controls.Advance()
        Self.assertEqual(G.Lives, 3)

    def TestDedicatedGameOverPreservesProgressAndRoutesButtons(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()
        for Mode in ("Story", "Endless"):
            G.Mode, G.Level, G.Score, G.Lives = Mode, 4, 1234, 1
            Before = Copy.deepcopy(G.Profile)
            G.Rounds.StartLevel()
            Self.FinishShuffle()
            Wrong = next(C.Slot for C in G.Cups if C.Cid != G.CorrectId)
            G.Rounds.Choose(Wrong)
            Self.assertEqual((G.State, G.Lives), ("last_reveal", 0))
            Self.assertTrue(G.Coin.isvisible())
            Self.assertTrue(G.Cups)
            G.DeathFrames = 30
            G.Controls.Advance()
            Self.assertEqual((G.State, G.Lives), ("over", 0))
            Self.assertEqual(G.Cups, [])
            Self.assertFalse(G.Coin.isvisible())
            Self.assertEqual(G.Profile, Before)
            Self.assertEqual(set(G.Buttons), {"play_again", "game_menu"})
            Images = [
                Canvas.itemcget(I, "image")
                for I in Canvas.find_all()
                if Canvas.type(I) == "image"
            ]
            Self.assertIn(str(G.Assets["party_over"]), Images)
            for Item in Canvas.find_all():
                if Canvas.type(Item) == "text":
                    Left, Top, Right, Bottom = Canvas.bbox(Item)
                    Self.assertTrue(-490 <= Left < Right <= 490)
                    Self.assertTrue(-345 <= Top < Bottom <= 345)
            Self.ClickButton("game_menu")
            Self.assertEqual(G.State, "menu")
            G.Views.ShowGameOver()
            Self.ClickButton("play_again")
            Self.assertEqual(G.Level, 1)
            Self.assertEqual(G.Score, 0)
            Self.assertEqual(G.State, "story" if Mode == "Story" else "reveal")

    def TestEndlessCombo(Self):
        G = Self.Game
        G.Mode = "Endless"
        Self.StartGameplay()
        for Ignored in range(15):
            Self.FinishShuffle()
            G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
            G.Controls.Advance()
        Self.assertEqual(G.Combo, 15)
        Self.assertEqual(G.Level, 16)
        Self.FinishShuffle()
        G.Rounds.Choose(next(C.Slot for C in G.Cups if C.Cid != G.CorrectId))
        Self.assertEqual(G.Combo, 0)

    def TestPauseInterruptAndHitboxes(Self):
        G = Self.Game
        Self.StartGameplay()
        G.Rounds.Choose(0)
        Self.assertEqual(G.State, "reveal")
        G.Controls.TogglePause()
        G.Rounds.Choose(0)
        Self.assertEqual(G.State, "paused")
        G.Controls.TogglePause()
        G.Rounds.BeginShuffle()
        G.Rounds.AnimateSwap()
        G.Controls.TogglePause()
        G.Controls.TogglePause()
        Self.FinishShuffle()
        Cup = G.Cups[G.CorrectId]
        G.Controls.OnClick(
            Cup.X, -140
        )  # Bare table outside the number button is not a hit.
        Self.assertEqual(G.State, "select")
        G.Rounds.Choose(999)
        Self.assertEqual(G.State, "select")
        G.Controls.OnClick(Cup.X, 0)
        Self.assertEqual(G.State, "result")
        Self.StartGameplay()
        G.Rounds.BeginShuffle()
        G.Rounds.AnimateSwap()
        G.Views.ShowHowToPlay()
        G.Update()
        Self.assertEqual(G.State, "how_to_play")
        G.Controls.Advance()
        Self.assertEqual(G.State, "menu")

    def TestMenuNavigationAndNoSpriteLeak(Self):
        G = Self.Game
        G.Controls.CycleMode()
        Self.assertEqual(G.Mode, "Endless")
        G.Controls.CycleDifficulty()
        Self.assertEqual(G.Difficulty, "Hard")
        Count = len(G.Screen.turtles())
        Sprites = tuple(Cup.Sprite for Cup in G.CupPool)
        for Ignored in range(20):
            Self.StartGameplay()
            G.Views.ShowMenu()
        Self.assertEqual(len(G.Screen.turtles()), Count)
        for Level, Expected in ((1, 3), (6, 4), (11, 5), (16, 6)):
            G.Level = Level
            G.Rounds.StartLevel()
            Self.assertEqual(len(G.Cups), Expected)
            Self.assertEqual(tuple(Cup.Sprite for Cup in G.Cups), Sprites[:Expected])
            G.Views.ShowMenu()
            Self.assertTrue(all(not Sprite.isvisible() for Sprite in Sprites))
        Self.assertEqual(len(G.Screen.turtles()), Count)

    def TestFailedHighScoreSaveIsVisible(Self):
        G = Self.Game
        Self.StartGameplay()
        Self.FinishShuffle()
        G.Scores = {}
        with Patch("RoundLogic.SaveScore", return_value=False):
            G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
        Self.assertTrue(G.SaveFailed)
        Canvas = G.Screen.getcanvas()
        Messages = [
            Canvas.itemcget(Item, "text")
            for Item in Canvas.find_all()
            if Canvas.type(Item) == "text"
        ]
        Self.assertIn("Save failed. Check folder permissions.", Messages)

    def TestCupImagesAreAboveTheBackground(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()
        for Level, Count in ((1, 3), (4, 4), (7, 5), (10, 6)):
            G.Level = Level
            G.Rounds.StartLevel()
            G.Screen.update()
            for Phase in ("reveal", "shuffle", "select"):
                if Phase == "shuffle":
                    G.Rounds.BeginShuffle()
                    G.Rounds.AnimateSwap()
                elif Phase == "select":
                    Self.FinishShuffle()
                G.Screen.update()
                Stack = list(Canvas.find_all())
                ImageName = str(G.Assets["skins"][G.Profile["equipped"]][2])
                CupItems = [
                    Item
                    for Item in Stack
                    if Canvas.type(Item) == "image"
                    and Canvas.itemcget(Item, "image") == ImageName
                ]
                Self.assertEqual(len(CupItems), Count)
                BackgroundTop = max(
                    Stack.index(I) for I in Canvas.find_withtag("scene")
                )
                Self.assertTrue(all(Stack.index(I) > BackgroundTop for I in CupItems))

    def TestPngAssetsAndMissingFileMessage(Self):
        G = Self.Game
        for Images in G.Assets["skins"].values():
            Self.assertEqual((Images[0].width(), Images[0].height()), (32, 34))
        for Name, Image in G.Assets["backgrounds"].items():
            Size = (435, 410) if Name == "menu" else (940, 410)
            Self.assertEqual((Image.width(), Image.height()), Size)
        Self.assertNotIn("portraits", G.Assets)
        with Tempfile.TemporaryDirectory() as Folder:
            with Patch.object(PartyArt, "AssetFolder", Path(Folder)):
                with Self.assertRaisesRegex(FileNotFoundError, "Starter.png"):
                    PartyArt.LoadAssets(G.Screen)

    def TestHeartHudMatchesRemainingLives(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()
        for Difficulty, Settings in Difficulties.items():
            G.Difficulty = Difficulty
            for Lives in range(Settings["lives"] + 1):
                G.Lives = Lives
                G.Views.DrawHud()
                Images = [
                    Canvas.itemcget(Item, "image")
                    for Item in Canvas.find_withtag("hud_art")
                    if Canvas.type(Item) == "image"
                ]
                Self.assertEqual(Images.count(str(G.Assets["heart_full"])), Lives)
                Self.assertEqual(
                    Images.count(str(G.Assets["heart_empty"])),
                    Settings["lives"] - Lives,
                )

    def TestFooterLinksAreClickableInEachPhase(Self):
        G = Self.Game

        def Click(Action):
            X1, Y1, X2, Y2 = G.FooterActions[Action]
            G.Controls.OnClick((X1 + X2) / 2, (Y1 + Y2) / 2)

        Click("help")
        Self.assertEqual(G.State, "how_to_play")
        Click("escape")
        Self.assertEqual(G.State, "menu")
        with Patch.object(G, "Close") as Close:
            Click("escape")
            Close.assert_called_once()
        Click("advance")
        Self.assertEqual(G.State, "story")
        Click("advance")
        Self.assertEqual(G.State, "reveal")
        Click("pause")
        Self.assertEqual(G.State, "paused")
        Previous = G.SoundEnabled
        Click("sound")
        Self.assertNotEqual(G.SoundEnabled, Previous)
        Click("pause")
        Self.assertEqual(G.State, "reveal")
        Self.FinishShuffle()
        Click("menu")
        Self.assertEqual(G.State, "paused")
        Self.ClickButton("save_menu")
        Self.assertEqual(G.State, "menu")
        G.Controls.OpenCabinetFromMenu()
        Click("escape")
        Self.assertEqual(G.State, "menu")

    def TestEndlessHintIsGatedTracksCupAndExpires(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()
        for Mode, Level, Visible in (
            ("Story", 10, False),
            ("Endless", 10, False),
            ("Endless", 11, True),
            ("Endless", 25, True),
        ):
            G.Mode, G.Level = Mode, Level
            G.Rounds.StartLevel()
            Self.FinishShuffle()
            Items = Canvas.find_withtag("coin_hint")
            Self.assertEqual(bool(Items), Visible)
            if Visible:
                Cup = G.Cups[G.CorrectId]
                Self.assertEqual(Canvas.coords(Items[0]), [Cup.X - 4, 58])
                G.Controls.TogglePause()
                Remaining = G.HintFrames
                G.Update()
                Self.assertEqual(G.HintFrames, Remaining)
                G.Controls.TogglePause()
                G.HintFrames = 1
                G.LastTick = 100
                G.FrameCredit = 0
                with Patch("WhatTheCup.Time.monotonic", return_value=100.05):
                    G.Update()
                Self.assertFalse(Canvas.find_withtag("coin_hint"))
                G.Views.ShowCoinHint()
                G.Rounds.Choose(Cup.Slot)
                Self.assertFalse(Canvas.find_withtag("coin_hint"))
        G.Views.ShowMenu()
        Self.assertFalse(Canvas.find_withtag("coin_hint"))

    @Unittest.skipUnless(Sys.platform == "win32", "Windows WAV playback backend")
    def TestCustomSoundPlaybackNeverUsesSystemAlerts(Self):
        import winsound as Winsound

        with Patch.object(Winsound, "PlaySound") as Playback:
            with Patch.object(Winsound, "MessageBeep") as SystemAlert:
                for Kind in (
                    "click",
                    "reveal",
                    "correct",
                    "wrong",
                    "win",
                    "unlock",
                    "ticket",
                    "equip",
                    "pause",
                ):
                    GameObjects.Tone(Kind)
                    FilePath, Flags = Playback.call_args.args
                    Self.assertTrue(Path(FilePath).is_file())
                    Self.assertTrue(Flags & Winsound.SND_ASYNC)
                    Self.assertTrue(Flags & Winsound.SND_NODEFAULT)
                Self.assertEqual(Playback.call_count, 9)
                SystemAlert.assert_not_called()

    def TestAudioAssetsHaveSafeLevelsAndCleanEffectEndpoints(Self):
        Folder = Path(GameObjects.__file__).parent / "assets" / "sounds"
        for FilePath in Folder.glob("*.wav"):
            with (
                Self.subTest(Sound=FilePath.name),
                Wave.open(str(FilePath), "rb") as Sound,
            ):
                Self.assertEqual(Sound.getsampwidth(), 2)
                Self.assertEqual(Sound.getnchannels(), 2)
                Self.assertEqual(Sound.getframerate(), 22050)
                Samples = Array("h", Sound.readframes(Sound.getnframes()))
                Peak = max(abs(Value) for Value in Samples)
                Self.assertGreater(Peak, 100)
                Self.assertLess(Peak, 32700, "Audio clips at full scale")
                if FilePath.stem != "LanternParty":
                    Self.assertLessEqual(Peak, 5000, "Effect is too loud for the set")
                    Self.assertLessEqual(
                        max(abs(Value) for Value in Samples[:2] + Samples[-2:]), 4
                    )

    def TestMenuClickPlaysFeedbackOnceAndMuteBlocksEffects(Self):
        G = Self.Game
        G.Views.ShowMenu()
        with Patch.object(G, "PlayTone") as Sound:
            Self.ClickButton("mode:Endless")
            Sound.assert_called_once_with("click")
        G.SoundEnabled = False
        with Patch("WhatTheCup.Tone") as Sound:
            G.PlayTone("correct")
            Sound.assert_not_called()

    def TestCupNumbersUseClearFontAndFitNumberChips(Self):
        from tkinter import font as Font

        G = Self.Game
        G.Level = 10
        G.Rounds.StartLevel()
        G.Screen.update()
        Canvas = G.Screen.getcanvas()
        Labels = []
        for Item in Canvas.find_all():
            if Canvas.type(Item) != "text":
                continue
            Text = Canvas.itemcget(Item, "text")
            Left, Top, Right, Bottom = Canvas.bbox(Item)
            if Text in "123456" and 90 <= Top <= 125:
                Actual = Font.Font(font=Canvas.itemcget(Item, "font")).actual()
                Self.assertEqual(Actual["family"], "Consolas")
                Self.assertEqual(Actual["size"], 14)
                Slot = int(Text) - 1
                Self.assertGreaterEqual(Left, G.Slots[Slot] - 15)
                Self.assertLessEqual(Right, G.Slots[Slot] + 15)
                Self.assertGreaterEqual(Top, 96)
                Self.assertLessEqual(Bottom, 124)
                Labels.append(Text)
        Self.assertCountEqual(Labels, list("123456"))

    def TestBundledFontAndKeycapBounds(Self):
        from tkinter import font as Font

        G = Self.Game
        Self.assertEqual(Font.Font(font=TextFont(12)).actual("family"), FontFamily)
        for Show in (
            G.Views.ShowMenu,
            G.Views.ShowHowToPlay,
            G.Cabinet.ShowCabinet,
        ):
            Show()
            G.Screen.update()
            Canvas = G.Screen.getcanvas()
            for Item in Canvas.find_withtag("footer_art"):
                if Canvas.type(Item) == "text":
                    Left, Top, Right, Bottom = Canvas.bbox(Item)
                    Self.assertTrue(-470 <= Left < Right <= 470)
                    Self.assertTrue(305 <= Top < Bottom <= 337)
            Self.assertIn("sound", G.FooterActions)

    def TestStoryDialogueHasPanelPadding(Self):
        G = Self.Game
        G.Mode = "Story"
        Canvas = G.Screen.getcanvas()
        for Level in range(1, 11):
            G.Level = Level
            G.Views.ShowStory()
            G.Screen.update()
            for Item in Canvas.find_all():
                if Canvas.type(Item) != "text":
                    continue
                Left, Top, Right, Bottom = Canvas.bbox(Item)
                if 200 < Top < 290 and Left < 0:
                    Self.assertGreaterEqual(Left, -445)
                    Self.assertLessEqual(Right, 220)
                    Self.assertLessEqual(Bottom, 282)

    @Unittest.skipUnless(Sys.platform == "win32", "Windows music backend")
    def TestMusicStopsAndRestartsWithoutDuplicateTimers(Self):
        from unittest.mock import Mock

        Scheduler = Mock()
        Scheduler.after.return_value = "music_timer"
        Music = BackgroundMusic(Scheduler)
        Commands = []

        def Command(Text):
            Commands.append(Text)
            return 0

        with Patch.object(Music, "Command", side_effect=Command):
            Music.Start()
            Self.assertTrue(Music.Opened)
            Music.Start()
            Self.assertEqual(Scheduler.after.call_count, 1)
            Music.Stop()
            Scheduler.after_cancel.assert_called_once_with("music_timer")
            Self.assertFalse(Music.Opened)
            Self.assertTrue(Commands[-1].startswith("close "))
            Music.Start()
            Self.assertTrue(Music.Opened)
            Self.assertEqual(Scheduler.after.call_count, 2)
            Music.Stop()

    def TestLiveTkErrorsAreNotSilenced(Self):
        G = Self.Game
        with Patch.object(G.Screen, "update", side_effect=App.Tkinter.TclError("bug")):
            with Self.assertRaises(App.Tkinter.TclError):
                G.Update()
        Self.assertTrue(G.Running)

    def TestImperfectEndingAndMenuClicks(Self):
        G = Self.Game
        Box = G.Buttons["mode:Endless"]
        G.Controls.OnClick((Box[0] + Box[2]) / 2, (Box[1] + Box[3]) / 2)
        Self.assertEqual(G.Mode, "Endless")
        G.Mode = "Story"
        Self.StartGameplay()
        G.Perfect = False
        G.Level = 10
        G.Rounds.StartLevel()
        Self.FinishShuffle()
        G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
        Self.assertEqual(G.State, "victory")
        Self.assertEqual(G.Score, 1040)
        G.Controls.OnClick(0, 0)
        Self.assertEqual(G.State, "victory")
        G.Controls.Escape()
        Self.assertEqual(G.State, "menu")

    def TestElapsedTimeRevealAndPause(Self):
        G = Self.Game
        Self.StartGameplay()
        G.RevealFrame = G.RevealFrames - 1
        G.LastTick = 100.0
        with Patch("WhatTheCup.Time.monotonic", return_value=100.05):
            G.Update()
        Self.assertEqual(G.State, "shuffle")
        G.Controls.TogglePause()
        Frames = G.SwapFrame
        G.LastTick = 100.0
        with Patch("WhatTheCup.Time.monotonic", return_value=101.0):
            G.Update()
        Self.assertEqual(G.SwapFrame, Frames)
        Self.assertEqual(G.State, "paused")

    def TestTextStaysInsideWindowAndLayersDoNotLeak(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()

        def VerifyText():
            G.Screen.update()
            for Item in Canvas.find_all():
                if Canvas.type(Item) == "text":
                    Text = Canvas.itemcget(Item, "text")
                    Self.assertNotIn("\u00e2", Text)
                    Bounds = Canvas.bbox(Item)
                    Self.assertGreaterEqual(Bounds[0], -490, Text)
                    Self.assertLessEqual(Bounds[2], 490, Text)
                    Self.assertGreaterEqual(Bounds[1], -345, Text)
                    Self.assertLessEqual(Bounds[3], 345, Text)

        for Mode in ("Story", "Endless"):
            G.Mode = Mode
            for Difficulty in Difficulties:
                G.Difficulty = Difficulty
                G.Views.ShowMenu()
                VerifyText()
        G.Views.ShowHowToPlay()
        VerifyText()
        G.Mode = "Story"
        Self.StartGameplay()
        Initial = len(Canvas.find_all())
        for Ignored in range(20):
            G.Views.DrawHud()
        Self.assertEqual(len(Canvas.find_all()), Initial)
        for Level in (1, 4, 7, 10):
            G.Level = Level
            G.Rounds.StartLevel()
            VerifyText()
            Self.FinishShuffle()
            G.Rounds.Choose(G.Cups[G.CorrectId].Slot)
            VerifyText()

    def TestEveryGameEntryDrawsGameplayInsteadOfMenu(Self):
        G = Self.Game
        Canvas = G.Screen.getcanvas()
        for Mode in ("Story", "Endless"):
            for Difficulty in Difficulties:
                for Entry in ("click", "enter", "restart", "help"):
                    G.Mode = Mode
                    G.Difficulty = Difficulty
                    G.Views.ShowMenu()
                    if Entry == "click":
                        X1, Y1, X2, Y2 = G.Buttons["start"]
                        G.Controls.OnClick((X1 + X2) / 2, (Y1 + Y2) / 2)
                    elif Entry == "enter":
                        G.Controls.Advance()
                    elif Entry == "restart":
                        G.Controls.Restart()
                    else:
                        G.Views.ShowHowToPlay()
                        G.Controls.Restart()
                    G.Screen.update()
                    Self.EnterRound()
                    Self.assertEqual(G.State, "reveal")
                    Scene = [
                        Canvas.coords(Item)
                        for Item in Canvas.find_withtag("scene")
                        if Canvas.type(Item) == "rectangle"
                    ]
                    Self.assertIn(
                        [-470.0, -236.0, 470.0, 174.0], Scene, (Mode, Difficulty, Entry)
                    )
                    Self.assertIn(
                        [-470.0, 184.0, 470.0, 292.0], Scene, (Mode, Difficulty, Entry)
                    )
                    Images = [
                        Canvas.itemcget(Item, "image")
                        for Item in Canvas.find_all()
                        if Canvas.type(Item) == "image"
                    ]
                    Backgrounds = G.Assets["backgrounds"]
                    Expected = "hall" if Mode == "Story" else "afterparty"
                    Self.assertIn(str(Backgrounds[Expected]), Images)
                    Self.assertNotIn(str(Backgrounds["menu"]), Images)


def load_tests(Loader, StandardTests, Pattern):
    """Unittest requires this hook name; project test methods use PascalCase."""
    Loader.testMethodPrefix = "Test"
    Suite = Unittest.TestSuite()
    for Value in globals().values():
        if isinstance(Value, type) and issubclass(Value, Unittest.TestCase):
            Suite.addTests(Loader.loadTestsFromTestCase(Value))
    return Suite


if __name__ == "__main__":
    Unittest.main()
