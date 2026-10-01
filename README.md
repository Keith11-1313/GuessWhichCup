# Guess Which Cup: Lantern House

A local pixel memory game. Join Mira, Theo and Jun for a night that moves
from the welcome hall to the kitchen, midnight terrace, and sunrise.

## Play

Double-click Play.bat on Windows, or run `python what_the_cup.py`.
Python 3 with Tkinter is required. No pip packages or internet are needed.

Story has ten chapters, with two short dialogue beats before each round.
Press Continue, then Play. Watch the spark, track its cup, and choose when
movement stops. Results wait for you. Endless starts directly in the neon
afterparty and continues until your lives run out.

Easy gives five lives, Normal three, and Hard one. Cup counts grow from
three to four at chapter 4, five at chapter 7, and six at chapter 10.
The instruction always shows the current cup count.

| Control | Action |
| --- | --- |
| Mouse | Buttons, cabinet cards, cup selection |
| 1 through the visible cup count | Choose a cup |
| Enter / Space | Story dialogue, Play, Next, Retry, cabinet draw, reveal |
| P | Pause or resume gameplay |
| S | Toggle sound |
| Tab / Left / Right | Menu mode / difficulty |
| C | Cup cabinet from the menu |
| H | Help |
| M | Menu |
| R | Restart the selected mode |
| Escape | Back; close from the menu |

## Cup cabinet

Open Cup cabinet from the menu. Start with three tickets: enough for one draw.
A draw costs three tickets. A duplicate returns one ticket. Equip an owned cup
by clicking its card, or use Equip after a draw. All cups on a table use the
same cosmetic skin, so the collection cannot reveal the hidden spark.

Earn one ticket for each Story chapter's first clear at a given difficulty,
and one ticket for every correct Endless round. Repeated inputs cannot award
the same round twice. Odds are also available inside the cabinet.

| Rarity | Cup | Chance |
| --- | --- | --- |
| Normal | Brass Keepsake | 50% |
| Uncommon | Garden Glaze | 27% |
| Rare | Moon Porcelain | 15% |
| Epic | Violet Sigil | 6% |
| Legendary | Sun Crown | 1.8% |
| Mythic | Astral Eclipse | 0.2% |

Mythic appears as an unseen silhouette until discovered. Each draw uses the
same independent odds. There is no pity counter.

Collection, tickets, claimed chapter rewards, and equipped cup are saved to
`lantern_profile.json`. High scores remain in `what_the_cup_scores.json`.
Writes use atomic replacement; a failed draw save spends no tickets.
Story runs restart at chapter 1; chapter rewards and cups persist.

## Project map

- `what_the_cup.py`: screens, input, state machine and elapsed-time animation.
- `game_config.py`: level scaling, colors and paths.
- `party_art.py`: original pixel sprites and five setting-specific backgrounds.
- `party_story.py`: narrative beats and chapter locations.
- `cup_collection.py`: odds, transactions and validated profile storage.
- `collection_screens.py`: cabinet, odds and animated draw reveal.
- `score_store.py`: validated high-score loading and atomic writes.
- `test_game.py`: deterministic gameplay, collection and layout regression tests.
- `qa_player_flow.py`: real Tk mouse/key-event player-flow QA with temporary saves.

The game uses built-in Turtle/Tkinter, original pixel title lettering,
nearest-pixel cup sprites and Segoe UI body text (system fallback elsewhere).
Sounds use Windows notifications or a system bell. The desktop window is
1000 x 700. This release was verified on Windows.

## Verify

`python -B -m unittest -v test_game`

`python -B qa_player_flow.py`

Both need a desktop session and isolate saves in temporary directories.
The player-flow check covers all ten chapters at actual animation speed,
a wrong guess and retry, keyboard selection, gacha, equip, persistence,
Endless, and pause. It takes a few minutes.

Optional screenshots: `python -B qa_player_flow.py --screenshots PATH`.
Only that developer screenshot option needs Pillow.

## Research applied

- https://www.nngroup.com/articles/progressive-disclosure/
- https://gameaccessibilityguidelines.com/full-list/
- https://docs.python.org/3/library/tkinter.html

Secondary information lives in Help, the cabinet and Odds. Gameplay presents
one immediate instruction. Story text is short and player-paced; backgrounds
follow the chapter context. Cosmetic draw transactions do not change gameplay.
