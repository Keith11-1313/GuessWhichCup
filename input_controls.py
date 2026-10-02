"""Keyboard binding, click hitboxes and state-dependent navigation."""

import time
from game_config import DIFFICULTIES, RESULT_BUTTON_BOUNDS
import cup_collection as collection


def point_in_rectangle(x, y, bounds):
    x1, y1, x2, y2 = bounds
    return x1 <= x <= x2 and y1 <= y <= y2


class InputControls:
    """Route input through explicit view, round and cabinet dependencies."""

    def __init__(self, session, views, rounds, cabinet):
        self.session = session
        self.views = views
        self.rounds = rounds
        self.cabinet = cabinet

    def button_at(self, x, y):
        """Find the first visible button whose bounds contain the click."""
        for name, bounds in list(self.session.buttons.items()):
            if point_in_rectangle(x, y, bounds):
                return name
        return None

    def on_click(self, x, y):
        """Route a click according to the current screen or round phase."""
        for action, bounds in self.session.footer_actions.items():
            if point_in_rectangle(x, y, bounds):
                handlers = {
                    "advance": self.advance,
                    "help": self.views.show_how_to_play,
                    "escape": self.escape,
                    "menu": self.views.show_menu,
                    "pause": self.toggle_pause,
                    "sound": self.toggle_sound,
                }
                handlers[action]()
                return
        if self.session.state == "select":
            for cup in self.session.cups:
                if cup.contains(x, y):
                    self.rounds.choose(cup.slot)
                    return
        elif self.session.state in ("result", "retry", "over", "victory"):
            if point_in_rectangle(x, y, RESULT_BUTTON_BOUNDS):
                self.advance()
        else:
            button = self.button_at(x, y)
            if button is None:
                return
            if self.session.state == "menu":
                self.menu_action(button)
            elif self.session.state in ("story", "cabinet", "odds", "gacha_reveal"):
                self.collection_action(button)
            elif self.session.state == "how_to_play" and button == "back":
                self.views.show_menu()

    def menu_action(self, button):
        """Apply one menu choice and redraw only when its setting changes."""
        if button.startswith("mode:"):
            self.session.mode = button.split(":", 1)[1]
            self.views.show_menu()
        elif button.startswith("diff:"):
            self.session.difficulty = button.split(":", 1)[1]
            self.views.show_menu()
        elif button == "start":
            self.rounds.start_game()
        elif button == "cabinet":
            self.cabinet.show_cabinet()
        elif button == "howto":
            self.views.show_how_to_play()

    def open_cabinet_from_menu(self):
        if self.session.state == "menu":
            self.cabinet.show_cabinet()

    def advance(self):
        if self.session.state == "menu":
            self.rounds.start_game()

        elif self.session.state == "how_to_play":
            self.views.show_menu()

        elif self.session.state == "story":
            if self.session.story_page == 0:
                self.session.story_page = 1
                self.views.show_story()
            else:
                self.rounds.start_level()

        elif self.session.state == "gacha_reveal":
            self.cabinet.show_cabinet()

        elif self.session.state == "gacha_opening":
            self.cabinet.reveal_draw()

        elif self.session.state == "cabinet":
            self.cabinet.draw_cup()

        elif self.session.state in ("over", "victory"):
            self.rounds.start_game()

        elif self.session.state == "result":
            self.session.level += 1
            self.rounds.begin_chapter()

        elif self.session.state == "retry":
            self.rounds.start_level()

    def restart(self):
        self.rounds.start_game()

    def toggle_sound(self):
        self.session.sound_enabled = not self.session.sound_enabled
        self.session.screen.title(
            "Guess Which Cup | Lantern House | Sound "
            + ("on" if self.session.sound_enabled else "off")
        )
        self.views.draw_footer()

    def cycle_mode(self):
        if self.session.state == "menu":
            self.session.mode = "Endless" if self.session.mode == "Story" else "Story"
            self.views.show_menu()

    def cycle_difficulty(self, direction=1):
        if self.session.state == "menu":
            names = list(DIFFICULTIES)
            self.session.difficulty = names[
                (names.index(self.session.difficulty) + direction) % len(names)
            ]
            self.views.show_menu()

    def toggle_pause(self):
        if self.session.state == "paused":
            self.session.state = self.session.paused_state
            self.session.last_tick = time.monotonic()
            self.session.frame_credit = 0.0
            if self.session.state == "select":
                self.views.set_message(
                    "Where is the spark?", self.rounds.selection_hint()
                )
            elif self.session.state == "reveal":
                self.views.set_message(
                    "Remember the spark", "Watch which cup holds it."
                )
            else:
                self.views.set_message("Follow the cup", "")
        elif self.session.state in ("reveal", "shuffle", "select"):
            self.session.paused_state = self.session.state
            self.session.state = "paused"
            self.views.set_message("Paused", "")

    def escape(self):
        if self.session.state == "menu":
            self.session.close()
        elif self.session.state in ("odds", "gacha_reveal", "gacha_opening"):
            self.cabinet.show_cabinet()
        else:
            self.views.show_menu()

    def bind_controls(self):
        self.session.screen.onclick(self.on_click)
        self.session.screen.listen()

        for key in ("Return", "space"):
            self.session.screen.onkeypress(self.advance, key)

        for key in ("m", "M"):
            self.session.screen.onkeypress(self.views.show_menu, key)

        for key in ("h", "H"):
            self.session.screen.onkeypress(self.views.show_how_to_play, key)

        for key in ("r", "R"):
            self.session.screen.onkeypress(self.restart, key)

        for n in range(1, 7):
            self.session.screen.onkeypress(
                lambda number=n: self.rounds.choose(number - 1), str(n)
            )

        self.session.screen.onkeypress(self.escape, "Escape")
        self.session.screen.onkeypress(self.toggle_pause, "p")
        self.session.screen.onkeypress(self.toggle_sound, "s")
        self.session.screen.onkeypress(self.toggle_pause, "P")
        self.session.screen.onkeypress(self.toggle_sound, "S")
        for key in ("c", "C"):
            self.session.screen.onkeypress(self.open_cabinet_from_menu, key)
        self.session.screen.onkeypress(self.cycle_mode, "Tab")
        self.session.screen.onkeypress(lambda: self.cycle_difficulty(-1), "Left")
        self.session.screen.onkeypress(self.cycle_difficulty, "Right")

    def collection_action(self, key):
        if key == "story_next":
            self.advance()
        elif key == "draw":
            self.cabinet.draw_cup()
        elif key == "odds":
            self.cabinet.show_odds()
        elif key == "back":
            self.views.show_menu()
        elif key == "cabinet":
            self.cabinet.show_cabinet()
        elif key.startswith("equip:"):
            skin = key.split(":", 1)[1]
            if collection.equip(self.session.profile_path, self.session.profile, skin):
                self.cabinet.show_cabinet("Cup equipped.")
            else:
                self.cabinet.show_cabinet("Could not save. Try again.")
