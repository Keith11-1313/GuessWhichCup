"""File-based high-score storage kept separate from the game screen."""

import json
import os
import tempfile


def load_scores(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return {}
        return {key: value for key, value in data.items()
                if isinstance(key, str) and type(value) is int and value >= 0}
    except (OSError, ValueError):
        return {}


def save_score(path, scores, key, score):
    """Save only when the new score beats the existing score."""
    old = scores.get(key, 0)
    old = old if type(old) is int and old >= 0 else 0
    if type(score) is not int or score < 0 or score <= old:
        return False

    updated = dict(scores, **{key: score})
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                dir=path.parent, prefix=path.name + '.', suffix='.tmp', delete=False) as file:
            temporary = file.name
            json.dump(updated, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        scores[key] = score
        return True
    except OSError:
        return False
    finally:
        if temporary and os.path.exists(temporary):
            try:
                os.unlink(temporary)
            except OSError:
                pass
