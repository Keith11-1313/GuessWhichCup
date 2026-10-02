"""Application setup and timer loop for Guess Which Cup.

Game owns session data and runtime resources. Explicit components handle
rendering, rounds, input and the cabinet without multiple inheritance.
"""

import time
import tkinter
import turtle
import cup_collection as collection
from collection_screens import CupCabinet
from game_config import COLORS, FRAME_MS, HEIGHT, SAVE_FILE, WIDTH
from game_objects import Cup, make_writer, tone
from game_screens import GameScreens
from input_controls import InputControls
from party_art import load_assets
from round_logic import RoundLogic
from score_store import load_scores

BG = COLORS["background"]
MUTED = COLORS["muted"]
GOLD = COLORS["gold"]


class Game:
    """Session and runtime with explicitly constructed behavior components."""

    def __init__(self, run_loop=True, score_path=None, profile_path=None):
        self.screen = turtle.Screen()
        self.screen.setup(WIDTH, HEIGHT)
        self.screen.title("Guess Which Cup | Lantern House | by @RENE")
        self.screen.bgcolor(BG)
        self.screen.tracer(0)
        self.assets = load_assets(self.screen)
        self.running = True
        self.sound_enabled = True
        self.paused_state = None
        self.last_tick = time.monotonic()
        self.frame_credit = 0.0
        root = self.screen.getcanvas().winfo_toplevel()
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.static = make_writer()
        self.footer = make_writer()
        self.menu_text = make_writer()
        self.hud_text = make_writer()
        self.message = make_writer()
        self.labels = make_writer(MUTED)

        self.ball = turtle.Turtle(visible=False)
        self.ball.speed(0)
        self.ball.penup()
        self.ball.shape("spark")
        self.ball.setheading(90)
        self.ball.color(GOLD)

        # QA supplies temporary paths; normal play uses saves beside the game.
        self.score_path = SAVE_FILE if score_path is None else score_path
        self.scores = load_scores(self.score_path)
        self.profile_path = (
            collection.PROFILE_FILE if profile_path is None else profile_path
        )
        self.profile = collection.load_profile(self.profile_path)
        self.story_page = 0
        self.save_failed = False
        self.reward_failed = False
        self.pending_cup = None
        self.draw_status = None
        self.draw_frame = 0
        self.art_layer = "scene"
        self.mode = "Story"
        self.difficulty = "Normal"
        self.level = 1
        self.score = 0
        self.lives = 3

        # Endless combo and Story perfect tracking
        self.combo = 0
        self.perfect = True

        self.state = "menu"
        self.cup_pool = [Cup(i, 0) for i in range(6)]
        for cup in self.cup_pool:
            cup.hide()
        self.cups = []
        self.slots = []
        self.correct_id = 0
        self.reveal_frame = 0
        self.reveal_frames = 0
        self.swaps = 0
        self.swap_duration = 30
        self.completed_swaps = 0
        self.swap_pair = None
        self.swap_frame = 0
        self.buttons = {}

        self.views = GameScreens(self)
        self.rounds = RoundLogic(self, self.views)
        self.cabinet = CupCabinet(self, self.views)
        self.controls = InputControls(self, self.views, self.rounds, self.cabinet)
        self.controls.bind_controls()
        self.views.show_menu()
        self.screen.ontimer(self.update, FRAME_MS)
        if run_loop:
            self.screen.mainloop()

    def clear_cups(self):
        for cup in self.cups:
            cup.hide()

        self.cups = []
        self.ball.hideturtle()
        self.labels.clear()

    def best_key(self):
        return f"{self.mode.lower()}_{self.difficulty.lower()}"

    def best_score(self):
        return int(self.scores.get(self.best_key(), 0))

    def play_tone(self, kind):
        if self.sound_enabled:
            tone(kind)

    def close(self):
        self.running = False
        self.screen.bye()

    def update(self):
        if not self.running:
            return
        try:
            now = time.monotonic()
            # Use elapsed time so the difficulty does not depend on render speed.
            self.frame_credit += min(now - self.last_tick, 0.1) * 1000 / FRAME_MS
            self.last_tick = now
            steps = int(self.frame_credit)
            self.frame_credit -= steps
            for _ in range(steps):
                if self.state == "reveal":
                    self.reveal_frame += 1
                    if self.reveal_frame >= self.reveal_frames:
                        self.rounds.begin_shuffle()
                elif self.state == "shuffle":
                    self.rounds.animate_swap()
                elif self.state == "gacha_opening":
                    self.cabinet.animate_draw()
            self.screen.update()
            if self.running:
                self.screen.ontimer(self.update, FRAME_MS)
        except turtle.Terminator:
            self.running = False
        except tkinter.TclError:
            # Closing can cancel Tk work. Other Tk errors must remain debuggable.
            if self.running:
                raise


if __name__ == "__main__":
    Game()
