"""Cosmetic cup collection and transactional local progression."""

from NamingCompatibility import MigrateSave
import copy as Copy
import json as Json
import os as Os
from pathlib import Path
import random as Random
import tempfile as Tempfile
from GameConfig import SaveFolder
from CupCatalog import Cups, AllCups, Rarities

ProfileFile = SaveFolder / "LanternProfile.json"
DrawCost = 3
BatchCost = 30


def FreshProfile():
    return {
        "version": 2,
        "tickets": 3,
        "owned": ["starter"],
        "equipped": "starter",
        "story_completed": False,
        "rewards": [],
        "draws": 0,
    }


def LoadProfile(FilePath):
    if FilePath.name == "LanternProfile.json":
        FilePath = MigrateSave(FilePath, "lantern_profile.json")
    Profile = FreshProfile()
    try:
        Data = Json.loads(FilePath.read_text(encoding="utf-8"))
        if not isinstance(Data, dict):
            return Profile
        for Key in ("tickets", "draws"):
            if type(Data.get(Key)) is int and Data[Key] >= 0:
                Profile[Key] = Data[Key]
        Known = {Cup[0] for Cup in AllCups}
        if isinstance(Data.get("owned"), list):
            Profile["owned"] = list(
                dict.fromkeys(
                    ["starter"]
                    + [
                        Item
                        for Item in Data["owned"]
                        if isinstance(Item, str) and Item in Known
                    ]
                )
            )
        if Data.get("equipped") in Profile["owned"]:
            Profile["equipped"] = Data["equipped"]
        if isinstance(Data.get("rewards"), list):
            Profile["rewards"] = list(
                dict.fromkeys(Item for Item in Data["rewards"] if isinstance(Item, str))
            )
        Profile["story_completed"] = Data.get("story_completed") is True or any(
            Key in Profile["rewards"] for Key in ("Easy:10", "Normal:10", "Hard:10")
        )
        if Profile["story_completed"] and "normal" not in Profile["owned"]:
            Profile["owned"].append("normal")
        if not Profile["story_completed"]:
            Profile["equipped"] = "starter"
    except (OSError, ValueError):
        pass
    return Profile


def Persist(FilePath, Profile):
    """Replace a save atomically. A failed write leaves the previous save intact."""
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
            Json.dump(Profile, File, indent=2)
            File.flush()
            Os.fsync(File.fileno())
        Os.replace(Temporary, FilePath)
        return True
    except OSError:
        return False
    finally:
        if Temporary and Os.path.exists(Temporary):
            try:
                Os.unlink(Temporary)
            except OSError:
                pass


def Reward(FilePath, Profile, Key=None):
    """One ticket per correct round; Story chapters pay once per difficulty."""
    if Key and Key in Profile["rewards"]:
        return 0
    Updated = Copy.deepcopy(Profile)
    Updated["tickets"] += 1
    if Key:
        Updated["rewards"].append(Key)
    if not Persist(FilePath, Updated):
        return -1
    Profile.update(Updated)
    return 1


def PickSkin(Roll, Boosted=False, Rng=None):
    if not 0 <= Roll < 10000:
        raise ValueError("Draw roll must be between 0 and 9999")
    Total = 0
    for Rarity, Normal, Batch, Ignored in Rarities:
        Weight = Batch if Boosted else Normal
        Total += Weight
        if Roll < Total:
            Designs = [Cup[0] for Cup in Cups if Cup[2] == Rarity]
            if Rng is not None:
                return Rng.choice(Designs)
            Offset = Roll - (Total - Weight)
            return Designs[min(2, Offset * 3 // Weight)]


def Draw(FilePath, Profile, Rng=Random):
    Results, Error = DrawMany(FilePath, Profile, 1, Rng)
    return Results[0] if Results else (None, Error)


def DrawMany(FilePath, Profile, Count=10, Rng=Random):
    """One atomic purchase: all cups and duplicate refunds, or no changes."""
    if not Profile.get("story_completed", False):
        return None, "Finish Story to unlock cup draws."
    if type(Count) is not int or Count not in (1, 10):
        raise ValueError("Choose one draw or ten draws")
    Cost = DrawCost * Count
    if Profile["tickets"] < Cost:
        return None, "Not enough tickets"
    Updated = Copy.deepcopy(Profile)
    Updated["tickets"] -= Cost
    Results = []
    for Ignored in range(Count):
        Selected = PickSkin(Rng.randrange(10000), Boosted=Count == 10, Rng=Rng)
        Duplicate = Selected in Updated["owned"]
        if Duplicate:
            Updated["tickets"] += 1
        else:
            Updated["owned"].append(Selected)
        Results.append((Selected, "duplicate" if Duplicate else "new"))
    Updated["draws"] += Count
    if not Persist(FilePath, Updated):
        return None, "Save failed; no tickets spent"
    Profile.update(Updated)
    return Results, ""


def CompleteStory(FilePath, Profile, Difficulty=None):
    """Grant the Brass Keepsake and unlock both post-story modes atomically."""
    Updated = Copy.deepcopy(Profile)
    Updated["story_completed"] = True
    if "normal" not in Updated["owned"]:
        Updated["owned"].append("normal")
    if not Profile.get("story_completed", False):
        Updated["equipped"] = "normal"
    Key = f"{Difficulty}:10" if Difficulty else None
    if Key and Key not in Updated["rewards"]:
        Updated["rewards"].append(Key)
        Updated["tickets"] += 1
    if not Persist(FilePath, Updated):
        return False
    Profile.update(Updated)
    return True


def Equip(FilePath, Profile, Skin):
    if not Profile.get("story_completed", False) and Skin != "starter":
        return False
    if Skin not in Profile["owned"]:
        return False
    Updated = Copy.deepcopy(Profile)
    Updated["equipped"] = Skin
    if not Persist(FilePath, Updated):
        return False
    Profile.update(Updated)
    return True
