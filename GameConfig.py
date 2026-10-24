"""Small, easy-to-explain configuration module for What The Cup."""

from NamingCompatibility import ReadAttribute

from pathlib import Path
import sys as Sys

Root = Path(__file__).resolve().parent
# A bundled executable extracts artwork to a temporary folder. Keep saves
# beside the actual executable so progress survives closing the game.
SaveFolder = (
    Path(Sys.executable).resolve().parent
    if ReadAttribute(Sys, "frozen", False)
    else Root
)
SaveFile = SaveFolder / "WhatTheCupScores.json"

Width, Height = 1000, 700
FrameMs = 17
StoryLevels = 10

# Shared by the painted result button and its click handler.
ResultButtonBounds = (239, -282, 441, -240)

Colors = {
    "background": "#101820",
    "white": "#f3efe3",
    "muted": "#b5c0ca",
    "gold": "#f1c878",
    "danger": "#ff8294",
}

Difficulties = {
    "Easy": {"extra_swaps": 0, "duration": 1.35, "reveal": 1.45, "lives": 5},
    "Normal": {"extra_swaps": 2, "duration": 1.00, "reveal": 1.00, "lives": 3},
    "Hard": {"extra_swaps": 5, "duration": 0.72, "reveal": 0.70, "lives": 1},
}


def LevelSettings(Level, Difficulty, Mode="Story"):
    """Return cup count and timing values for one level."""
    Tune = Difficulties[Difficulty]
    if Mode == "Endless":
        Cups = min(6, 3 + (Level - 1) // 5)
        Swaps = min(24, 5 + (Level - 1) // 2 + Tune["extra_swaps"])
        Frames = round(max(24, 45 - (Level - 1)) * Tune["duration"])
        Reveal = round(max(100, 170 - (Level - 1) * 3) * Tune["reveal"])
        return Cups, Swaps, max(18, Frames), max(75, Reveal)
    Cups = min(6, 3 + (Level - 1) // 3)
    Swaps = 4 + Level * 2 + Tune["extra_swaps"]
    Frames = max(9, round(max(15, 45 - (Level - 1) * 3) * Tune["duration"]))
    Reveal = max(65, round(max(100, 175 - (Level - 1) * 6) * Tune["reveal"]))
    return Cups, Swaps, Frames, Reveal


def AnswerSeconds(Level, Difficulty, Mode):
    Base = {"Easy": 12, "Normal": 10, "Hard": 8}[Difficulty]
    return max(5, Base - (Level - 1) // 10) if Mode == "Endless" else Base
