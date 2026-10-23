# Guess Which Cup: Lantern House

A local pixel memory game. Join Mira, Theo and Jun for a night that moves
from the welcome hall to the kitchen, midnight terrace, and sunrise.

## Play

Double-click Play.bat on Windows, or run `python what_the_cup.py`.
Python 3 with Tkinter is required. No pip packages or internet are needed.

### Windows executable

Open the executable inside the desired version folder in `dist/` to play without installing Python. You can share
that single executable; artwork and sounds are included. Keep it in a writable
folder, such as Desktop or Documents. The executable stores `lantern_profile.json`
and `what_the_cup_scores.json` beside itself. To carry over existing progress,
copy those save files beside the executable before starting it. Also copy
`lantern_run.json` when you want to carry over a saved active run.

To rebuild after editing the source, install the optional packaging tool once:
`python -m pip install --target .build-tools pyinstaller==6.22.0`
Then run `Build.bat`. Build output is ignored by Git; player saves are never
included in the executable.

`VERSION` sets the next build's version. Outputs use
`dist/vVERSION/GuessWhichCup-vVERSION.exe`. Update VERSION before an explicitly
requested build; Build.bat refuses to overwrite an existing version. Building
is manual. Preview versions are review builds, not a published release.

Current local build locations:

- `dist/v1.0/GuessWhichCup.exe`: older executable with the original filename.
- `dist/v2.0/GuessWhichCup-v2.0.exe`: versioned executable.

`VERSION` currently contains `2.0`. Existing executables do not update when
source or PNGs change. Check the source separately before choosing a new
version and building; the presence of a build does not prove it includes the
latest changes. No build is part of a documentation update.

Each version stores its JSON saves in its own folder. Copy the save files to
another version's folder to carry progress over.

Story has ten chapters, with one brief dialogue line before each round.
Mira, Theo and Jun appear through their names and dialogue, without character
sprites or portraits. Press Play once to start the round.
Watch the coin, track its cup, and choose when
movement stops. Results wait for you. Endless starts directly in the neon
afterparty and continues until your lives run out.

Easy gives five lives, Normal three, and Hard one. Cup counts grow from
three to four at chapter 4, five at chapter 7, and six at chapter 10.
The instruction always shows the current cup count.
In Endless rounds 11 onward, a tiny amber glint briefly appears beneath the
correct cup after shuffling. It lasts about 0.9 seconds and clears on selection
or when leaving the round. Story and Endless rounds 1–10 keep normal tracking.
Footer controls pair a keyboard keycap with a clickable action label.
The sound control is available on every screen; S mutes both music and effects.

| Control | Action |
| --- | --- |
| Mouse | Buttons, cabinet cards, cup selection |
| 1 through the visible cup count | Choose a cup |
| Enter or Space | Play, resume a saved run, Next, Retry, draw, reveal, or confirm duplicate conversion |
| P | Open pause options or resume gameplay |
| S | Toggle sound |
| [ and ] | Lower and raise music volume by 5% respectively |
| Tab | Switch menu mode |
| Left and Right | Change menu difficulty |
| C | Cup cabinet from the menu |
| H | Help outside a run; pause options during a run |
| M | Pause options during a run; menu elsewhere |
| R | Restart the selected mode, except while paused |
| Escape | Pause/resume during a run; back elsewhere; close from the menu |

## Cup cabinet

Open Cup cabinet from the menu. Start with three tickets: enough for one draw.
A draw costs three tickets. A duplicate returns one ticket. Equip an owned cup
by clicking its card, or use Equip after a draw. All cups on a table use the
same cosmetic skin, so the collection cannot reveal the hidden coin.
The large menu cup also displays the equipped skin; it is drawn separately
from the room background PNG.

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
Unowned cups carry a lock overlay. A new-cup draw opens that lock before the
reveal; duplicates keep their existing unlocked state. Enter during gift
opening skips to the cup reveal without spending additional tickets.
Duplicate reveals wait for Next (or Enter), then shrink the cup into a ticket
and show +1 ticket. The cup stays visible until that confirmation; waiting
does not start conversion. Keep browsing returns to the cabinet afterward.
The draw transaction, including a duplicate refund, is saved before gift
opening; Next triggers presentation only and cannot award another refund.

Opening and reveal screens use a darker room PNG so the cup, rarity and
ticket remain readable. The ticket has notched edges, an inset border,
perforations and a coin emblem. The small UI ticket and larger conversion
reward use the same PNG. Correct guesses show floating points and +1 ticket when a ticket was actually saved.
These animations never change balances; saving happens before the visual cue.
The window's title-bar icon follows the equipped cup immediately. Windows
receives a dedicated taskbar identity instead of grouping the game as Python;
the taskbar appearance still needs manual verification. The executable's file
icon is a separate, static build asset.

Collection, tickets, claimed chapter rewards, and equipped cup are saved to
`lantern_profile.json`. High scores remain in `what_the_cup_scores.json`.
Writes use atomic replacement; a failed draw save spends no tickets.
M, P or Escape during a run opens a pause overlay. Resume returns to the exact
frozen board. Save & Menu saves a checkpoint and returns to the main menu;
Save & Exit saves first, then closes the game. Failed saves leave the table
paused with an error. Resume run on the main menu restores `lantern_run.json`,
including a shuffle in progress, score, hearts, combo and chapter/round.
New game starts from chapter/round 1 and clears the old checkpoint.
Cup ownership, tickets and high scores remain in their existing save files.
Endless ticket rewards use a run/round identifier so reloading a checkpoint
does not award the same ticket again.
Losing the last heart opens a dedicated Party over scene with final score,
best score, and chapter/round reached. Play again restarts the selected mode;
Menu returns to the party menu. Cups, tickets and saved high scores are kept.
Its editable illustration is `assets/backgrounds/party_over.png`.

## Project map

- `what_the_cup.py`: shared session setup, application entry and timer loop.
- `game_screens.py`: menu, story, HUD, messages and common drawing helpers.
- `round_logic.py`: round setup, shuffling, scoring and win/loss resolution.
- `input_controls.py`: keyboard bindings, click routing and navigation.
- `game_objects.py`: cup sprites, click targets, text pens and sound feedback.
- `game_audio.py`: a separate background-music channel with clean mute/close.
- `game_theme.py`: process-only registration of the bundled pixel font.
- `game_config.py`: level scaling, colors and paths.
- `party_art.py`: small PNG loader, image placement and scalable UI borders.
- `assets/`: editable PNG cups, backgrounds, title and coin.
- `pause_menu.py`: frozen-board pause overlay and Save & Menu / Save & Exit.
- `run_progress.py`: validated, atomic active-run checkpoint storage.
- `visual_effects.py`: points, earned-ticket and duplicate-conversion animations.
- `party_story.py`: narrative beats and chapter locations.
- `cup_collection.py`: odds, transactions and validated profile storage.
- `collection_screens.py`: cabinet, odds and animated draw reveal.
- `score_store.py`: validated high-score loading and atomic writes.
- `test_game.py`: deterministic gameplay, collection and layout regression tests.
- `qa_player_flow.py`: real Tk mouse/key-event player-flow QA with temporary saves.

`Game` constructs the main gameplay components: `views` (`GameScreens`), `rounds`
(`RoundLogic`), `controls` (`InputControls`), and `cabinet` (`CupCabinet`).
It also constructs `progress` (`RunProgress`), `pause_menu` (`PauseMenu`) and
`effects` (`VisualEffects`) for checkpoints, pause controls and reward cues.
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
nearest-pixel cup scaling and bundled Pixelify Sans lettering. Numbers use
bold Consolas for readability.
Sounds are original soft WAV chimes in `assets/sounds`, played asynchronously
on Windows. Other platforms stay silent; no system notification or bell is
used as a fallback. Press S to toggle sound. The desktop window is
1000 x 700. Runtime checks target Windows; an executable must be checked separately
after building.

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

The latest regression run passed all 43 tests after the darker reveal
background and ticket artwork update. Earlier full player-flow QA covered all
ten Story chapters. That earlier run does not replace checking the latest
cabinet interaction manually.

Before a team handoff or a new executable build, check these in the actual window:

- Reveal a duplicate and wait: the cup must stay visible. Click Next (or press
  Enter) and verify it turns into the ticket without adding another refund.
- Draw a new cup, equip it, and check the menu cup, gameplay cups and title-bar icon.
- Win a round: inspect the points icon and the ticket icon when a ticket is earned.
- Pause during a shuffle, resume, then save and return to the menu. Restart
  the source game and use Resume run to check the frozen board is restored.
- Lose the last heart and check Party over, Play again and Menu.
- Inspect title, text, icons and buttons for clipping at the normal window size.

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
| `assets/backgrounds` | Hall, kitchen, terrace, dawn and afterparty | 940 x 410 |
| `assets/backgrounds` | `menu.png` | 435 x 410 |
| `assets/backgrounds` | `cabinet_reveal.png` (dimmed hall for gift opening and reveal) | 940 x 410 |
| `assets/backgrounds` | `party_over.png` | 936 x 252 |
| `assets/ui` | `title.png`; `coin.png` | 440 x 46; 24 x 24, transparent |
| `assets/ui` | `heart_full.png`, `heart_empty.png` | 24 x 18, transparent |
| `assets/ui` | `coin_hint.png` | 9 x 7, transparent |
| `assets/ui` | `app_icon.png`; `app_icon.ico` | Brass Keepsake window and executable icons |
| `assets/ui` | Button icons and `_dark` variants, except tickets | 16 x 16, transparent |
| `assets/ui` | `ticket.png`, `ticket_dark.png` | 20 x 16, transparent; conversion reward scales to 80 x 64 |
| `assets/ui` | `lock_badge.png`; `unlock_0.png` through `unlock_3.png` | 32 x 34; 24 x 28, transparent |

The title is an editable brass-sign PNG. Menu statistics use separate labels
instead of slash-separated strings. Reward popups pair points with a coin
icon and earned tickets with a ticket icon.

The UI uses bundled Pixelify Sans, licensed under the SIL Open Font License
in `assets/fonts/OFL.txt`. Windows loads it only for this process; the player
does not need to install the font. Dialogue wraps before the action buttons.
Numbers use bold Consolas for clear digit shapes while surrounding words keep
the pixel font. Cup number labels are larger than the small counter text.

`assets/sounds/lantern_party.wav` is an original 48-second, 16-bit PCM lounge loop
with warm sustained chords, low bass and sparse soft bells. It starts at 20%
music-channel volume. Use [ and ] to adjust by 5%; change
`DEFAULT_MUSIC_VOLUME` in `game_audio.py` to tune the starting level.
The reveal, correct, wrong, win, click and unlock effects use separate WAVs.
Music uses a separate Windows
audio channel, so feedback does not cut off the loop. S stops both channels;
closing the game releases the music device. Tests and QA leave music disabled.
Volume adjustment affects only this game's music channel, never Windows master
volume. The four `assets/ui/unlock_*.png` frames and `lock_badge.png` remain
editable image assets.

Lives use one filled heart per remaining life and empty hearts for lives lost.
Easy shows five heart slots, Normal three, and Hard one. To change audio,
replace `reveal.wav`, `correct.wav`, `wrong.wav`, or `win.wav` in
`assets/sounds` with short PCM WAV files. Keep the filenames; the game uses
only Python's standard library with Windows audio APIs; no audio package is needed.

Backgrounds include scenery and the table, without character artwork.
Cups are scaled automatically for the cabinet,
table and draw reveal. Dialogue, scores and button text stay in Python, where
the team can change them directly. `party_art.py` names every image it loads;
a missing file reports its full path. Include the whole `assets` folder when
copying or submitting the project.

World artwork uses an original cozy countryside pixel-art direction: timber,
warm lanterns, muted foliage, copper kitchen details and layered forest skies.
Each location has its own palette. Keep the center cup lane visually quiet.
The menu backdrop contains no cup; its equipped cup remains a separate image.
Characters appear only in the short story dialogue.

Read `game_config.py`, then `what_the_cup.py`, `input_controls.py`, and
`round_logic.py` to follow gameplay. Open the drawing modules when working on
appearance. `self.session` in a component is the same `Game` object that owns
the score, lives, current phase and sprites; it is not another saved game.

| Phase | What happens | Next phase |
| --- | --- | --- |
| `menu` | Choose mode and difficulty | `story` or `reveal` |
| `story` | Read one brief line, then press Play | `reveal` |
| `reveal` | Lift the cup holding the coin | `shuffle` |
| `shuffle` | Animate swaps and update numbered positions | `select` |
| `select` | Accept one valid cup choice | `resolving` |
| `resolving` | Lock input and calculate the result | `result`, `retry`, `over`, or `victory` |
| `result`, `retry` | Wait for Next or Retry | Next chapter or the same round |
| `paused` | Resume, Save & Menu, or Save & Exit | Previous phase, menu, or closed |
| `gacha_opening` | Gift opening; Enter skips to reveal | `gacha_reveal` |
| `gacha_reveal` | New cup: Equip or browse. Duplicate: Next starts conversion, then browse | `cabinet` |

Cup `cid` identifies the same object throughout a round. Cup `slot` changes
after a swap and matches the numbered table position. `correct_id` indexes
the cup list, so selection compares the chosen object with the original cup.
This distinction is the first thing to check if a shuffle or guess goes wrong.

For a breakpoint, follow a click from `controls.on_click()` to
`rounds.choose()`, then the appropriate result method and `views.set_message()`.
For collection issues, follow `controls.collection_action()` to the cabinet
and `cup_collection.py`. Draws save before the opening animation begins;
skipping that animation cannot award another draw.

Keep the profile and high-score JSON files, plus `lantern_run.json` if present, when cleaning a player's copy. Missing saves
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
