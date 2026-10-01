"""Round setup, shuffle animation, scoring and save operations."""

import math
import random
import time
import cup_collection as collection
from game_config import COLORS, DIFFICULTIES, STORY_LEVELS, level_settings
from score_store import save_score

GOLD = COLORS["gold"]


class RoundLogic:

    def __init__(self, session, views):
        self.session = session
        self.views = views

    def save_high_score(self):
        if self.session.score > self.session.best_score():
            self.session.save_failed = not save_score(
                self.session.score_path,
                self.session.scores,
                self.session.best_key(),
                self.session.score,
            )

    def start_game(self):
        self.session.save_failed = False
        self.session.reward_failed = False
        self.session.score = 0
        self.session.level = 1
        self.session.lives = DIFFICULTIES[self.session.difficulty]["lives"]

        # Reset combo/perfect for a new game
        self.session.combo = 0
        self.session.perfect = True

        self.begin_chapter()

    def selection_hint(self):
        return f"Click a cup or press 1-{len(self.session.cups)}."

    def start_level(self):
        self.session.state = "reveal"
        self.session.clear_cups()
        self.views.draw_background()
        self.session.menu_text.clear()
        self.session.buttons = {}
        self.views.draw_hud()

        (
            count,
            self.session.swaps,
            self.session.swap_duration,
            self.session.reveal_frames,
        ) = level_settings(self.session.level, self.session.difficulty)

        spacing = min(150, 760 / max(1, count - 1))
        self.session.slots = [(i - (count - 1) / 2) * spacing for i in range(count)]

        self.session.cups = self.session.cup_pool[:count]
        # cid stays with the cup; slot is its current numbered table position.
        for i, cup in enumerate(self.session.cups):
            cup.reset(i, self.session.slots[i], self.session.profile["equipped"])

        self.session.art_layer = "choice_art"
        for i, x in enumerate(self.session.slots):
            self.views.rectangle(x - 15, -124, x + 15, -96, "#312331")
            self.views.write(self.session.labels, x, -119, str(i + 1), 12, GOLD)
        self.session.art_layer = "scene"
        self.cups = [
            Cup(i, self.slots[i], self.profile["equipped"]) for i in range(count)
        ]

        for cup in self.cups:
            cup.y = -35
            cup.render()

        for i, x in enumerate(self.slots):
            self.rectangle(x - 15, -124, x + 15, -96, "#312331")
            self.write(self.labels, x, -119, str(i + 1), 12, GOLD)

        self.session.correct_id = random.randrange(count)
        self.session.reveal_frame = 0
        self.session.completed_swaps = 0
        self.session.swap_pair = None
        self.session.last_tick = time.monotonic()
        self.session.frame_credit = 0.0

        special = self.session.cups[self.session.correct_id]
        special.y = 76
        special.render()

        self.session.ball.goto(special.x, -40)
        self.session.ball.showturtle()

        self.views.set_message("Remember the spark", "Watch which cup holds it.")

        self.session.play_tone("reveal")
        self.session.screen.listen()
        self.session.screen.update()

    def begin_shuffle(self):
        self.session.state = "shuffle"
        self.session.ball.hideturtle()

        for cup in self.session.cups:
            cup.y = 0
        for cup in self.cups:
            cup.y = -35
            cup.render()

        self.views.set_message("Follow the cup", "")

    def animate_swap(self):
        if self.session.swap_pair is None:
            if self.session.completed_swaps >= self.session.swaps:
                self.session.state = "select"
                self.views.set_message("Where is the spark?", self.selection_hint())
                return

            a, b = random.sample(self.session.cups, 2)
            self.session.swap_pair = (a, b, a.slot, b.slot)
            self.session.swap_frame = 0

        a, b, slot_a, slot_b = self.session.swap_pair
        self.session.swap_frame += 1

        t = min(1.0, self.session.swap_frame / self.session.swap_duration)
        eased = t * t * (3 - 2 * t)

        a.x = (
            self.session.slots[slot_a]
            + (self.session.slots[slot_b] - self.session.slots[slot_a]) * eased
        )

        b.x = (
            self.session.slots[slot_b]
            + (self.session.slots[slot_a] - self.session.slots[slot_b]) * eased
        )

        arc = math.sin(math.pi * t) * 37
        a.y = -35 + arc
        b.y = -35 - arc

        a.render()
        b.render()

        if t >= 1:
            a.slot, b.slot = slot_b, slot_a
            a.x, b.x = self.session.slots[a.slot], self.session.slots[b.slot]
            a.y = b.y = 0
            a.x, b.x = self.slots[a.slot], self.slots[b.slot]
            a.y = b.y = -35

            a.render()
            b.render()

            self.session.completed_swaps += 1
            self.session.swap_pair = None

    def choose(self, slot):
        """Resolve one valid choice; ignore input outside the selection phase."""
        if self.session.state != "select":
            return
        selected = next((cup for cup in self.session.cups if cup.slot == slot), None)
        if selected is None:
            return

        # Lock input before rendering so a second click cannot score twice.
        self.session.state = "resolving"
        correct = self.session.cups[self.session.correct_id]
        selected.y = 76
        selected.render()
        correct.y = 76
        correct.render()
        self.session.ball.goto(correct.x, -40)
        self.session.ball.showturtle()

        if selected is correct:
            self.resolve_correct_guess()
        else:
            self.resolve_wrong_guess()

    def resolve_correct_guess(self):
        """Award points and one eligible ticket, then show the next action."""
        points = self.session.level * 100 + (self.session.lives - 1) * 20
        if self.session.mode == "Endless":
            self.session.combo += 1
            points += self.session.combo * 25

        reward_key = None
        if self.session.mode == "Story":
            reward_key = f"{self.session.difficulty}:{self.session.level}"
        earned = collection.reward(
            self.session.profile_path, self.session.profile, reward_key
        )
        self.session.reward_failed = earned == -1
        earned_text = "  /  +1 ticket" if earned == 1 else ""

        self.session.score += points
        self.save_high_score()
        self.views.draw_hud()
        self.session.play_tone("correct")
        if self.session.mode == "Story" and self.session.level >= STORY_LEVELS:
            self.finish_story()
        else:
            self.session.state = "result"
            self.views.set_message("Found it", f"+{points} points{earned_text}")

    def finish_story(self):
        """Complete the narrative and apply the perfect-run bonus once."""
        self.session.state = "victory"
        if self.session.perfect:
            self.session.score += 1000
            self.save_high_score()
            self.views.set_message(
                "The wish came true",
                "Mira: This house feels like home again. Thank you.",
                GOLD,
            )
            self.views.draw_hud()
            self.views.write(
                self.session.message,
                -442,
                -279,
                "+1,000 perfect bonus",
                10,
                GOLD,
                "left",
            )
        else:
            self.views.set_message(
                "The wish came true",
                "Mira: Same time next year? Your seat will be here.",
            )
        self.session.play_tone("win")

    def resolve_wrong_guess(self):
        """Lose a life and either offer a retry or end the run."""
        self.session.lives -= 1
        if self.session.mode == "Endless":
            self.session.combo = 0
        else:
            self.session.perfect = False
        self.views.draw_hud()
        self.session.play_tone("wrong")
        if self.session.lives > 0:
            self.session.state = "retry"
            self.views.set_message("Not this cup", f"{self.session.lives} lives left.")
        else:
            self.session.state = "over"
            self.views.set_message("Party over", f"Final score: {self.session.score:,}")

    def begin_chapter(self):
        if self.session.mode == "Story":
            self.session.story_page = 0
            self.views.show_story()
        else:
            self.start_level()
