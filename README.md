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

- `what_the_cup.py`: shared session setup, application entry and timer loop.
- `game_screens.py`: menu, story, HUD, messages and common drawing helpers.
- `round_logic.py`: round setup, shuffling, scoring and win/loss resolution.
- `input_controls.py`: keyboard bindings, click routing and navigation.
- `game_objects.py`: cup sprites, click targets, text pens and sound feedback.
- `game_config.py`: level scaling, colors and paths.
- `party_art.py`: small PNG loader, image placement and scalable UI borders.
- `assets/`: editable PNG cups, backgrounds, characters, title and spark.
- `party_story.py`: narrative beats and chapter locations.
- `cup_collection.py`: odds, transactions and validated profile storage.
- `collection_screens.py`: cabinet, odds and animated draw reveal.
- `score_store.py`: validated high-score loading and atomic writes.
- `test_game.py`: deterministic gameplay, collection and layout regression tests.
- `qa_player_flow.py`: real Tk mouse/key-event player-flow QA with temporary saves.

`Game` constructs four components: `views` (`GameScreens`), `rounds`
(`RoundLogic`), `controls` (`InputControls`), and `cabinet` (`CupCabinet`).
Each constructor lists its dependencies. Views receive the session; rounds
and the cabinet also receive views; controls receive all three components.
There is no multiple inheritance or lookup of sibling methods through Game.
The session owns runtime resources and shared data, including explicit save
paths, image references and a reusable pool of six cup sprites. Navigation
lives in controls, chapter progression in rounds, and drawing in views.

Sprites use public Turtle methods to hide, reset and show. The pool stays
bounded across retries and menu visits. QA discovers the input canvas through
public Tk widget traversal rather than Turtle's internal widget attributes.

To trace a guess, start at `InputControls.on_click()`, which calls
`RoundLogic.choose()`. A correct guess goes to `resolve_correct_guess()`;
a mistake goes to `resolve_wrong_guess()`. The result is drawn through
`GameScreens.set_message()`. `Game.update()` advances animations and refreshes
the window. The state gates in these methods prevent repeated input from
awarding a round twice.

The game uses built-in Turtle/Tkinter, original PNG pixel artwork,
nearest-pixel cup scaling and Segoe UI body text (system fallback elsewhere).
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
Screenshot mode brings the game to the foreground and captures a paused
shuffle in every chapter. Inspect those images as well as the final overview.
The tests also check that rendered cup images sit above the scenery, since a
correct visibility flag alone cannot detect a cup covered by the background.

For consistent formatting, optionally install `requirements-dev.txt`, then
run `python -m black .`. The formatter is not required to play or test the game.

## Team debugging for finals

Use Python 3.10 or newer with Tkinter. Run `python -B what_the_cup.py` from a
terminal while debugging so error messages remain visible. `-B` prevents
generated bytecode folders. Start with the test commands above after a change.
Both checks receive temporary save paths directly and preserve player saves.

### Editing artwork

For future asset work, follow this project workflow:

1. Create or revise the artwork in a temporary drawing/export script.
2. Export the final artwork as PNG files into the appropriate `assets` folder.
3. Make the game load those PNGs through `party_art.load_assets()`; do not put
   pixel-by-pixel art generation back into the runtime game code.
4. Keep gameplay logic and editable dialogue separate from artwork. Small
   scalable UI borders may stay in code so buttons fit their text.
5. Run the regression tests and player-flow QA, then visually inspect the
   actual game for alignment, transparency, scaling and drawing order.
6. Remove temporary exporters, previews, caches and unused files after
   verification. Keep the final PNGs, runtime source, tests and instructions.

This is the default workflow for contributors and coding assistants working
on new assets for this project.

Open the PNG files in a pixel editor and save over the same filename. Restart
the game after an edit. Keep PNG format, transparency and the original canvas
size so alignment and cup hitboxes stay correct. No image-generation code or
Pillow installation is needed to play the game.

| Folder | Editable files | Size |
| --- | --- | --- |
| `assets/cups` | Six rarity cups and `unknown.png` | 32 x 34, transparent |
| `assets/characters` | `mira.png`, `theo.png`, `jun.png` story portraits | 16 x 25, transparent |
| `assets/backgrounds` | Hall, kitchen, terrace, dawn and afterparty | 940 x 410 |
| `assets/backgrounds` | `menu.png` | 435 x 410 |
| `assets/ui` | `title.png`; `spark.png` | 360 x 28; 18 x 18, transparent |

Backgrounds include scenery, the table and small party guests. Story portraits
are separate character images. Cups are scaled automatically for the cabinet,
table and draw reveal. Dialogue, scores and button text stay in Python, where
the team can change them directly. `party_art.py` names every image it loads;
a missing file reports its full path. Include the whole `assets` folder when
copying or submitting the project.

Read `game_config.py`, then `what_the_cup.py`, `input_controls.py`, and
`round_logic.py` to follow gameplay. Open the drawing modules when working on
appearance. `self.session` in a component is the same `Game` object that owns
the score, lives, current phase and sprites; it is not another saved game.

| Phase | What happens | Next phase |
| --- | --- | --- |
| `menu` | Choose mode and difficulty | `story` or `reveal` |
| `story` | Continue through two dialogue pages | `reveal` |
| `reveal` | Lift the cup holding the spark | `shuffle` |
| `shuffle` | Animate swaps and update numbered positions | `select` |
| `select` | Accept one valid cup choice | `resolving` |
| `resolving` | Lock input and calculate the result | `result`, `retry`, `over`, or `victory` |
| `result` / `retry` | Wait for Next or Retry | Next chapter or the same round |
| `paused` | Stop animation and selection | The previous gameplay phase |

Cup `cid` identifies the same object throughout a round. Cup `slot` changes
after a swap and matches the numbered table position. `correct_id` indexes
the cup list, so selection compares the chosen object with the original cup.
This distinction is the first thing to check if a shuffle or guess goes wrong.

For a breakpoint, follow a click from `controls.on_click()` to
`rounds.choose()`, then the appropriate result method and `views.set_message()`.
For collection issues, follow `controls.collection_action()` to the cabinet
and `cup_collection.py`. Draws save before the opening animation begins;
skipping that animation cannot award another draw.

Keep the two JSON save files when cleaning a player's copy. Missing saves
start fresh; deleting them resets that player's progress. Tests and QA belong
with the source so the team can repeat verification. The only generated files
to discard are `__pycache__`, `.pyc` files and abandoned `.tmp` files after the
game has closed. No downloaded assets or runtime packages are needed.

## Research applied

- https://www.nngroup.com/articles/progressive-disclosure/
- https://gameaccessibilityguidelines.com/full-list/
- https://docs.python.org/3/library/tkinter.html

Secondary information lives in Help, the cabinet and Odds. Gameplay presents
one immediate instruction. Story text is short and player-paced; backgrounds
follow the chapter context. Cosmetic draw transactions do not change gameplay.
