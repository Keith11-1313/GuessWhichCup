"""Menu, story, HUD and drawing helpers for the shared Game session."""

from game_config import COLORS, DIFFICULTIES, RESULT_BUTTON_BOUNDS, STORY_LEVELS
from party_art import scenery, frame, draw_title, portrait, place_image
from party_story import CHAPTERS, SCENES, LOCATION_NAMES, location

WHITE = COLORS["white"]
MUTED = COLORS["muted"]
GOLD = COLORS["gold"]


class GameScreens:

    def __init__(self, session):
        self.session = session

    def write(self, pen, x, y, text, size=16, color=WHITE, align="center"):
        pen.color(color)
        pen.goto(x, y)
        pen.write(
            text,
            align=align,
            font=("Segoe UI", size, "bold" if size >= 16 else "normal"),
        )

    def rectangle(self, x1, y1, x2, y2, fill, outline=None):
        self.session.screen.getcanvas().create_rectangle(
            x1,
            -y2,
            x2,
            -y1,
            fill=fill,
            outline=outline or fill,
            width=0 if outline is None else 1,
            tags=(self.session.art_layer,),
        )

    def draw_background(self, view="game"):
        self.session.static.clear()
        canvas = self.session.screen.getcanvas()
        for layer in ("scene", "hud_art", "choice_art", "message_art", "draw_fx"):
            canvas.delete(layer)
        self.session.art_layer = "scene"
        scenery(self, menu=view == "menu")
        draw_title(self, -466, 306)
        self.write(self.session.static, 467, 288, "Lantern House", 16, GOLD, "right")
        self.write(
            self.session.static, 467, 266, "A night to remember", 10, MUTED, "right"
        )
        self.rectangle(-470, 255, 470, 257, "#765465")
        if view != "menu":
            frame(self, -470, -292, 470, -184, "#241d30")
        self.draw_footer()
        # Pooled cup sprites already exist when this new scenery is painted.
        # Keep the scenery behind them; movement alone does not raise images.
        canvas.tag_lower("scene")

    def draw_button(self, name, text, x, y, width, active=False):
        fill = GOLD if active else "#342a41"
        frame(
            self,
            x - width / 2,
            y - 22,
            x + width / 2,
            y + 22,
            fill,
            "#ffe0a0" if active else "#715166",
        )
        self.write(
            self.session.menu_text, x, y - 8, text, 12, "#2b2030" if active else WHITE
        )
        self.session.buttons[name] = (x - width / 2, y - 22, x + width / 2, y + 22)

    def show_how_to_play(self):
        self.session.state = "how_to_play"
        self.session.clear_cups()
        self.draw_background()
        self.session.menu_text.clear()
        self.session.hud_text.clear()
        self.session.message.clear()
        self.session.buttons = {}
        frame(self, -365, -156, 365, 224, "#241d30")
        self.write(
            self.session.menu_text, -330, 177, "A little party trick", 24, GOLD, "left"
        )
        self.write(
            self.session.menu_text,
            -330,
            140,
            "Three moments. One spark to keep safe.",
            12,
            MUTED,
            "left",
        )
        for y, title, detail in (
            (80, "Remember", "Look for the spark underneath the lifted cup."),
            (8, "Follow", "Track that cup as the table shuffles."),
            (-64, "Choose", "Click its cup or press the matching number."),
        ):
            self.rectangle(-330, y - 16, -326, y + 20, GOLD)
            self.write(self.session.menu_text, -306, y, title, 16, WHITE, "left")
            self.write(self.session.menu_text, -306, y - 26, detail, 12, MUTED, "left")
        self.write(
            self.session.menu_text,
            -330,
            -132,
            "A correct pick earns points. A mistake costs one life.",
            11,
            MUTED,
            "left",
        )
        self.set_message(
            "Take your time",
            "P pauses the round. Sound is optional. Results wait for you.",
        )
        self.draw_button("back", "Back to the party", 312, -268, 242, True)
        self.session.screen.update()

    def show_menu(self):
        self.session.state = "menu"
        self.session.clear_cups()
        self.draw_background(view="menu")
        self.session.menu_text.clear()
        self.session.hud_text.clear()
        self.session.message.clear()
        self.session.buttons = {}
        frame(self, -8, -175, 470, 236, "#241d30")
        self.write(self.session.menu_text, 24, 198, "Your invitation", 22, GOLD, "left")
        self.write(
            self.session.menu_text,
            24,
            167,
            "A hidden spark. A table full of friends.",
            12,
            WHITE,
            "left",
        )

        self.rectangle(24, 125, 435, 126, "#533f53")
        self.write(
            self.session.menu_text, 24, 99, "Choose your evening", 12, MUTED, "left"
        )
        self.draw_button(
            "mode:Story", "Story", 125, 65, 190, self.session.mode == "Story"
        )
        self.draw_button(
            "mode:Endless", "Endless", 335, 65, 190, self.session.mode == "Endless"
        )
        mode_detail = (
            "Ten chapters with Mira, Theo & Jun."
            if self.session.mode == "Story"
            else "The afterparty. Keep your streak alive."
        )
        self.write(self.session.menu_text, 24, 23, mode_detail, 11, MUTED, "left")
        self.write(self.session.menu_text, 24, -13, "Set the pace", 12, MUTED, "left")
        for x, name in ((91, "Easy"), (231, "Normal"), (371, "Hard")):
            self.draw_button(
                "diff:" + name, name, x, -49, 122, self.session.difficulty == name
            )
        lives = DIFFICULTIES[self.session.difficulty]["lives"]
        self.write(
            self.session.menu_text,
            24,
            -94,
            f"{lives} lives  /  Best score  {self.session.best_score():,}",
            11,
            MUTED,
            "left",
        )
        self.draw_button("start", "Join the party", 152, -137, 244, True)
        self.draw_button("howto", "How to play", 359, -137, 142)
        frame(self, -470, -292, 470, -197, "#211b2c")
        self.write(self.session.menu_text, -438, -230, "Your cups", 16, WHITE, "left")
        self.write(
            self.session.menu_text,
            -438,
            -259,
            f"{len(self.session.profile['owned'])} / 6 collected   /   {self.session.profile['tickets']} tickets",
            12,
            MUTED,
            "left",
        )
        self.draw_button("cabinet", "Cup cabinet", 321, -245, 228)
        self.session.screen.update()

    def draw_hud(self):
        self.session.hud_text.clear()
        self.session.screen.getcanvas().delete("hud_art")
        self.session.art_layer = "hud_art"
        frame(self, -470, 174, 470, 236, "#211b2c")
        self.rectangle(-166, 186, -165, 223, "#533f53")
        self.rectangle(142, 186, 143, 223, "#533f53")
        self.write(
            self.session.hud_text,
            -445,
            209,
            f"{self.session.mode}  /  {self.session.difficulty}",
            12,
            WHITE,
            "left",
        )
        total_lives = DIFFICULTIES[self.session.difficulty]["lives"]
        for index in range(total_lives):
            name = "heart_full" if index < self.session.lives else "heart_empty"
            place_image(self, self.session.assets[name], -445 + index * 29, 201)
        title = (
            f"Chapter {self.session.level} of {STORY_LEVELS}"
            if self.session.mode == "Story"
            else f"Round {self.session.level}  /  Combo {self.session.combo}"
        )
        self.write(self.session.hud_text, -12, 207, title, 13, GOLD)
        chapter = LOCATION_NAMES[location(self.session.mode, self.session.level)]
        self.write(self.session.hud_text, -12, 185, chapter, 10, MUTED)
        self.write(
            self.session.hud_text,
            443,
            207,
            f"Score  {self.session.score:,}",
            13,
            GOLD,
            "right",
        )
        self.write(
            self.session.hud_text,
            443,
            185,
            f"Best  {self.session.best_score():,}",
            10,
            MUTED,
            "right",
        )
        self.session.art_layer = "scene"

    def set_message(self, text, detail="", color=WHITE):
        self.session.message.clear()
        self.session.screen.getcanvas().delete("message_art")
        self.write(self.session.message, -442, -222, text, 18, color, "left")
        if self.session.state in ("result", "retry", "over", "victory") and (
            self.session.save_failed or self.session.reward_failed
        ):
            detail = "Save failed. Check folder permissions."
        if detail:
            self.write(self.session.message, -442, -253, detail, 12, MUTED, "left")
        if self.session.state in ("result", "retry", "over", "victory"):
            label = (
                "Next"
                if self.session.state == "result"
                else "Retry" if self.session.state == "retry" else "Play again"
            )
            self.session.art_layer = "message_art"
            frame(self, *RESULT_BUTTON_BOUNDS, GOLD, "#ffe0a0")
            self.session.art_layer = "scene"
            self.write(self.session.message, 340, -274, label, 12, "#2b2030")
        self.draw_footer()

    def draw_footer(self):
        self.session.footer.clear()
        if self.session.state == "menu":
            left, right = "Enter  Play    H  Help", "Esc  Quit"
        elif self.session.state == "story":
            left, right = (
                "Enter  Continue" if self.session.story_page == 0 else "Enter  Play"
            ), "M  Menu"
        elif self.session.state == "cabinet":
            left, right = "Enter  Draw", "Esc  Back"
        elif self.session.state == "gacha_opening":
            left, right = "Enter  Reveal", "Esc  Back"
        elif self.session.state in ("reveal", "shuffle", "select", "paused"):
            left, right = (
                "P  Resume" if self.session.state == "paused" else "P  Pause    S Sound"
            ), "M  Menu"
        elif self.session.state in ("result", "retry", "over", "victory"):
            left, right = "Enter  Continue", "M  Menu"
        else:
            left, right = "", "Esc  Back"
        self.write(self.session.footer, -464, -327, left, 10, MUTED, "left")
        self.write(self.session.footer, 464, -327, right, 10, MUTED, "right")

    def show_story(self):
        self.session.state = "story"
        self.session.clear_cups()
        self.draw_background()
        self.session.menu_text.clear()
        self.session.hud_text.clear()
        self.session.message.clear()
        self.session.buttons = {}
        setting, speaker, first, second = SCENES[self.session.level - 1]
        frame(self, -470, 174, 470, 236, "#211b2c")
        self.write(
            self.session.menu_text,
            -440,
            197,
            f"Chapter {self.session.level}",
            14,
            GOLD,
            "left",
        )
        self.write(
            self.session.menu_text,
            440,
            197,
            LOCATION_NAMES[setting],
            14,
            WHITE,
            "right",
        )
        self.write(
            self.session.menu_text,
            0,
            121,
            CHAPTERS[self.session.level - 1][0],
            24,
            WHITE,
        )
        portrait(self, speaker, -53, -97)
        self.write(self.session.message, -442, -220, speaker, 16, GOLD, "left")
        self.write(
            self.session.message,
            -442,
            -252,
            (first, second)[self.session.story_page],
            13,
            WHITE,
            "left",
        )
        self.draw_button(
            "story_next",
            "Continue" if self.session.story_page == 0 else "Play",
            340,
            -260,
            202,
            True,
        )
        self.draw_footer()
        self.session.screen.update()
