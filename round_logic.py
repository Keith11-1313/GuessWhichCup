"""Round setup, shuffle animation, scoring and save operations."""

import math
import random
import time
import cup_collection as collection
from game_config import COLORS, DIFFICULTIES, STORY_LEVELS, level_settings
from game_objects import Cup
from score_store import save_score

GOLD = COLORS["gold"]


class RoundLogic:
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

    def save_high_score(self):
        if self.score > self.best_score():
            self.save_failed = not save_score(
                self.score_path, self.scores, self.best_key(), self.score
            )

    def start_game(self):
        self.save_failed = False
        self.reward_failed = False
        self.score = 0
        self.level = 1
        self.lives = DIFFICULTIES[self.difficulty]["lives"]

        # Reset combo/perfect for a new game
        self.combo = 0
        self.perfect = True

        self.begin_chapter()

    def selection_hint(self):
        return f"Click a cup or press 1-{len(self.cups)}."

    def start_level(self):
        self.state = "reveal"
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear()
        self.buttons = {}
        self.draw_hud()

        count, self.swaps, self.swap_duration, self.reveal_frames = level_settings(
            self.level, self.difficulty
        )

        spacing = min(150, 760 / max(1, count - 1))
        self.slots = [(i - (count - 1) / 2) * spacing for i in range(count)]

        self.cups = [
            Cup(i, self.slots[i], self.profile["equipped"]) for i in range(count)
        ]

        for cup in self.cups:
            cup.y = -35
            cup.render()

        for i, x in enumerate(self.slots):
            self.rectangle(x - 15, -124, x + 15, -96, "#312331")
            self.write(self.labels, x, -119, str(i + 1), 12, GOLD)

        self.correct_id = random.randrange(count)
        self.reveal_frame = 0
        self.completed_swaps = 0
        self.swap_pair = None
        self.state = "reveal"
        self.last_tick = time.monotonic()
        self.frame_credit = 0.0

        special = self.cups[self.correct_id]
        special.y = 76
        special.render()

        self.ball.goto(special.x, -40)
        self.ball.showturtle()

        self.set_message("Remember the spark", "Watch which cup holds it.")

        self.play_tone("reveal")
        self.screen.listen()
        self.screen.update()

    def begin_shuffle(self):
        self.state = "shuffle"
        self.ball.hideturtle()

        for cup in self.cups:
            cup.y = -35
            cup.render()

        self.set_message("Follow the cup", "")

    def animate_swap(self):
        if self.swap_pair is None:
            if self.completed_swaps >= self.swaps:
                self.state = "select"
                self.set_message("Where is the spark?", self.selection_hint())
                return

            a, b = random.sample(self.cups, 2)
            self.swap_pair = (a, b, a.slot, b.slot)
            self.swap_frame = 0

        a, b, slot_a, slot_b = self.swap_pair
        self.swap_frame += 1

        t = min(1.0, self.swap_frame / self.swap_duration)
        eased = t * t * (3 - 2 * t)

        a.x = self.slots[slot_a] + (self.slots[slot_b] - self.slots[slot_a]) * eased

        b.x = self.slots[slot_b] + (self.slots[slot_a] - self.slots[slot_b]) * eased

        arc = math.sin(math.pi * t) * 37
        a.y = -35 + arc
        b.y = -35 - arc

        a.render()
        b.render()

        if t >= 1:
            a.slot, b.slot = slot_b, slot_a
            a.x, b.x = self.slots[a.slot], self.slots[b.slot]
            a.y = b.y = -35

            a.render()
            b.render()

            self.completed_swaps += 1
            self.swap_pair = None

    def choose(self, slot):
        """Resolve one valid choice; ignore input outside the selection phase."""
        if self.state != "select":
            return
        selected = next((cup for cup in self.cups if cup.slot == slot), None)
        if selected is None:
            return

        # Lock input before rendering so a second click cannot score twice.
        self.state = "resolving"
        correct = self.cups[self.correct_id]
        selected.y = 76
        selected.render()
        correct.y = 76
        correct.render()
        self.ball.goto(correct.x, -40)
        self.ball.showturtle()

        if selected is correct:
            self.resolve_correct_guess()
        else:
            self.resolve_wrong_guess()

    def resolve_correct_guess(self):
        """Award points and one eligible ticket, then show the next action."""
        points = self.level * 100 + (self.lives - 1) * 20
        if self.mode == "Endless":
            self.combo += 1
            points += self.combo * 25

        reward_key = None
        if self.mode == "Story":
            reward_key = f"{self.difficulty}:{self.level}"
        earned = collection.reward(collection.PROFILE_FILE, self.profile, reward_key)
        self.reward_failed = earned == -1
        earned_text = "  /  +1 ticket" if earned == 1 else ""

        self.score += points
        self.save_high_score()
        self.draw_hud()
        self.play_tone("correct")
        if self.mode == "Story" and self.level >= STORY_LEVELS:
            self.finish_story()
        else:
            self.state = "result"
            self.set_message("Found it", f"+{points} points{earned_text}")

    def finish_story(self):
        """Complete the narrative and apply the perfect-run bonus once."""
        self.state = "victory"
        if self.perfect:
            self.score += 1000
            self.save_high_score()
            self.set_message(
                "The wish came true",
                "Mira: This house feels like home again. Thank you.",
                GOLD,
            )
            self.draw_hud()
            self.write(
                self.message, -442, -279, "+1,000 perfect bonus", 10, GOLD, "left"
            )
        else:
            self.set_message(
                "The wish came true",
                "Mira: Same time next year? Your seat will be here.",
            )
        self.play_tone("win")

    def resolve_wrong_guess(self):
        """Lose a life and either offer a retry or end the run."""
        self.lives -= 1
        if self.mode == "Endless":
            self.combo = 0
        else:
            self.perfect = False
        self.draw_hud()
        self.play_tone("wrong")
        if self.lives > 0:
            self.state = "retry"
            self.set_message("Not this cup", f"{self.lives} lives left.")
        else:
            self.state = "over"
            self.set_message("Party over", f"Final score: {self.score:,}")
