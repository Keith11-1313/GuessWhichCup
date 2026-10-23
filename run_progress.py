"""Validated, atomic checkpoints for a paused run, separate from cup ownership."""

import json
import math
import time
import uuid
from game_config import DIFFICULTIES, level_settings
from cup_collection import persist

RUN_STATES = ("story", "reveal", "shuffle", "select", "result", "retry")
COUNTERS = (
    "reveal_frame", "reveal_frames", "swaps", "swap_duration",
    "completed_swaps", "swap_frame", "correct_id", "hint_frames",
)


def load_run(path):
    """Reject damaged checkpoints rather than partially restoring a board."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1:
            return None
        if data.get("state") not in RUN_STATES or data.get("mode") not in ("Story", "Endless"):
            return None
        if data.get("difficulty") not in DIFFICULTIES:
            return None
        for key in ("level", "score", "lives", "combo") + COUNTERS:
            if type(data.get(key)) is not int or not 0 <= data[key] <= 10**12:
                return None
        if not 1 <= data["level"] <= 100000 or not 1 <= data["lives"] <= 5:
            return None
        if data["mode"] == "Story" and data["level"] > 10:
            return None
        if type(data.get("perfect")) is not bool:
            return None
        uuid.UUID(hex=data["run_id"])
        count, swaps, duration, reveal = level_settings(data["level"], data["difficulty"])
        if (data["swaps"], data["swap_duration"], data["reveal_frames"]) != (swaps, duration, reveal) and data["state"] != "story":
            return None
        cups = data["cups"]
        if not isinstance(cups, list) or len(cups) != (0 if data["state"] == "story" else count):
            return None
        if cups:
            if any(type(c["slot"]) is not int for c in cups):
                return None
            if sorted(c["slot"] for c in cups) != list(range(count)):
                return None
            if not 0 <= data["correct_id"] < count:
                return None
            for c in cups:
                for key in ("x", "y"):
                    value = c[key]
                    limit = 450 if key == "x" else 100
                    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > limit:
                        return None
        pair = data.get("swap_pair")
        if pair is not None:
            if not isinstance(pair, list) or len(pair) != 4 or any(type(v) is not int or not 0 <= v < count for v in pair):
                return None
            if pair[0] == pair[1] or pair[2] == pair[3]:
                return None
        return data
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


class RunProgress:
    def __init__(self, session, path):
        self.session = session
        self.path = path

    def snapshot(self):
        g = self.session
        phase = g.paused_state if g.state == "paused" else g.state
        data = {key: getattr(g, key) for key in COUNTERS}
        data.update({key: getattr(g, key) for key in ("mode", "difficulty", "level", "score", "lives", "combo", "perfect", "run_id")})
        data.update(version=1, state=phase,
                    cups=[dict(slot=c.slot, x=c.x, y=c.y) for c in g.cups],
                    swap_pair=None)
        if g.swap_pair is not None and g.cups:
            a, b, sa, sb = g.swap_pair
            data["swap_pair"] = [a.cid, b.cid, sa, sb]
        return data

    def save(self):
        data = self.snapshot()
        if data["state"] not in RUN_STATES or not persist(self.path, data):
            return False
        self.session.saved_run = data
        return True

    def clear(self):
        self.session.saved_run = None
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass

    def restore(self):
        data = load_run(self.path)
        if data is None:
            self.session.saved_run = None
            return False
        g = self.session
        g.saved_run = data
        for key in ("mode", "difficulty", "level", "score", "lives", "combo", "perfect", "run_id"):
            setattr(g, key, data[key])
        g.save_failed = g.reward_failed = False
        if data["state"] == "story":
            g.views.show_story()
            return True
        g.rounds.start_level(refresh=False)
        for key in COUNTERS:
            setattr(g, key, data[key])
        for cup, saved in zip(g.cups, data["cups"]):
            cup.slot, cup.x, cup.y = saved["slot"], saved["x"], saved["y"]
            cup.render()
        pair = data["swap_pair"]
        g.swap_pair = (g.cups[pair[0]], g.cups[pair[1]], pair[2], pair[3]) if pair else None
        g.state = data["state"]
        if g.state in ("reveal", "result", "retry"):
            g.coin.goto(g.cups[g.correct_id].x, -40)
            g.coin.showturtle()
        else:
            g.coin.hideturtle()
        messages = {
            "reveal": ("Remember the coin", "Watch which cup holds it."),
            "shuffle": ("Follow the cup", ""),
            "select": ("Where is the coin?", g.rounds.selection_hint()),
            "result": ("Round complete", "Continue to the next table."),
            "retry": ("Not this cup", f"{g.lives} lives left."),
        }
        g.views.set_message(*messages[g.state])
        if g.state == "select" and g.hint_frames:
            remaining = g.hint_frames
            g.views.show_coin_hint()
            g.hint_frames = remaining
        g.last_tick, g.frame_credit = time.monotonic(), 0.0
        g.screen.update()
        return True
