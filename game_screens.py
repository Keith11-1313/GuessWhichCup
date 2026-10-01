"""Menu, story, HUD and drawing helpers for the shared Game session."""

from game_config import COLORS, DIFFICULTIES, RESULT_BUTTON_BOUNDS, STORY_LEVELS
from party_art import scenery, frame, pixel_title, guest
from party_story import CHAPTERS, SCENES, LOCATION_NAMES, location

WHITE = COLORS["white"]
MUTED = COLORS["muted"]
GOLD = COLORS["gold"]


class GameScreens:
    def write(self, pen, x, y, text, size=16, color=WHITE, align="center"):
        pen.color(color)
        pen.goto(x, y)
        pen.write(
            text,
            align=align,
            font=("Segoe UI", size, "bold" if size >= 16 else "normal"),
        )

    def rectangle(self, x1, y1, x2, y2, fill, outline=None):
        self.screen.getcanvas().create_rectangle(
            x1,
            -y2,
            x2,
            -y1,
            fill=fill,
            outline=outline or fill,
            width=0 if outline is None else 1,
            tags=(getattr(self, "art_layer", "scene"),),
        )

    def draw_background(self, view="game"):
        self.static.clear()
        canvas = self.screen.getcanvas()
        for layer in ("scene", "hud_art", "choice_art", "message_art", "draw_fx"):
            canvas.delete(layer)
        self.art_layer = "scene"
        scenery(self, menu=view == "menu")
        pixel_title(self, "GUESS WHICH CUP", -466, 306, 4)
        self.write(self.static, 467, 288, "Lantern House", 16, GOLD, "right")
        self.write(self.static, 467, 266, "A night to remember", 10, MUTED, "right")
        self.rectangle(-470, 255, 470, 257, "#765465")
        if view != "menu":
            frame(self, -470, -292, 470, -184, "#241d30")
        self.draw_footer()

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
        self.write(self.menu_text, x, y - 8, text, 12, "#2b2030" if active else WHITE)
        self.buttons[name] = (x - width / 2, y - 22, x + width / 2, y + 22)

    def show_how_to_play(self):
        self.state = "how_to_play"
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear()
        self.hud_text.clear()
        self.message.clear()
        self.buttons = {}
        frame(self, -365, -156, 365, 224, "#241d30")
        self.write(self.menu_text, -330, 177, "A little party trick", 24, GOLD, "left")
        self.write(
            self.menu_text,
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
            self.write(self.menu_text, -306, y, title, 16, WHITE, "left")
            self.write(self.menu_text, -306, y - 26, detail, 12, MUTED, "left")
        self.write(
            self.menu_text,
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
        self.screen.update()

    def show_menu(self):
        self.state = "menu"
        self.clear_cups()
        self.draw_background(view="menu")
        self.menu_text.clear()
        self.hud_text.clear()
        self.message.clear()
        self.buttons = {}
        frame(self, -8, -175, 470, 236, "#241d30")
        self.write(self.menu_text, 24, 198, "Your invitation", 22, GOLD, "left")
        self.write(
            self.menu_text,
            24,
            167,
            "A hidden spark. A table full of friends.",
            12,
            WHITE,
            "left",
        )

        self.rectangle(24, 125, 435, 126, "#533f53")
        self.write(self.menu_text, 24, 99, "Choose your evening", 12, MUTED, "left")
        self.draw_button("mode:Story", "Story", 125, 65, 190, self.mode == "Story")
        self.draw_button(
            "mode:Endless", "Endless", 335, 65, 190, self.mode == "Endless"
        )
        mode_detail = (
            "Ten chapters with Mira, Theo & Jun."
            if self.mode == "Story"
            else "The afterparty. Keep your streak alive."
        )
        self.write(self.menu_text, 24, 23, mode_detail, 11, MUTED, "left")
        self.write(self.menu_text, 24, -13, "Set the pace", 12, MUTED, "left")
        for x, name in ((91, "Easy"), (231, "Normal"), (371, "Hard")):
            self.draw_button("diff:" + name, name, x, -49, 122, self.difficulty == name)
        lives = DIFFICULTIES[self.difficulty]["lives"]
        self.write(
            self.menu_text,
            24,
            -94,
            f"{lives} lives  /  Best score  {self.best_score():,}",
            11,
            MUTED,
            "left",
        )
        self.draw_button("start", "Join the party", 152, -137, 244, True)
        self.draw_button("howto", "How to play", 359, -137, 142)
        frame(self, -470, -292, 470, -197, "#211b2c")
        self.write(self.menu_text, -438, -230, "Your cups", 16, WHITE, "left")
        self.write(
            self.menu_text,
            -438,
            -259,
            f"{len(self.profile['owned'])} / 6 collected   /   {self.profile['tickets']} tickets",
            12,
            MUTED,
            "left",
        )
        self.draw_button("cabinet", "Cup cabinet", 321, -245, 228)
        self.screen.update()

    def draw_hud(self):
        self.hud_text.clear()
        self.screen.getcanvas().delete("hud_art")
        self.art_layer = "hud_art"
        frame(self, -470, 174, 470, 236, "#211b2c")
        self.rectangle(-166, 186, -165, 223, "#533f53")
        self.rectangle(142, 186, 143, 223, "#533f53")
        self.write(
            self.hud_text,
            -445,
            209,
            f"{self.mode}  /  {self.difficulty}",
            12,
            WHITE,
            "left",
        )
        self.write(
            self.hud_text,
            -445,
            185,
            f"Lives  {self.lives}",
            11,
            COLORS["danger"],
            "left",
        )
        title = (
            f"Chapter {self.level} of {STORY_LEVELS}"
            if self.mode == "Story"
            else f"Round {self.level}  /  Combo {self.combo}"
        )
        self.write(self.hud_text, -12, 207, title, 13, GOLD)
        chapter = LOCATION_NAMES[location(self.mode, self.level)]
        self.write(self.hud_text, -12, 185, chapter, 10, MUTED)
        self.write(self.hud_text, 443, 207, f"Score  {self.score:,}", 13, GOLD, "right")
        self.write(
            self.hud_text, 443, 185, f"Best  {self.best_score():,}", 10, MUTED, "right"
        )
        self.art_layer = "scene"

    def set_message(self, text, detail="", color=WHITE):
        self.message.clear()
        self.screen.getcanvas().delete("message_art")
        self.write(self.message, -442, -222, text, 18, color, "left")
        if self.state in ("result", "retry", "over", "victory") and (
            getattr(self, "save_failed", False) or self.reward_failed
        ):
            detail = "Save failed. Check folder permissions."
        if detail:
            self.write(self.message, -442, -253, detail, 12, MUTED, "left")
        if self.state in ("result", "retry", "over", "victory"):
            label = (
                "Next"
                if self.state == "result"
                else "Retry" if self.state == "retry" else "Play again"
            )
            self.art_layer = "message_art"
            frame(self, *RESULT_BUTTON_BOUNDS, GOLD, "#ffe0a0")
            self.art_layer = "scene"
            self.write(self.message, 340, -274, label, 12, "#2b2030")
        self.draw_footer()

    def draw_footer(self):
        self.footer.clear()
        if self.state == "menu":
            left, right = "Enter  Play    H  Help", "Esc  Quit"
        elif self.state == "story":
            left, right = (
                "Enter  Continue" if self.story_page == 0 else "Enter  Play"
            ), "M  Menu"
        elif self.state == "cabinet":
            left, right = "Enter  Draw", "Esc  Back"
        elif self.state == "gacha_opening":
            left, right = "Enter  Reveal", "Esc  Back"
        elif self.state in ("reveal", "shuffle", "select", "paused"):
            left, right = (
                "P  Resume" if self.state == "paused" else "P  Pause    S Sound"
            ), "M  Menu"
        elif self.state in ("result", "retry", "over", "victory"):
            left, right = "Enter  Continue", "M  Menu"
        else:
            left, right = "", "Esc  Back"
        self.write(self.footer, -464, -327, left, 10, MUTED, "left")
        self.write(self.footer, 464, -327, right, 10, MUTED, "right")

    def begin_chapter(self):
        if self.mode == "Story":
            self.story_page = 0
            self.show_story()
        else:
            self.start_level()

    def show_story(self):
        self.state = "story"
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear()
        self.hud_text.clear()
        self.message.clear()
        self.buttons = {}
        setting, speaker, first, second = SCENES[self.level - 1]
        frame(self, -470, 174, 470, 236, "#211b2c")
        self.write(self.menu_text, -440, 197, f"Chapter {self.level}", 14, GOLD, "left")
        self.write(
            self.menu_text, 440, 197, LOCATION_NAMES[setting], 14, WHITE, "right"
        )
        self.write(self.menu_text, 0, 121, CHAPTERS[self.level - 1][0], 24, WHITE)
        colors = {
            "Mira": ("#829d8c", "#36263b"),
            "Theo": ("#b47b90", "#b38361"),
            "Jun": ("#8c9bbc", "#272735"),
        }
        shirt, hair = colors[speaker]
        guest(self, -53, -97, shirt, hair, 6)
        self.write(self.message, -442, -220, speaker, 16, GOLD, "left")
        self.write(
            self.message,
            -442,
            -252,
            (first, second)[self.story_page],
            13,
            WHITE,
            "left",
        )
        self.draw_button(
            "story_next",
            "Continue" if self.story_page == 0 else "Play",
            340,
            -260,
            202,
            True,
        )
        self.draw_footer()
        self.screen.update()
