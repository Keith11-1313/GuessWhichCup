"""Keyboard binding, click hitboxes and state-dependent navigation."""

import sys
from game_config import DIFFICULTIES, RESULT_BUTTON_BOUNDS
import cup_collection as collection
from run_progress import RUN_STATES


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
                self.session.play_tone("click")
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
                    "menu": self.request_menu,
                    "pause": self.toggle_pause,
                    "sound": self.toggle_sound,
                }
                handlers[action]()
                return
        if self.session.state == "paused":
            button = self.button_at(x, y)
            if button == "resume":
                self.session.pause_menu.resume()
            elif button == "restart":
                self.restart()
            elif button in ("save_menu", "save_exit"):
                self.session.pause_menu.save_and_leave(exit_app=button == "save_exit")
            return
        if self.session.state == "select":
            for cup in self.session.cups:
                if cup.contains(x, y):
                    self.rounds.choose(cup.slot)
                    return
        elif self.session.state == "over":
            button = self.button_at(x, y)
            if button == "play_again":
                self.advance()
            elif button == "game_menu":
                self.views.show_menu()
        elif self.session.state in ("result", "retry", "victory"):
            if point_in_rectangle(x, y, RESULT_BUTTON_BOUNDS):
                self.advance()
        else:
            button = self.button_at(x, y)
            if button is None:
                return
            if self.session.state in ("menu", "menu_setup"):
                self.menu_action(button)
            elif self.session.state in ("story", "cabinet", "odds", "gacha_reveal"):
                self.collection_action(button)
            elif self.session.state == "how_to_play" and button == "back":
                self.views.show_menu()

    def menu_action(self, button):
        """Apply one menu choice and redraw only when its setting changes."""
        setup = self.session.state == "menu_setup"
        if button == "new_game_setup":
            self.views.show_menu(new_game=True)
        elif button == "back_saved":
            self.views.show_menu()
        elif button.startswith("mode:"):
            self.session.mode = button.split(":", 1)[1]
            self.views.show_menu(new_game=setup)
        elif button.startswith("diff:"):
            self.session.difficulty = button.split(":", 1)[1]
            self.views.show_menu(new_game=setup)
        elif button == "start":
            self.rounds.start_game()
        elif button == "resume_run":
            if not self.session.progress.restore():
                self.views.show_menu()
        elif button == "cabinet":
            self.cabinet.show_cabinet()
        elif button == "howto":
            self.views.show_how_to_play()

    def open_cabinet_from_menu(self):
        if self.session.state == "menu":
            self.cabinet.show_cabinet()

    def advance(self):
        if self.session.state == "paused":
            self.session.pause_menu.resume()
            return
        if self.session.state == "menu_setup":
            self.rounds.start_game()
        elif self.session.state == "menu":
            if self.session.saved_run:
                if not self.session.progress.restore():
                    self.views.show_menu()
            else:
                self.rounds.start_game()

        elif self.session.state == "how_to_play":
            self.views.show_menu()

        elif self.session.state == "story":
            self.rounds.start_level()

        elif self.session.state == "gacha_reveal":
            if self.cabinet.duplicate_pending:
                self.cabinet.convert_duplicate()
            else:
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
        if self.session.state == "paused":
            self.session.pause_menu.resume()
        self.rounds.start_game()

    def request_help(self):
        if self.session.state in RUN_STATES or self.session.state == "paused":
            self.session.pause_menu.open()
        else:
            self.views.show_how_to_play()

    def toggle_sound(self):
        self.session.sound_enabled = not self.session.sound_enabled
        if self.session.sound_enabled and self.session.audio_active:
            self.session.music.start()
        else:
            self.session.music.stop()
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(None, 0)
        self.session.screen.title(
            "Guess Which Cup | Lantern House | Sound "
            + ("on" if self.session.sound_enabled else "off")
        )
        self.views.draw_footer()

    def cycle_mode(self):
        if self.session.state == "menu" and self.session.saved_run:
            return
        if self.session.state in ("menu", "menu_setup"):
            setup = self.session.state == "menu_setup"
            self.session.mode = "Endless" if self.session.mode == "Story" else "Story"
            self.views.show_menu(new_game=setup)

    def adjust_music_volume(self, step):
        self.session.music.set_volume(self.session.music.volume + step)
        self.views.draw_footer()

    def cycle_difficulty(self, direction=1):
        if self.session.state == "menu" and self.session.saved_run:
            return
        if self.session.state in ("menu", "menu_setup"):
            setup = self.session.state == "menu_setup"
            names = list(DIFFICULTIES)
            self.session.difficulty = names[
                (names.index(self.session.difficulty) + direction) % len(names)
            ]
            self.views.show_menu(new_game=setup)

    def request_menu(self):
        if self.session.state in RUN_STATES or self.session.state == "paused":
            self.session.pause_menu.open()
        else:
            self.views.show_menu()

    def toggle_pause(self):
        if self.session.state == "paused":
            self.session.pause_menu.resume()
        else:
            self.session.pause_menu.open()

    def escape(self):
        if self.session.state == "paused":
            self.session.pause_menu.resume()
        elif self.session.state in RUN_STATES:
            self.session.pause_menu.open()
        elif self.session.state == "menu":
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
            self.session.screen.onkeypress(self.request_menu, key)

        for key in ("h", "H"):
            self.session.screen.onkeypress(self.request_help, key)

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
        self.session.screen.onkeypress(lambda: self.adjust_music_volume(-5), "minus")
        self.session.screen.onkeypress(lambda: self.adjust_music_volume(5), "equal")
        for key in ("c", "C"):
            self.session.screen.onkeypress(self.open_cabinet_from_menu, key)
        self.session.screen.onkeypress(self.cycle_mode, "Tab")
        self.session.screen.onkeypress(lambda: self.cycle_difficulty(-1), "Left")
        self.session.screen.onkeypress(self.cycle_difficulty, "Right")

    def collection_action(self, key):
        if key == "convert_duplicate":
            self.cabinet.convert_duplicate()
        elif key == "story_next":
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
                self.session.play_tone("equip")
                self.session.update_window_icon()
                self.cabinet.show_cabinet("Cup equipped.")
            else:
                self.cabinet.show_cabinet("Could not save. Try again.")
