"""Keyboard binding, click hitboxes and state-dependent navigation."""

import time
from game_config import DIFFICULTIES, RESULT_BUTTON_BOUNDS
from game_objects import tone


def point_in_rectangle(x, y, bounds):
    x1, y1, x2, y2 = bounds
    return x1 <= x <= x2 and y1 <= y <= y2


class InputControls:
    """Input methods mixed into Game; no separate game state is stored here."""

    def button_at(self, x, y):
        """Find the first visible button whose bounds contain the click."""
        for name, bounds in list(self.buttons.items()):
            if point_in_rectangle(x, y, bounds):
                return name
        return None

    def on_click(self, x, y):
        """Route a click according to the current screen or round phase."""
        if self.state == "select":
            for cup in self.cups:
                if cup.contains(x, y):
                    self.choose(cup.slot)
                    return
        elif self.state in ("result", "retry", "over", "victory"):
            if point_in_rectangle(x, y, RESULT_BUTTON_BOUNDS):
                self.advance()
        else:
            button = self.button_at(x, y)
            if button is None:
                return
            if self.state == "menu":
                self.menu_action(button)
            elif self.state in ("story", "cabinet", "odds", "gacha_reveal"):
                self.collection_action(button)
            elif self.state == "how_to_play" and button == "back":
                self.show_menu()

    def menu_action(self, button):
        """Apply one menu choice and redraw only when its setting changes."""
        if button.startswith("mode:"):
            self.mode = button.split(":", 1)[1]
            self.show_menu()
        elif button.startswith("diff:"):
            self.difficulty = button.split(":", 1)[1]
            self.show_menu()
        elif button == "start":
            self.start_game()
        elif button == "cabinet":
            self.show_cabinet()
        elif button == "howto":
            self.show_how_to_play()

    def open_cabinet_from_menu(self):
        if self.state == "menu":
            self.show_cabinet()

    def advance(self):
        if self.state == "menu":
            self.start_game()

        elif self.state == "how_to_play":
            self.show_menu()

        elif self.state == "story":
            if self.story_page == 0:
                self.story_page = 1
                self.show_story()
            else:
                self.start_level()

        elif self.state == "gacha_reveal":
            self.show_cabinet()

        elif self.state == "gacha_opening":
            self.reveal_draw()

        elif self.state == "cabinet":
            self.draw_cup()

        elif self.state in ("over", "victory"):
            self.start_game()

        elif self.state == "result":
            self.level += 1
            self.begin_chapter()

        elif self.state == "retry":
            self.start_level()

    def restart(self):
        self.start_game()

    def play_tone(self, kind):
        if self.sound_enabled:
            tone(kind, self.screen)

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.screen.title(
            "Guess Which Cup | Lantern House | Sound "
            + ("on" if self.sound_enabled else "off")
        )

    def cycle_mode(self):
        if self.state == "menu":
            self.mode = "Endless" if self.mode == "Story" else "Story"
            self.show_menu()

    def cycle_difficulty(self, direction=1):
        if self.state == "menu":
            names = list(DIFFICULTIES)
            self.difficulty = names[
                (names.index(self.difficulty) + direction) % len(names)
            ]
            self.show_menu()

    def toggle_pause(self):
        if self.state == "paused":
            self.state = self.paused_state
            self.last_tick = time.monotonic()
            self.frame_credit = 0.0
            if self.state == "select":
                self.set_message("Where is the spark?", self.selection_hint())
            elif self.state == "reveal":
                self.set_message("Remember the spark", "Watch which cup holds it.")
            else:
                self.set_message("Follow the cup", "")
        elif self.state in ("reveal", "shuffle", "select"):
            self.paused_state = self.state
            self.state = "paused"
            self.set_message("Paused", "")

    def escape(self):
        if self.state == "menu":
            self.close()
        elif self.state in ("odds", "gacha_reveal", "gacha_opening"):
            self.show_cabinet()
        else:
            self.show_menu()

    def bind_controls(self):
        self.screen.onclick(self.on_click)
        self.screen.listen()

        for key in ("Return", "space"):
            self.screen.onkeypress(self.advance, key)

        for key in ("m", "M"):
            self.screen.onkeypress(self.show_menu, key)

        for key in ("h", "H"):
            self.screen.onkeypress(self.show_how_to_play, key)

        for key in ("r", "R"):
            self.screen.onkeypress(self.restart, key)

        for n in range(1, 7):
            self.screen.onkeypress(lambda number=n: self.choose(number - 1), str(n))

        self.screen.onkeypress(self.escape, "Escape")
        self.screen.onkeypress(self.toggle_pause, "p")
        self.screen.onkeypress(self.toggle_sound, "s")
        self.screen.onkeypress(self.toggle_pause, "P")
        self.screen.onkeypress(self.toggle_sound, "S")
        for key in ("c", "C"):
            self.screen.onkeypress(self.open_cabinet_from_menu, key)
        self.screen.onkeypress(self.cycle_mode, "Tab")
        self.screen.onkeypress(lambda: self.cycle_difficulty(-1), "Left")
        self.screen.onkeypress(self.cycle_difficulty, "Right")
