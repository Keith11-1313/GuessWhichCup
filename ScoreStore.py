"""File-based high-score storage kept separate from the game screen."""

import json as Json
import os as Os
import tempfile as Tempfile


def LoadScores(FilePath):
    try:
        if FilePath.name == "WhatTheCupScores.json" and not FilePath.exists():
            Legacy = FilePath.with_name("what_the_cup_scores.json")
            if Legacy.is_file():
                FilePath = Legacy
        Data = Json.loads(FilePath.read_text(encoding="utf-8"))
        if not isinstance(Data, dict):
            return {}
        return {
            Key: Value
            for Key, Value in Data.items()
            if isinstance(Key, str) and type(Value) is int and Value >= 0
        }
    except (OSError, ValueError):
        return {}


def SaveScore(FilePath, Scores, Key, Score):
    """Save only when the new score beats the existing score."""
    Old = Scores.get(Key, 0)
    Old = Old if type(Old) is int and Old >= 0 else 0
    if type(Score) is not int or Score < 0 or Score <= Old:
        return False

    Updated = dict(Scores, **{Key: Score})
    Temporary = None
    try:
        with Tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=FilePath.parent,
            prefix=FilePath.name + ".",
            suffix=".tmp",
            delete=False,
        ) as File:
            Temporary = File.name
            Json.dump(Updated, File, indent=2)
            File.flush()
            Os.fsync(File.fileno())
        Os.replace(Temporary, FilePath)
        Scores[Key] = Score
        return True
    except OSError:
        return False
    finally:
        if Temporary and Os.path.exists(Temporary):
            try:
                Os.unlink(Temporary)
            except OSError:
                pass
