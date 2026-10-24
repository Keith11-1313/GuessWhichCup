"""Paged animated collection, single pulls and an atomic ten-pull reveal."""

import CupCollection as Collection
from PartyArt import Frame, PlaceImage, PlaceSkin
from GameConfig import Colors

DrawFrames = 72
LockOpenFrame = 28
PageSize = 6


class CupCabinet:
    def __init__(Self, Session, Views):
        Self.Session = Session
        Self.Views = Views
        Self.Page = 0
        Self.DuplicatePending = False
        Self.Batch = []
        Self.BatchPending = False
        Self.BatchConverting = False
        Self.BatchFrame = 0
        Self.BatchArt = {}

    def Unlocked(Self):
        if Self.Session.Profile.get("story_completed", False):
            return True
        Self.Views.ShowMenu()
        return False

    def CabinetShell(Self, State):
        G = Self.Session
        G.State = State
        G.ClearCups()
        Self.Views.DrawBackground()
        if State in ("gacha_opening", "gacha_reveal", "batch_reveal"):
            PlaceImage(Self.Views, G.Assets["cabinet_reveal"], -470, 236)
        G.MenuText.clear()
        G.HudText.clear()
        G.Message.clear()
        G.Buttons = {}

    def ShowCabinet(Self, Notice=""):
        if not Self.Unlocked():
            return False
        G = Self.Session
        G.UpdateWindowIcon()
        Self.CabinetShell("cabinet")
        Frame(Self.Views, -470, 174, 470, 236, "#141d27")
        Self.Views.Write(
            G.MenuText, -440, 202, "Cup cabinet", 20, Colors["gold"], "left"
        )
        Self.Views.DrawButton("equip:starter", "Plain Cup", 0, 206, 174)
        Owned = sum(Cup[0] in G.Profile["owned"] for Cup in Collection.Cups)
        Self.Views.Write(
            G.MenuText,
            440,
            206,
            f"{G.Profile['tickets']} tickets",
            16,
            Colors["white"],
            "right",
        )
        Self.Views.Write(
            G.MenuText,
            440,
            183,
            f"{Owned} of {len(Collection.Cups)} collected",
            10,
            Colors["muted"],
            "right",
        )
        PageCount = (len(Collection.Cups) + PageSize - 1) // PageSize
        Self.Page = max(0, min(PageCount - 1, Self.Page))
        for Index, Cup in enumerate(
            Collection.Cups[Self.Page * PageSize : (Self.Page + 1) * PageSize]
        ):
            Skin, Name, Rarity, Ignored, Color = Cup
            X, Y = (-306, 0, 306)[Index % 3], 96 if Index < 3 else -66
            Owned = Skin in G.Profile["owned"]
            Active = G.Profile["equipped"] == Skin
            Hidden = Rarity == "Mythic" and not Owned
            Frame(
                Self.Views,
                X - 132,
                Y - 72,
                X + 132,
                Y + 72,
                "#202c39",
                Color if Active else "#526071",
            )
            Self.Views.Rectangle(X - 130, Y + 68, X + 130, Y + 71, Color)
            Self.Views.WriteFitted(
                G.MenuText,
                X - 112,
                Y + 45,
                "Unseen cup" if Hidden else Name,
                224,
                15,
                Color,
            )
            Self.Views.Write(
                G.MenuText, X, Y + 25, "???" if Hidden else Rarity, 10, Colors["muted"]
            )
            if Hidden:
                G.Screen.getcanvas().create_image(
                    X, -(Y - 14), image=G.Assets["secret"], tags=("scene",)
                )
            else:
                PlaceSkin(Self.Views, Skin, 1, X, Y - 14, Anchor="center")
            if Owned:
                Self.Views.Write(
                    G.MenuText,
                    X,
                    Y - 67,
                    "Equipped" if Active else "Equip cup",
                    10,
                    Color,
                )
                G.Buttons["equip:" + Skin] = (X - 132, Y - 72, X + 132, Y + 72)
            else:
                G.Screen.getcanvas().create_image(
                    X,
                    -(Y - 30),
                    image=G.Assets["lock_badge"],
                    tags=("scene", "cup_lock", "lock:" + Skin),
                )
        if Self.Page:
            Self.Views.DrawButton("page:previous", "Previous", -145, -162, 110)
        if Self.Page + 1 < PageCount:
            Self.Views.DrawButton("page:next", "Next", 145, -162, 110)
        Self.Views.Write(
            G.MenuText, 0, -167, f"{Self.Page+1} of {PageCount}", 11, Colors["muted"]
        )
        Self.Views.WriteFitted(
            G.MenuText,
            -440,
            -215,
            Notice or "Ten draws boost every non-Normal rarity. See Odds.",
            880,
            12,
            Colors["white"],
        )
        EnoughBatch = G.Profile["tickets"] >= Collection.BatchCost
        Self.Views.DrawButton(
            "draw",
            "1 draw: 3 tickets",
            -336,
            -254,
            208,
            G.Profile["tickets"] >= 3 and not EnoughBatch,
        )
        Self.Views.DrawButton(
            "draw10", "10 draws: 30 tickets", -101, -254, 232, EnoughBatch
        )
        Self.Views.DrawButton("odds", "Odds", 111, -254, 142)
        Self.Views.DrawButton("back", "Back", 340, -254, 202)
        Self.Views.DrawFooter()
        G.Screen.update()
        return True

    def ShowOdds(Self):
        if not Self.Unlocked():
            return
        G = Self.Session
        Self.CabinetShell("odds")
        Frame(Self.Views, -430, -154, 430, 224, "#1b2430")
        Self.Views.Write(G.MenuText, -394, 182, "Draw odds", 24, Colors["gold"], "left")
        Self.Views.Write(G.MenuText, 134, 144, "Single", 12, Colors["muted"])
        Self.Views.Write(G.MenuText, 326, 144, "Ten-draw", 12, Colors["gold"])
        for Index, (Rarity, Single, Batch, Color) in enumerate(Collection.Rarities):
            Y = 105 - Index * 40
            Self.Views.Write(G.MenuText, -394, Y, Rarity, 14, Color, "left")
            Self.Views.Write(
                G.MenuText, 134, Y, f"{Single/100:g}%", 14, Colors["white"]
            )
            Self.Views.Write(G.MenuText, 326, Y, f"{Batch/100:g}%", 14, Colors["gold"])
        Self.Views.SetMessage(
            "Every cup is cosmetic",
            "Odds apply to each pull. Three designs share each rarity. Duplicates return 1 ticket.",
        )
        Self.Views.DrawButton("cabinet", "Back", 340, -260, 202, True)
        G.Screen.update()

    def DrawCup(Self, Count=1):
        G = Self.Session
        if G.State != "cabinet":
            return
        Results, Error = Collection.DrawMany(G.ProfilePath, G.Profile, Count)
        if Results is None:
            Self.ShowCabinet(Error)
            return
        Self.Batch = Results if Count == 10 else []
        G.PendingCup, G.DrawStatus = Results[0]
        G.DrawFrame = 0
        Self.DuplicatePending = False
        Self.CabinetShell("gacha_opening")
        Self.Views.SetMessage(
            "Opening ten cups" if Count == 10 else "Opening your gift"
        )
        Self.AnimateDraw()

    def AnimateDraw(Self):
        G = Self.Session
        G.DrawFrame += 1
        if G.DrawFrame >= DrawFrames:
            Self.RevealDraw()
            return
        Canvas = G.Screen.getcanvas()
        Canvas.delete("draw_fx")
        G.ArtLayer = "draw_fx"
        Frame(Self.Views, -96, -60, 96, 136, "#202c39", Colors["gold"])
        Canvas.create_image(0, -32, image=G.Assets["draw_mystery"], tags=("draw_fx",))
        if G.DrawStatus == "new":
            Progress = G.DrawFrame
            Phase = (
                0
                if Progress < 28
                else 1 if Progress < 40 else 2 if Progress < 56 else 3
            )
            Shake = (-2, 0, 2, 0)[Progress // 3 % 4] if Phase == 0 else 0
            Canvas.create_image(
                Shake,
                -4,
                image=G.Assets["unlock_frames"][Phase],
                tags=("draw_fx", "unlock_lock"),
            )
            if Progress == LockOpenFrame:
                G.PlayTone("unlock")
        for I in range(8):
            X, Y = -160 + (I * 43) % 320, -60 + (I * 31 + G.DrawFrame * 3) % 180
            Self.Views.Rectangle(X, Y, X + 3, Y + 3, Colors["gold"])
        G.ArtLayer = "scene"

    def RevealDraw(Self):
        if Self.Batch:
            Self.ShowBatchResults()
            return
        G = Self.Session
        Skin, Status = G.PendingCup, G.DrawStatus
        Self.DuplicatePending = Status == "duplicate"
        Self.CabinetShell("gacha_reveal")
        Ignored, Name, Rarity, Ignored, Color = next(
            Cup for Cup in Collection.Cups if Cup[0] == Skin
        )
        Self.Views.Write(G.MenuText, 0, 161, Rarity, 18, Color)
        PlaceSkin(
            Self.Views, Skin, 3, 0, 60, Anchor="center", ExtraTags=("reveal_cup",)
        )
        Self.Views.Write(G.MenuText, 0, -70, Name, 22, Color)
        Self.Views.SetMessage(
            "Duplicate cup" if Self.DuplicatePending else "Cup unlocked",
            (
                "Already owned. Next converts it to 1 ticket."
                if Self.DuplicatePending
                else "Equip it for your next game."
            ),
        )
        if Self.DuplicatePending:
            Self.Views.DrawButton("convert_duplicate", "Next", 340, -260, 202, True)
        else:
            Self.Views.DrawButton("equip:" + Skin, "Equip", 80, -260, 202, True)
            Self.Views.DrawButton("cabinet", "Keep browsing", 340, -260, 202)
        G.PlayTone("win")
        G.Screen.update()

    def ConvertDuplicate(Self):
        G = Self.Session
        if G.State != "gacha_reveal" or not Self.DuplicatePending:
            return
        Self.DuplicatePending = False
        G.Screen.getcanvas().delete("reveal_cup")
        G.Buttons = {}
        Self.Views.SetMessage("Duplicate converted", "+1 ticket added to your cabinet.")
        Self.Views.DrawButton("cabinet", "Keep browsing", 340, -260, 202, True)
        G.Effects.Duplicate(G.PendingCup)
        G.PlayTone("ticket")
        G.Screen.update()

    def ShowBatchResults(Self, Converted=False):
        G = Self.Session
        Self.CabinetShell("batch_reveal")
        Self.BatchConverting = False
        Self.BatchPending = not Converted and any(
            Status == "duplicate" for Ignored, Status in Self.Batch
        )
        Self.BatchArt = {}
        Self.Views.Write(
            G.MenuText, -438, 201, "Ten cups unwrapped", 21, Colors["gold"], "left"
        )
        for Index, (Skin, Status) in enumerate(Self.Batch):
            Ignored, Name, Rarity, Ignored, Color = next(
                Cup for Cup in Collection.Cups if Cup[0] == Skin
            )
            X, Y = (-372, -186, 0, 186, 372)[Index % 5], 86 if Index < 5 else -70
            Frame(
                Self.Views,
                X - 82,
                Y - 72,
                X + 82,
                Y + 72,
                "#202c39",
                Color if Status == "new" else "#526071",
            )
            Self.Views.WriteFitted(G.MenuText, X - 69, Y + 46, Name, 138, 11, Color)
            Self.Views.Write(G.MenuText, X, Y + 27, Rarity, 9, Colors["muted"])
            if Converted and Status == "duplicate":
                Item = G.Screen.getcanvas().create_image(
                    X, -(Y - 12), image=G.Assets["ticket_reward"], tags=("scene",)
                )
            else:
                Item = PlaceSkin(Self.Views, Skin, 1, X, Y - 12, Anchor="center")
            Self.BatchArt[Index] = Item
            Label = (
                "+1 ticket"
                if Converted and Status == "duplicate"
                else "Duplicate" if Status == "duplicate" else "New cup"
            )
            Self.Views.Write(
                G.MenuText,
                X,
                Y - 66,
                Label,
                10,
                "#a3d4bb" if Label != "Duplicate" else Colors["muted"],
            )
            if not Self.BatchPending and not (Converted and Status == "duplicate"):
                G.Buttons["equip:" + Skin] = (X - 82, Y - 72, X + 82, Y + 72)
        Duplicates = sum(Status == "duplicate" for Ignored, Status in Self.Batch)
        Self.Views.SetMessage(
            (
                "Duplicates become tickets"
                if Self.BatchPending
                else "Your ten-draw results"
            ),
            (
                f"Next converts {Duplicates} duplicates into {Duplicates} tickets."
                if Self.BatchPending
                else f"{10-Duplicates} new cups. {Duplicates} tickets returned."
            ),
        )
        G.ArtLayer = "batch_action"
        Self.Views.DrawButton(
            "batch_next", "Next" if Self.BatchPending else "Done", 340, -260, 202, True
        )
        G.ArtLayer = "scene"
        G.PlayTone("win" if not Converted else "ticket")
        G.Screen.update()

    def NextBatch(Self):
        if Self.BatchConverting:
            return
        if not Self.BatchPending:
            Self.ShowCabinet()
            return
        Self.BatchConverting = True
        Self.BatchFrame = 0
        Self.Session.Buttons = {}
        Canvas = Self.Session.Screen.getcanvas()
        Canvas.delete("batch_action")
        for Index, (Ignored, Status) in enumerate(Self.Batch):
            if Status == "duplicate":
                Canvas.dtag(Self.BatchArt[Index], "animated_skin")
        Self.Views.SetMessage("Converting duplicates", "")

    def AnimateBatch(Self):
        if not Self.BatchConverting:
            return
        Self.BatchFrame += 1
        G = Self.Session
        for Index, (Skin, Status) in enumerate(Self.Batch):
            if Status != "duplicate":
                continue
            Image = (
                G.Assets["skins"][Skin][1 if Self.BatchFrame < 15 else 0]
                if Self.BatchFrame < 30
                else G.Assets["ticket_reward"]
            )
            G.Screen.getcanvas().itemconfigure(Self.BatchArt[Index], image=Image)
        if Self.BatchFrame >= 45:
            Self.ShowBatchResults(Converted=True)
