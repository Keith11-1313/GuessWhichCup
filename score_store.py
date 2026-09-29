"""File-based high-score storage kept separate from the game screen."""

import json


def load_scores(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_score(path, scores, key, score):
    """Save only when the new score beats the existing score."""
    if score <= int(scores.get(key, 0)):
        return False

    scores[key] = score
    try:
        path.write_text(json.dumps(scores, indent=2), encoding='utf-8')
        return True
    except OSError:
        return False
