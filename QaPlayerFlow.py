"""Exercise real Tk mouse/key events with isolated saves.

Run python -B QaPlayerFlow.py. Optional --screenshots DIR saves a review sheet.
Install Requirements.txt before running the source or this developer QA tool.
"""

from GameObjects import InputCanvas
import argparse as Argparse
from pathlib import Path
import tempfile as Tempfile
import time as Time
from unittest.mock import patch as Patch

import WhatTheCup as App
import CupCollection as Collection


def Run(ScreenshotDir=None):
    with Tempfile.TemporaryDirectory() as Folder:
        Game = App.Game(
            RunLoop=False,
            ScorePath=Path(Folder) / "scores.json",
            ProfilePath=Path(Folder) / "profile.json",
        )
        Game.SoundEnabled = False
        Game.Screen.title("Guess Which Cup | Automated QA - temporary saves")
        Root = Game.Screen.getcanvas().winfo_toplevel()
        Canvas = InputCanvas(Game.Screen)
        Captured = []

        def Pump(Seconds=0.04):
            Deadline = Time.monotonic() + Seconds
            while Time.monotonic() < Deadline:
                Root.update()
                Time.sleep(0.004)

        def Click(X, Y):
            Canvas.event_generate(
                "<Button-1>",
                x=round(X - Canvas.canvasx(0)),
                y=round(-Y - Canvas.canvasy(0)),
            )
            Pump(0.015)

        def Button(Name):
            X1, Y1, X2, Y2 = Game.Buttons[Name]
            Click((X1 + X2) / 2, (Y1 + Y2) / 2)

        def Key(Name):
            Canvas.focus_force()
            Canvas.event_generate("<KeyPress>", keysym=Name)
            Pump(0.015)
            if Name.lower() == "m" and Game.State == "paused":
                Button("save_menu")

        def WaitFor(State, Timeout=30):
            Deadline = Time.monotonic() + Timeout
            while Game.State != State and Time.monotonic() < Deadline:
                Pump()
            assert Game.State == State, (State, Game.State)

        def Capture(Name):
            if ScreenshotDir:
                from PIL import ImageGrab

                ScreenshotDir.mkdir(exist_ok=True, parents=True)
                # ImageGrab captures desktop pixels, so the game must be on top.
                Root.lift()
                Root.focus_force()
                Pump(0.08)
                Game.Screen.update()
                Root.update_idletasks()
                ImageGrab.grab(
                    bbox=(
                        Root.winfo_rootx(),
                        Root.winfo_rooty(),
                        Root.winfo_rootx() + Root.winfo_width(),
                        Root.winfo_rooty() + Root.winfo_height(),
                    )
                ).save(ScreenshotDir / (Name + ".png"))
                Captured.append(Name)

        try:
            Pump(0.1)
            Capture("complete-menu")
            assert Game.Profile["equipped"] == "starter"
            assert "cabinet" not in Game.Buttons and "mode:Endless" not in Game.Buttons
            Button("diff:Easy")
            Button("start")
            for Level in range(1, 11):
                assert Game.Level == Level
                assert Game.State == "story"
                Capture("complete-story-" + str(Level))
                Button("story_next")
                assert Game.State == "reveal"
                assert {Cup.Sprite.shape() for Cup in Game.Cups} == {"starter_cup"}
                Capture("complete-game-" + str(Level))
                WaitFor("shuffle")
                Pump(0.3)
                Key("p")
                assert Game.State == "paused"
                Capture("complete-shuffle-" + str(Level))
                Key("p")
                WaitFor("select")
                assert (
                    Game.Rounds.SelectionHint()
                    == f"Click a cup or press 1-{len(Game.Cups)}."
                )
                Capture("complete-select-" + str(len(Game.Cups)))
                if Level == 1:
                    Key("6")
                    assert Game.State == "select"
                    Wrong = next(
                        Cup.Slot for Cup in Game.Cups if Cup.Cid != Game.CorrectId
                    )
                    Key(str(Wrong + 1))
                    assert Game.State == "retry"
                    Capture("complete-retry")
                    Click(340, -266)
                    assert Game.State == "reveal"
                    WaitFor("select")
                Key(str(Game.Cups[Game.CorrectId].Slot + 1))
                assert Game.State == ("victory" if Level == 10 else "result")
                if Level < 10:
                    Click(340, -266)
                print("Verified Story chapter", Level, flush=True)
            Capture("complete-ending")
            assert Game.Profile["story_completed"]
            assert Game.Profile["equipped"] == "normal"
            Key("m")
            Button("cabinet")
            assert Game.State == "cabinet"
            Capture("complete-cabinet")
            Button("odds")
            assert Game.State == "odds"
            Capture("complete-odds")
            Button("cabinet")
            with (
                Patch("CupCollection.Random.randrange", return_value=7700),
                Patch(
                    "CupCollection.Random.choice", side_effect=lambda Items: Items[0]
                ),
            ):
                Button("draw")
            assert Game.State == "gacha_opening"
            Capture("complete-draw-opening")
            WaitFor("gacha_reveal")
            Capture("complete-draw-rare")
            Button("equip:rare")
            assert Collection.LoadProfile(Game.ProfilePath)["equipped"] == "rare"
            Button("back")
            Button("mode:Endless")
            Button("start")
            assert Game.State == "reveal" and Game.scene_location == "afterparty"
            Capture("complete-endless")
            Key("p")
            assert Game.State == "paused"
            Key("p")
            assert Game.State == "reveal"
            WaitFor("select")
            Click(Game.Cups[Game.CorrectId].X, 0)
            assert Game.State == "result"
            Key("Return")
            assert Game.Level == 2
            Key("m")
            Button("cabinet")
            assert Game.Profile["tickets"] == 11
            assert Collection.LoadProfile(Game.ProfilePath) == Game.Profile
            print(
                "Verified real mouse/key story, retry, all cup counts, gacha, equip, saves, Endless and pause.",
                flush=True,
            )
            if ScreenshotDir:
                from PIL import Image

                Names = [
                    "complete-menu",
                    "complete-cabinet",
                    "complete-draw-rare",
                    "complete-story-4",
                    "complete-game-4",
                    "complete-game-7",
                    "complete-game-10",
                    "complete-endless",
                    "complete-ending",
                ]
                Sheet = Image.new("RGB", (1500, 1050), "#191522")
                for I, Name in enumerate(Names):
                    with Image.open(ScreenshotDir / (Name + ".png")) as Photo:
                        Photo.thumbnail((500, 350))
                        Sheet.paste(Photo, ((I % 3) * 500, (I // 3) * 350))
                Sheet.save(ScreenshotDir / "complete-review.png")
        finally:
            Game.Close()


if __name__ == "__main__":
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("--screenshots", type=Path, dest="Screenshots")
    Run(Parser.parse_args().Screenshots)
