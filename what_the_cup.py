"""Application setup and timer loop for Guess Which Cup.

Game owns the shared session data. The four behavior classes supply screen,
round, input and cabinet methods without separate copies of that data.
"""

import time
import tkinter
import turtle
import cup_collection as collection
from collection_screens import CupCabinet
from game_config import COLORS, FRAME_MS, HEIGHT, SAVE_FILE, WIDTH
from game_objects import make_writer
from game_screens import GameScreens
from input_controls import InputControls
from party_art import register_cup
from round_logic import RoundLogic
from score_store import load_scores

BG = COLORS["background"]
MUTED = COLORS["muted"]
GOLD = COLORS["gold"]


class Game(GameScreens, RoundLogic, InputControls, CupCabinet):
    """Shared session and runtime; behavior lives in the named modules."""

    def __init__(self, run_loop=True):
        self.screen = turtle.Screen()
        self.screen.setup(WIDTH, HEIGHT)
        self.screen.title("Guess Which Cup | Lantern House | by @RENE")
        self.screen.bgcolor(BG)
        self.screen.tracer(0)
        register_cup(self.screen)
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

        self.score_path = SAVE_FILE
        self.scores = load_scores(self.score_path)
        self.profile = collection.load_profile(collection.PROFILE_FILE)
        self.story_page = 0
        self.reward_failed = False
        self.pending_cup = None
        self.mode = "Story"
        self.difficulty = "Normal"
        self.level = 1
        self.score = 0
        self.lives = 3

        # Endless combo and Story perfect tracking
        self.combo = 0
        self.perfect = True

        self.state = "menu"
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

        self.bind_controls()
        self.show_menu()
        self.screen.ontimer(self.update, FRAME_MS)
        if run_loop:
            self.screen.mainloop()

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
                        self.begin_shuffle()
                elif self.state == "shuffle":
                    self.animate_swap()
                elif self.state == "gacha_opening":
                    self.animate_draw()
            self.screen.update()
            if self.running:
                self.screen.ontimer(self.update, FRAME_MS)
        except (turtle.Terminator, tkinter.TclError):
            self.running = False


if __name__ == "__main__":
    Game()
