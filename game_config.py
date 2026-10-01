"""Small, easy-to-explain configuration module for What The Cup."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAVE_FILE = ROOT / 'what_the_cup_scores.json'

WIDTH, HEIGHT = 1000, 700
FRAME_MS = 17
STORY_LEVELS = 10

COLORS = {
    'background': '#191522',
    'panel': '#30213b',
    'panel_light': '#46334f',
    'white': '#fff0d9',
    'muted': '#cbb8c9',
    'gold': '#f2bf68',
    'gold_dark': '#f2bf68',
    'danger': '#ff8294',
    'success': '#67e8b0',
}

DIFFICULTIES = {
    'Easy':   {'extra_swaps': 0, 'duration': 1.35, 'reveal': 1.45, 'lives': 5},
    'Normal': {'extra_swaps': 2, 'duration': 1.00, 'reveal': 1.00, 'lives': 3},
    'Hard':   {'extra_swaps': 5, 'duration': 0.72, 'reveal': 0.70, 'lives': 1},
}


def level_settings(level, difficulty):
    """Return cup count and timing values for one level."""
    tune = DIFFICULTIES[difficulty]
    cups = min(6, 3 + (level - 1) // 3)
    swaps = 4 + level * 2 + tune['extra_swaps']
    frames = max(9, round(max(15, 45 - (level - 1) * 3) * tune['duration']))
    reveal = max(65, round(max(100, 175 - (level - 1) * 6) * tune['reveal']))
    return cups, swaps, frames, reveal
