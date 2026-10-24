"""A pause overlay that freezes the current board and saves before leaving."""

import time
from game_config import COLORS
from party_art import frame
from run_progress import RUN_STATES


class PauseMenu:
    def __init__(self, session):
        self.session = session
        self.previous_buttons = {}

    def open(self):
        g = self.session
        if g.state == "paused" or g.state not in RUN_STATES:
            return
        g.paused_state, g.state = g.state, "paused"
        self.previous_buttons = dict(g.buttons)
        g.play_tone("pause")
        self.draw()

    def draw(self, error=""):
        g = self.session
        canvas = g.screen.getcanvas()
        canvas.delete("pause_art")
        canvas.create_rectangle(-500, -250, 500, 300, fill="#15121d", stipple="gray50", width=0, tags=("pause_art",))
        g.art_layer = "pause_art"
        frame(g.views, -250, -198, 250, 174, "#211b2c")
        g.views.canvas_label(-56, -126, "Paused", 24, COLORS["gold"], ("pause_art",))
        g.buttons = {}
        g.views.draw_button("resume", "Resume", 0, 58, 300, True)
        g.views.draw_button("restart", "Restart run", 0, 0, 300)
        g.views.draw_button("save_menu", "Save & Menu", 0, -58, 300)
        g.views.draw_button("save_exit", "Save & Exit", 0, -116, 300)
        if error:
            g.views.canvas_label(-205, 161, error, 11, COLORS["danger"], ("pause_art",))
        g.art_layer = "scene"
        g.views.draw_footer()

    def resume(self):
        g = self.session
        if g.state != "paused":
            return
        g.screen.getcanvas().delete("pause_art")
        g.buttons = self.previous_buttons
        g.state, g.paused_state = g.paused_state, None
        g.last_tick, g.frame_credit = time.monotonic(), 0.0
        g.views.draw_footer()

    def save_and_leave(self, exit_app=False):
        g = self.session
        if not g.progress.save():
            self.draw("Could not save. Your table is still paused.")
            return False
        self.resume()
        if exit_app:
            g.close()
        else:
            g.views.show_menu()
        return True
