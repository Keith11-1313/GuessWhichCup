"""Menu, story, HUD and drawing helpers for the shared Game session."""

from game_config import COLORS, DIFFICULTIES, RESULT_BUTTON_BOUNDS, STORY_LEVELS
from tkinter import font
from game_theme import text_font, label_runs, label_width
from party_art import scenery, frame, draw_title, place_image
from party_story import CHAPTERS, LOCATION_NAMES, location

WHITE = COLORS["white"]
MUTED = COLORS["muted"]
GOLD = COLORS["gold"]


class GameScreens:

    def __init__(self, session):
        self.session = session

    def write(self, pen, x, y, text, size=16, color=WHITE, align="center"):
        pen.color(color)
        width = label_width(text, size, size >= 16)
        cursor = x - width / 2 if align == "center" else x - width if align == "right" else x
        for part, style in label_runs(text, size, size >= 16):
            pen.goto(cursor, y)
            pen.write(part, align="left", font=style)
            cursor += font.Font(font=style).measure(part)

    def canvas_label(self, x, y, text, size, color, tags):
        """Draw mixed-font labels from their left edge, vertically centered."""
        canvas = self.session.screen.getcanvas()
        for part, style in label_runs(text, size):
            canvas.create_text(x, y, text=part, anchor="w", font=style, fill=color, tags=tags)
            x += font.Font(font=style).measure(part)

    def write_fitted(self, pen, x, y, text, width, size=12, color=WHITE):
        """Measure the actual mixed-font label before placing it in a fixed area."""
        while size > 9 and label_width(text, size, size >= 16) > width:
            size -= 1
        self.write(pen, x, y, text, size, color, "left")

    def write_wrapped(self, pen, x, y, text, width, size=12, color=MUTED):
        """Wrap dialogue before its action button, preserving readable text."""
        measure = lambda text: label_width(text, size)
        lines = []
        line = ""
        for word in text.split():
            candidate = f"{line} {word}".strip()
            if line and measure(candidate) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
        for index, line in enumerate(lines):
            self.write(pen, x, y - index * 21, line, size, color, "left")

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
        self.session.effects.clear()
        self.session.static.clear()
        canvas = self.session.screen.getcanvas()
        for layer in ("scene", "hud_art", "choice_art", "message_art", "draw_fx", "pause_art"):
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
        icon_name = {
            "start": "play", "story_next": "play", "mode:Story": "book",
            "play_again": "play", "game_menu": "back", "resume": "play", "resume_run": "play",
            "new_game_setup": "play", "back_saved": "back", "save_menu": "back", "save_exit": "back", "convert_duplicate": "play",
            "mode:Endless": "endless", "howto": "help",
            "cabinet": "cup" if text == "Cup cabinet" else "back",
            "draw": "ticket", "odds": "odds", "back": "back",
        }.get(name)
        offset = 24 if icon_name else 0
        size = 12
        while size > 9 and label_width(text, size) + offset > width - 28:
            size -= 1
        text_width = label_width(text, size)
        left = x - (text_width + offset) / 2
        if icon_name:
            palette = "icons_dark" if active else "icons"
            place_image(self, self.session.assets[palette][icon_name], left, y + 8)
        self.canvas_label(left + offset, -y, text, size,
                          "#2b2030" if active else WHITE, (self.session.art_layer,))
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
            "Three moments. One lucky coin to keep safe.",
            12,
            MUTED,
            "left",
        )
        for y, title, detail in (
            (80, "Remember", "Look for the coin underneath the lifted cup."),
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
            "P pauses. Use [ and ] for music volume. S mutes sound.",
        )
        self.draw_button("back", "Back to the party", 312, -260, 242, True)
        self.session.screen.update()

    def show_menu(self, new_game=False):
        self.session.update_window_icon()
        self.session.state = "menu_setup" if new_game else "menu"
        self.session.clear_cups()
        self.draw_background(view="menu")
        self.session.menu_text.clear()
        self.session.hud_text.clear()
        self.session.message.clear()
        self.session.buttons = {}
        frame(self, -8, -175, 470, 236, "#241d30")
        if self.session.saved_run and not new_game:
            self.draw_saved_run_menu()
        else:
            self.draw_new_game_menu(new_game)
        frame(self, -470, -292, 470, -197, "#211b2c")
        place_image(self, self.session.assets["icons"]["cup"], -438, -210)
        self.write(self.session.menu_text, -412, -230, "Your cups", 16, WHITE, "left")
        self.write(
            self.session.menu_text,
            -438,
            -259,
            f"{len(self.session.profile['owned'])} of 6 collected",
            12,
            MUTED,
            "left",
        )
        place_image(self, self.session.assets["icons"]["ticket"], -210, -240)
        self.write(self.session.menu_text, -186, -259, f"{self.session.profile['tickets']} tickets", 12, MUTED, "left")
        self.draw_button("cabinet", "Cup cabinet", 321, -245, 228)
        self.session.screen.update()

    def draw_choice_card(self, name, title, detail, x, bottom, width, height, selected, hearts=0):
        """The entire card is clickable; a tick distinguishes selection from Start."""
        fill = "#383044" if selected else "#292233"
        edge = GOLD if selected else "#614b60"
        frame(self, x, bottom, x + width, bottom + height, fill, edge)
        if selected:
            self.rectangle(x + 2, bottom + 2, x + 5, bottom + height - 2, GOLD)
            canvas = self.session.screen.getcanvas()
            cx, cy = x + width - 19, -(bottom + height - 17)
            canvas.create_line(cx - 5, cy, cx - 1, cy + 4, cx + 6, cy - 5,
                               fill=GOLD, width=2, tags=(self.session.art_layer,))
        self.write_fitted(self.session.menu_text, x + 14, bottom + height - 31,
                          title, width - 55, 15, GOLD if selected else WHITE)
        if hearts:
            for index in range(hearts):
                place_image(self, self.session.assets["heart_full"], x + 10 + index * 22, bottom + 29)
        else:
            self.write_fitted(self.session.menu_text, x + 14, bottom + 17, detail, width - 28, 11, MUTED)
        self.session.buttons[name] = (x, bottom, x + width, bottom + height)

    def draw_new_game_menu(self, new_game):
        g, pen = self.session, self.session.menu_text
        self.write(pen, 24, 196, "New game", 24, GOLD, "left")
        self.write(pen, 24, 163, "Game mode", 12, MUTED, "left")
        for x, mode, detail in ((24, "Story", "10 story chapters"), (240, "Endless", "No round limit")):
            self.draw_choice_card("mode:" + mode, mode, detail, x, 60, 194, 87, g.mode == mode)
        self.write(pen, 24, 28, "Difficulty", 12, MUTED, "left")
        for x, difficulty in ((24, "Easy"), (164, "Normal"), (304, "Hard")):
            self.draw_choice_card("diff:" + difficulty, difficulty, "", x, -63, 130, 76,
                                  g.difficulty == difficulty, DIFFICULTIES[difficulty]["lives"])
        pace = {"Easy": "Slower shuffles", "Normal": "Balanced speed", "Hard": "Faster shuffles"}[g.difficulty]
        self.write(pen, 24, -88, pace, 11, MUTED, "left")
        self.write(pen, 434, -88, f"Best {g.best_score():,}", 11, MUTED, "right")
        if g.saved_run:
            self.write_fitted(pen, 24, -112, "Start replaces your saved game. Back keeps it.", 410, 10, "#e4bc88")
        self.draw_button("start", "Start " + g.mode, 159, -143, 258, True)
        self.draw_button("back_saved" if new_game else "howto", "Back" if new_game else "How to play", 370, -143, 128)

    def draw_saved_run_menu(self):
        """Summarize the saved game before offering a single primary action."""
        g, pen = self.session, self.session.menu_text
        saved = g.saved_run
        self.write(pen, 24, 195, "Welcome back", 24, GOLD, "left")
        self.write(pen, 24, 164, "Your last saved game", 12, "#a9d7ab", "left")
        self.rectangle(24, -39, 434, 144, "#2b2637")
        self.rectangle(24, -39, 28, 144, "#8ab69d")
        icon = "book" if saved["mode"] == "Story" else "endless"
        place_image(self, g.assets["icons"][icon], 42, 126)
        self.write(pen, 68, 108, saved["mode"], 22, WHITE, "left")
        self.write(pen, 416, 113, saved["difficulty"], 12, MUTED, "right")
        setting = LOCATION_NAMES[location(saved["mode"], saved["level"])]
        self.write(pen, 42, 82, setting, 11, MUTED, "left")
        self.write(pen, 42, 46, "Chapter" if saved["mode"] == "Story" else "Round", 11, MUTED, "left")
        self.write(pen, 246, 46, "Score", 11, MUTED, "left")
        self.write(pen, 42, 12, str(saved["level"]), 24, WHITE, "left")
        self.write_fitted(pen, 246, 12, f"{saved['score']:,}", 172, 24, WHITE)
        self.write(pen, 42, -22, "Lives left", 11, MUTED, "left")
        for index in range(DIFFICULTIES[saved["difficulty"]]["lives"]):
            icon = "heart_full" if index < saved["lives"] else "heart_empty"
            place_image(self, g.assets[icon], 246 + index * 29, -5)
        self.draw_button("resume_run", f"Resume {saved['mode']}", 231, -85, 400, True)
        self.draw_button("new_game_setup", "Start a different game", 231, -143, 400)

    def show_game_over(self):
        """Dedicated end-of-run scene; displaying it never changes saved progress."""
        self.session.state = "over"
        self.session.clear_cups()
        self.session.menu_text.clear()
        self.session.hud_text.clear()
        self.session.message.clear()
        self.session.buttons = {}
        self.draw_background()
        frame(self, -470, -292, 470, 236, "#211b2c")
        place_image(self, self.session.assets["party_over"], -468, 234)
        pen = self.session.menu_text
        self.write(pen, 0, -62, "Party over", 28, GOLD)
        self.write(pen, 0, -91, "The coin slipped away. There is still a seat for you.", 12, WHITE)
        progress = "Chapter" if self.session.mode == "Story" else "Round"
        for x, label, value in (
            (-268, "Final score", f"{self.session.score:,}"),
            (0, "Best score", f"{self.session.best_score():,}"),
            (268, progress, str(self.session.level)),
        ):
            self.write(pen, x, -132, label, 11, MUTED)
            self.write(pen, x, -164, value, 20, WHITE)
        warning = self.session.save_failed or self.session.reward_failed
        if warning:
            self.write(pen, 0, -197, "Save failed. Check folder permissions.", 11, COLORS["danger"])
        self.draw_button("play_again", "Play again", -128, -246, 224, True)
        self.draw_button("game_menu", "Menu", 128, -246, 224)
        self.draw_footer()
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
            f"{self.session.mode}   {self.session.difficulty}",
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
            else f"Round {self.session.level}   Combo {self.session.combo}"
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
            self.write_wrapped(
                self.session.message, -442, -251, detail,
                650 if self.session.state in ("result", "retry", "over", "victory") else 880,
            )
        if self.session.state in ("result", "retry", "over", "victory"):
            label = (
                "Next"
                if self.session.state == "result"
                else "Retry" if self.session.state == "retry" else "Play again"
            )
            self.session.art_layer = "message_art"
            frame(self, *RESULT_BUTTON_BOUNDS, GOLD, "#ffe0a0")
            self.session.art_layer = "scene"
            self.write(self.session.message, 340, -269, label, 12, "#2b2030")
        self.draw_footer()

    def draw_footer(self):
        self.session.footer.clear()
        self.session.screen.getcanvas().delete("footer_art")
        self.session.footer_actions = {}
        state = self.session.state
        if state == "menu_setup":
            left = [("advance", "Enter  Start " + self.session.mode)]
            right = ("escape", "Esc  Back")
        elif state == "menu":
            left = [("advance", "Enter  Resume saved" if self.session.saved_run else "Enter  Play"), ("help", "H  Help")]
            right = ("escape", "Esc  Quit")
        elif state == "paused":
            left = [("pause", "P  Resume"), ("sound", "S  Sound on" if self.session.sound_enabled else "S  Sound off")]
            right = ("escape", "Esc  Resume")
        elif state in ("reveal", "shuffle", "select"):
            pause = "P  Resume" if state == "paused" else "P  Pause"
            sound = "S  Sound on" if self.session.sound_enabled else "S  Sound off"
            left = [("pause", pause), ("sound", sound)]
            right = ("menu", "M  Menu")
        elif state == "story":
            left, right = [("advance", "Enter  Play")], ("menu", "M  Menu")
        elif state == "over":
            left, right = [("advance", "Enter  Play again")], ("menu", "M  Menu")
        elif state in ("result", "retry", "victory"):
            left, right = [("advance", "Enter  Continue")], ("menu", "M  Menu")
        elif state in ("cabinet", "gacha_opening", "gacha_reveal"):
            label = "Enter  Draw" if state == "cabinet" else "Enter  Reveal"
            if state == "gacha_reveal":
                label = "Enter  Next" if self.session.cabinet.duplicate_pending else "Enter  Cabinet"
            left, right = [("advance", label)], ("escape", "Esc  Back")
        else:
            left, right = [], ("escape", "Esc  Back")
        if not any(action == "sound" for action, _ in left):
            left.append(("sound", "S  Sound on" if self.session.sound_enabled else "S  Sound off"))
        if self.session.sound_enabled:
            left = [(action, f"S  Sound {self.session.music.volume}%" if action == "sound" else label)
                    for action, label in left]
        measure = lambda text: label_width(text, 11)
        old_layer = self.session.art_layer
        self.session.art_layer = "footer_art"
        x = -464
        for action, label in left:
            key, caption = label.split("  ", 1)
            width = max(28, measure(key) + 14) + 10 + measure(caption)
            self.footer_link(action, label, x, width)
            x += width + 22
        action, label = right
        key, caption = label.split("  ", 1)
        width = max(28, measure(key) + 14) + 10 + measure(caption)
        self.footer_link(action, label, 464 - width, width)
        self.session.art_layer = old_layer

    def footer_link(self, action, label, x, width):
        key, caption = label.split("  ", 1)
        key_width = max(28, font.Font(font=text_font(11)).measure(key) + 14)
        self.rectangle(x, -334, x + key_width, -308, "#100e19")
        self.rectangle(x, -331, x + key_width, -307, "#76576c")
        self.rectangle(x + 2, -328, x + key_width - 2, -309, "#342a41")
        canvas = self.session.screen.getcanvas()
        canvas.create_text(x + key_width / 2, 319, text=key, font=text_font(11),
                           fill=WHITE, tags=("footer_art",))
        self.canvas_label(x + key_width + 10, 320, caption, 11, MUTED, ("footer_art",))
        self.session.footer_actions[action] = (x - 4, -335, x + width + 4, -304)

    def show_coin_hint(self):
        """Briefly show a small muted glint beneath the tracked cup."""
        cup = self.session.cups[self.session.correct_id]
        canvas = self.session.screen.getcanvas()
        canvas.delete("coin_hint")
        canvas.create_image(
            cup.x - 4, 58, anchor="nw",
            image=self.session.assets["coin_hint"], tags=("coin_hint",),
        )
        self.session.hint_frames = 53

    def show_story(self):
        self.session.state = "story"
        self.session.clear_cups()
        self.draw_background()
        self.session.menu_text.clear()
        self.session.hud_text.clear()
        self.session.message.clear()
        self.session.buttons = {}
        chapter_title, setting, speaker, dialogue = CHAPTERS[self.session.level - 1]
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
        title_half_width = label_width(chapter_title, 24, True) / 2 + 22
        frame(self, -title_half_width, 110, title_half_width, 158, "#241d30")
        self.write(
            self.session.menu_text,
            0,
            121,
            chapter_title,
            24,
            WHITE,
        )
        self.write(self.session.message, -442, -220, speaker, 16, GOLD, "left")
        self.write_wrapped(
            self.session.message,
            -442,
            -246,
            dialogue,
            650,
            13,
            WHITE,
        )
        self.draw_button(
            "story_next",
            "Play",
            340,
            -260,
            202,
            True,
        )
        self.draw_footer()
        self.session.screen.update()
