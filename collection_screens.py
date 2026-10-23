"""Cup cabinet screens, kept separate from round gameplay."""

import cup_collection as collection
from party_art import frame, place_image
from game_config import COLORS

DRAW_FRAMES = 72
LOCK_OPEN_FRAME = 28


class CupCabinet:

    def __init__(self, session, views):
        self.session = session
        self.views = views
        self.duplicate_pending = False

    def cabinet_shell(self, state):
        self.session.state = state
        self.session.clear_cups()
        self.views.draw_background()
        if state in ("gacha_opening", "gacha_reveal"):
            place_image(self.views, self.session.assets["cabinet_reveal"], -470, 236)
        self.session.menu_text.clear()
        self.session.hud_text.clear()
        self.session.message.clear()
        self.session.buttons = {}

    def show_cabinet(self, notice=""):
        self.session.update_window_icon()
        self.cabinet_shell("cabinet")
        frame(self.views, -470, 174, 470, 236, "#211b2c")
        self.views.write(
            self.session.menu_text, -440, 202, "Cup cabinet", 18, COLORS["gold"], "left"
        )
        self.views.write(
            self.session.menu_text,
            440,
            204,
            f"Tickets  {self.session.profile['tickets']}",
            16,
            COLORS["white"],
            "right",
        )
        place_image(self.views, self.session.assets["icons"]["ticket"], 292, 224)
        self.views.write(
            self.session.menu_text,
            440,
            184,
            "Earn one for each new win.",
            10,
            COLORS["muted"],
            "right",
        )
        for index, (skin, name, rarity, weight, color) in enumerate(collection.CUPS):
            x = (-306, 0, 306)[index % 3]
            y = 96 if index < 3 else -66
            owned = skin in self.session.profile["owned"]
            active = self.session.profile["equipped"] == skin
            frame(
                self.views,
                x - 132,
                y - 72,
                x + 132,
                y + 72,
                "#302539",
                color if active else "#715166",
            )
            hidden = skin == "mythic" and not owned
            self.views.write(
                self.session.menu_text,
                x,
                y + 47,
                "Unseen cup" if hidden else name,
                13,
                color,
            )
            self.views.write(
                self.session.menu_text,
                x,
                y + 27,
                "???" if hidden else rarity,
                10,
                COLORS["muted"],
            )
            self.session.static.shape("secret_preview" if hidden else skin + "_preview")
            self.session.static.goto(x, y - 14)
            self.session.static.stamp()
            if owned:
                self.views.write(
                    self.session.menu_text, x, y - 67,
                    "Equipped" if active else "Click to equip", 10, color,
                )
            else:
                self.session.screen.getcanvas().create_image(
                    x, -(y - 30), image=self.session.assets["lock_badge"],
                    tags=("scene", "cup_lock", f"lock:{skin}"),
                )
            if owned:
                self.session.buttons["equip:" + skin] = (
                    x - 132,
                    y - 72,
                    x + 132,
                    y + 72,
                )
        self.views.write(
            self.session.menu_text,
            -440,
            -215,
            notice or "A little surprise from the party.",
            13,
            COLORS["white"],
            "left",
        )
        self.views.draw_button(
            "draw",
            "Draw for 3 tickets",
            -290,
            -254,
            284,
            self.session.profile["tickets"] >= collection.DRAW_COST,
        )
        self.views.draw_button("odds", "Odds", 26, -254, 174)
        self.views.draw_button("back", "Back", 322, -254, 202)
        self.views.draw_footer()
        self.session.screen.update()

    def show_odds(self):
        self.cabinet_shell("odds")
        frame(self.views, -310, -155, 310, 224, "#241d30")
        self.views.write(
            self.session.menu_text,
            -277,
            179,
            "Every draw, every chance",
            21,
            COLORS["gold"],
            "left",
        )
        for index, (_, name, rarity, weight, color) in enumerate(collection.CUPS):
            y = 129 - index * 41
            self.views.write(self.session.menu_text, -277, y, rarity, 14, color, "left")
            self.views.write(
                self.session.menu_text,
                275,
                y,
                f"{weight/100:g}%",
                14,
                COLORS["white"],
                "right",
            )
        self.views.set_message(
            "Three tickets per draw", "Duplicates return one ticket. Cups are cosmetic."
        )
        self.views.draw_button("cabinet", "Back", 340, -260, 202, True)
        self.session.screen.update()

    def draw_cup(self):
        if self.session.state != "cabinet":
            return
        skin, status = collection.draw(self.session.profile_path, self.session.profile)
        if skin is None:
            self.show_cabinet(status)
            return
        self.session.pending_cup = skin
        self.session.draw_status = status
        self.session.draw_frame = 0
        self.cabinet_shell("gacha_opening")
        self.views.set_message("Opening your gift", "")
        self.animate_draw()

    def animate_draw(self):
        self.session.draw_frame += 1
        if self.session.draw_frame >= DRAW_FRAMES:
            self.reveal_draw()
            return
        self.session.screen.getcanvas().delete("draw_fx")
        self.session.art_layer = "draw_fx"
        center = 32
        frame(self.views, -96, center - 92, 96, center + 104, "#302539", "#f2bf68")
        canvas = self.session.screen.getcanvas()
        canvas.create_image(0, -center, image=self.session.assets["draw_mystery"], tags=("draw_fx",))
        if self.session.draw_status == "new":
            progress = self.session.draw_frame
            if progress < LOCK_OPEN_FRAME:
                phase = 0
            elif progress < 40:
                phase = 1
            elif progress < 56:
                phase = 2
            else:
                phase = 3
            shake = (-2, 0, 2, 0)[progress // 3 % 4] if phase == 0 else 0
            canvas.create_image(
                shake, -center + 28, image=self.session.assets["unlock_frames"][phase],
                tags=("draw_fx", "unlock_lock"),
            )
            if progress == LOCK_OPEN_FRAME:
                self.session.play_tone("unlock")
        for i in range(8):
            x = -160 + (i * 43) % 320
            y = -60 + (i * 31 + self.session.draw_frame * 3) % 180
            self.views.rectangle(x, y, x + 3, y + 3, "#f2bf68")
        self.session.art_layer = "scene"

    def reveal_draw(self):
        skin, status = self.session.pending_cup, self.session.draw_status
        self.duplicate_pending = status == "duplicate"
        self.cabinet_shell("gacha_reveal")
        _, name, rarity, _, color = next(
            cup for cup in collection.CUPS if cup[0] == skin
        )
        self.views.write(self.session.menu_text, 0, 161, rarity, 18, color)
        self.session.static.shape(skin + "_hero")
        self.session.static.goto(0, 60)
        self.session.static.stamp()
        self.views.write(self.session.menu_text, 0, -70, name, 22, color)
        self.views.set_message(
            "Duplicate cup" if status == "duplicate" else "Cup unlocked",
            (
                "You already own this cup. Next converts it to 1 ticket."
                if status == "duplicate"
                else "Equip it for your next game."
            ),
        )
        if self.duplicate_pending:
            self.views.draw_button("convert_duplicate", "Next", 340, -260, 202, True)
        else:
            self.views.draw_button("equip:" + skin, "Equip", 80, -260, 202, True)
            self.views.draw_button("cabinet", "Keep browsing", 340, -260, 202)
        self.session.play_tone("win")
        self.session.screen.update()

    def convert_duplicate(self):
        """Present the already-saved refund only after the player acknowledges it."""
        if self.session.state != "gacha_reveal" or not self.duplicate_pending:
            return
        self.duplicate_pending = False
        self.session.static.clearstamps()
        self.session.buttons = {}
        self.views.set_message("Duplicate converted", "+1 ticket added to your cabinet.")
        self.views.draw_button("cabinet", "Keep browsing", 340, -260, 202, True)
        self.session.effects.duplicate(self.session.pending_cup)
        self.session.screen.update()
