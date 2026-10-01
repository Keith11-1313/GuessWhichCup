"""Cosmetic cup collection and transactional local progression."""
import copy
import json
import os
from pathlib import Path
import random
import tempfile

PROFILE_FILE = Path(__file__).resolve().parent / 'lantern_profile.json'
DRAW_COST = 3
# Weights total 10,000. Each rarity currently contains one original cup.
CUPS = (
    ('normal', 'Brass Keepsake', 'Normal', 5000, '#e2ad62'),
    ('uncommon', 'Garden Glaze', 'Uncommon', 2700, '#92cfac'),
    ('rare', 'Moon Porcelain', 'Rare', 1500, '#91bde8'),
    ('epic', 'Violet Sigil', 'Epic', 600, '#c49aef'),
    ('legendary', 'Sun Crown', 'Legendary', 180, '#ffdd92'),
    ('mythic', 'Astral Eclipse', 'Mythic', 20, '#95f4ed'),
)


def fresh_profile():
    return {'version': 1, 'tickets': 3, 'owned': ['normal'],
            'equipped': 'normal', 'rewards': [], 'draws': 0}


def load_profile(path):
    profile = fresh_profile()
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return profile
        for key in ('tickets', 'draws'):
            if type(data.get(key)) is int and data[key] >= 0:
                profile[key] = data[key]
        known = {cup[0] for cup in CUPS}
        if isinstance(data.get('owned'), list):
            profile['owned'] = list(dict.fromkeys(['normal'] +
                [item for item in data['owned'] if isinstance(item,str) and item in known]))
        if data.get('equipped') in profile['owned']:
            profile['equipped'] = data['equipped']
        if isinstance(data.get('rewards'), list):
            profile['rewards'] = list(dict.fromkeys(
                item for item in data['rewards'] if isinstance(item,str)))
    except (OSError, ValueError):
        pass
    return profile


def persist(path, profile):
    """Replace a save atomically. A failed write leaves the previous save intact."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,
                prefix=path.name+'.',suffix='.tmp',delete=False) as file:
            temporary = file.name
            json.dump(profile,file,indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary,path)
        return True
    except OSError:
        return False
    finally:
        if temporary and os.path.exists(temporary):
            try:
                os.unlink(temporary)
            except OSError:
                pass


def reward(path, profile, key=None):
    """One ticket per correct round; Story chapters pay once per difficulty."""
    if key and key in profile['rewards']:
        return 0
    updated = copy.deepcopy(profile)
    updated['tickets'] += 1
    if key:
        updated['rewards'].append(key)
    if not persist(path,updated):
        return -1
    profile.update(updated)
    return 1


def pick_skin(roll):
    if not 0 <= roll < 10000:
        raise ValueError('Draw roll must be between 0 and 9999')
    total = 0
    for cup in CUPS:
        total += cup[3]
        if roll < total:
            return cup[0]


def draw(path, profile, rng=random):
    if profile['tickets'] < DRAW_COST:
        return None, 'Not enough tickets'
    selected = pick_skin(rng.randrange(10000))
    updated = copy.deepcopy(profile)
    updated['tickets'] -= DRAW_COST
    updated['draws'] += 1
    duplicate = selected in updated['owned']
    if duplicate:
        updated['tickets'] += 1
    else:
        updated['owned'].append(selected)
    if not persist(path,updated):
        return None, 'Save failed; no tickets spent'
    profile.update(updated)
    return selected, 'duplicate' if duplicate else 'new'


def equip(path, profile, skin):
    if skin not in profile['owned']:
        return False
    updated = copy.deepcopy(profile)
    updated['equipped'] = skin
    if not persist(path,updated):
        return False
    profile.update(updated)
    return True
