"""Resolve serialized legacy attribute names without changing save schemas."""

import re as Re

ProjectModules = {
    "__main__",
    "ScoreStore",
    "PartyStory",
    "RunProgress",
    "VisualEffects",
    "AmbientScene",
    "SoundMixer",
    "GameTheme",
    "PauseMenu",
    "PartyArt",
    "RoundLogic",
    "UiMotion",
    "CupCollection",
    "GameConfig",
    "CollectionScreens",
    "GameSettings",
    "SkinAnimation",
    "GameAudio",
    "GameScreens",
    "CupCatalog",
    "TestGame",
    "WhatTheCup",
    "QaPlayerFlow",
    "GameObjects",
    "GameViewport",
    "InputControls",
}


def PascalName(Name):
    return "".join(
        Part[:1].upper() + Part[1:] for Part in Re.split(r"[_-]+", Name) if Part
    )


def AttributeName(Object, Name):
    Module = getattr(Object, "__module__", type(Object).__module__)
    if Module in ProjectModules:
        return "FilePath" if Name == "path" else PascalName(Name)
    return Name


def ReadAttribute(Object, Name, *Default):
    return getattr(Object, AttributeName(Object, Name), *Default)


def WriteAttribute(Object, Name, Value):
    setattr(Object, AttributeName(Object, Name), Value)


def AssetPath(RelativePath):
    from pathlib import PurePosixPath

    FilePath = PurePosixPath(RelativePath)
    return str(FilePath.with_name(PascalName(FilePath.stem) + FilePath.suffix))


def MigrateSave(FilePath, LegacyName):
    """Move an older save only when the new filename does not exist."""
    LegacyPath = FilePath.with_name(LegacyName)
    if not FilePath.exists() and LegacyPath.is_file():
        try:
            LegacyPath.replace(FilePath)
        except OSError:
            return LegacyPath
    return FilePath
