# Guess Which Cup: Lantern House

A local pixel memory game. Enter Lantern House's closing-night challenge:
find the lucky coin at ten tables to win Brass Keepsake. Mira, Theo and Jun
host the hall, kitchen, terrace and sunrise final. Endless keeps the afterparty going.

## Play

Double-click Play.bat on Windows, or run `python WhatTheCup.py`.
Python 3.10 or newer with Tkinter and Pillow is required. Install the source
dependencies once with `python -m pip install -r Requirements.txt`.
The game then runs offline. Packaged executables include their dependencies.

### Windows executable

Open the executable inside the desired version folder in `dist/` to play without installing Python. You can share
that single executable; artwork and sounds are included. Keep it in a writable
folder, such as Desktop or Documents. The executable stores `LanternProfile.json`
and `WhatTheCupScores.json` beside itself. To carry over existing progress,
copy those save files beside the executable before starting it. Also copy
`LanternRun.json` when you want to carry over a saved active run.

To rebuild after editing the source, install the optional packaging tool once:
`python -m pip install --target .build-tools pyinstaller==6.22.0`
Then run `Build.bat`. Build output is ignored by Git; player saves are never
included in the executable.

`Version` sets the next build's version. Outputs use
`dist/vVersion/GuessWhichCup-vVersion.exe`. Update Version before an explicitly
requested build; Build.bat refuses to overwrite an existing version. Building
is manual. Preview versions are review builds, not a published release.

Current local build locations:

- `dist/v1.0/GuessWhichCup.exe`: older executable with the original filename.
- `dist/v2.0/GuessWhichCup-v2.0.exe`: versioned executable.

`Version` currently contains `2.0`. Existing executables do not update when
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

Easy gives five lives, Normal three, and Hard one. Story cup counts grow from
three to four at chapter 4, five at chapter 7, and six at chapter 10.
Endless adds cups at rounds 6, 11 and 16 instead. Its swap count caps at 24,
with at least 18 frames per swap and 75 frames to remember the coin.
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
| O | Open Settings; pauses an active run first |
| F11 | Toggle full screen |
| - and = | Lower and raise music volume by 5% respectively |
| Tab | Switch menu mode |
| Left and Right | Change menu difficulty |
| C | Cup cabinet from the menu |
| H | Help outside a run; pause options during a run |
| M | Pause options during a run; menu elsewhere |
| R | Restart the selected mode, including from pause |
| Escape | Pause/resume during a run; back elsewhere; close from the menu |

## Settings, countdown and animation

Open Settings with O, its clickable footer action, or the Settings button in
pause. It preserves the current board. Done or Escape returns to the previous
screen; an active run stays paused until Resume.

- Full screen: the complete logical canvas, images, text and pointer mapping
  scale together to fit the display. A full-bleed room backdrop fills the
  remaining aspect-ratio space. Nearest-neighbor image scaling preserves pixel
  edges. F11 switches back without changing the game state.
- Animation: eased cup lifts, brief scene-reveal curtains, animated hover
  outlines, win/loss particles, slow lantern glow and a few background motes.
  Ambient effects stay behind the playable cups and freeze during pause.
  Turn it off for reduced motion; gameplay timings stay unchanged.
- Answer timer: a visible seconds label and shrinking bar after the cups stop.
  It starts at 12 seconds on Easy, 10 on Normal and 8 on Hard. Endless reduces
  this by one second per ten rounds, down to five seconds. Expiration reveals
  the coin and costs exactly one life. Pause and Settings freeze the countdown.
  The timer is automatic. There is no timer setting or Gameplay tab.
- Audio tab: Master controls all game audio. Music and Game sounds have
  independent volume sliders, step buttons and persistent percentages.
  Effective channel gain is Master multiplied by the channel level. Master
  at zero mutes all channels; raising it restores sound. S is a shortcut for
  zero/restored Master. - and = change Music. There is no separate Mute All
  button or hotkey sentence inside Settings.
- The two Settings tabs are Audio and Display; Done returns to the prior screen.

Preferences save to `LanternSettings.json` beside the profile. Failed preference
writes show an error in Settings. Run checkpoints include the remaining timer;
legacy checkpoints without a timer receive a fresh automatic allowance when restored.
Version-1 profiles keep their cups/tickets; a claimed chapter-10 Story reward
is recognized as completed Story. Otherwise owned skins remain saved, but
Plain Cup is equipped and post-story access stays locked until completion.
New Endless checkpoints use the gentler progression; older Endless checkpoints
retain their saved cup count and shuffle timing until the next round.

## Cup cabinet

New players own and equip only **Plain Cup**. Finish Story's tenth table to
permanently earn and equip **Brass Keepsake**, unlock **Endless**, and unlock
**Cup cabinet**. Locked cards explain the requirement; keyboard shortcuts and
backend transactions enforce the same gate. The Story-completion reward is
saved atomically. If saving fails, Retry save claims it without awarding the
score bonus twice. Story victory's primary action opens the cabinet.

The cabinet contains 18 collectible skins: three designs in each of six
rarities, spread across three pages. Plain Cup remains available through its
own equip button and is not part of the draw pool. All cups at a gameplay
table share the equipped skin and the same animation frame, so animation
cannot reveal where the coin is hidden. Four PNG frames per skin animate
highlights and details in the cabinet, results, menu preview and gameplay.
Motion can be reduced in Display settings.

A single draw costs 3 tickets. Ten draws cost 30 tickets and use boosted odds
on **every pull**. The entire ten-draw purchase, all new ownership and all
refunds are one atomic transaction. Insufficient funds or a failed write
spends nothing. Duplicate results within the same batch count correctly.
The ten-card result screen waits for Next before animating duplicate cups
into ticket icons; new cups remain visible. Each duplicate returns 1 ticket.
Done returns to the cabinet; new result cards can equip their skin after
conversion. The animation never writes balances a second time.

Earn one ticket for each Story chapter's first clear at a given difficulty,
and one for each correct Endless round. Repeated inputs and checkpoint
replays cannot award the same round twice. Initial tickets remain banked
while the cabinet is locked.

| Rarity | Designs | Single | Each pull in ten-draw |
| --- | --- | --- | --- |
| Normal | Brass Keepsake, Oak Tumbler, Cream Ceramic | 50% | 35% |
| Uncommon | Garden Glaze, Fernstone, Cobalt Glaze | 27% | 32% |
| Rare | Moon Porcelain, Tideglass, Rose Quartz | 15% | 22% |
| Epic | Violet Sigil, Ember Sigil, Jade Serpent | 6% | 8% |
| Legendary | Sun Crown, Royal Hourglass, Phoenix Crest | 1.8% | 2.5% |
| Mythic | Astral Eclipse, Void Bloom, Aurora Prism | 0.2% | 0.5% |

A rarity is rolled first, then one of its three designs is selected uniformly.
Boosted odds are not a guaranteed rarity.

Mythic appears as an unseen silhouette until discovered. Each draw uses the
same independent single or ten-draw rarity odds shown above. There is no pity counter.
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

Collection, tickets, claimed chapter rewards, Story-completion status and equipped cup are saved to
`LanternProfile.json`. High scores remain in `WhatTheCupScores.json`. Older `what_the_cup_scores.json` files
are read automatically when the PascalCase file is absent; the next improved
score is written to `WhatTheCupScores.json`. Both filenames are ignored by Git.
Writes use atomic replacement; a failed draw save spends no tickets.
M, P or Escape during a run opens a pause overlay. Resume returns to the exact
frozen board. Restart run (circular arrow) begins the selected mode and
difficulty again from round or chapter 1, resets the run score and hearts,
and clears its checkpoint. Cups, tickets and high scores remain saved.
Save & Menu uses a home icon; Save & Exit uses a door-and-arrow icon. Save & Menu saves a checkpoint and returns to the main menu;
Save & Exit saves first, then closes the game. Failed saves leave the table
paused with an error. The saved-game home screen separates the navigation column from the saved
run summary. It shows mode, difficulty, location, chapter or round, score,
hearts and Story table marks. Resume is the primary action; New game, Cup
cabinet, Settings and How to play are secondary actions. Resume Story or Resume Endless restores `LanternRun.json`,
including a shuffle in progress, score, hearts, combo, chapter/round and
remaining answer time.
New game opens a dedicated setup screen. Mode cards explain
Story (10 chapters) and Endless (no round limit). Difficulty cards show their
starting hearts; a checkmark and border identify the current selections.
The shuffle pace is described below the cards. Card titles, captions, buttons
and saved-score values are measured against their available width before
drawing; clipping checks cover both modes and every difficulty. Gold action buttons start or
resume play. The saved-game summary includes the chapter location. Back or Escape returns to the
saved-run screen. Changing settings does not change the checkpoint. Start Story or Start Endless begins at chapter or
round 1 and replaces it; Enter resumes the saved run when one exists.
Cup ownership, tickets and high scores remain in their existing save files.
Endless ticket rewards use a run/round identifier so reloading a checkpoint
does not award the same ticket again.
Losing the last heart first holds the opened cups and revealed coin on the
board for about 1.5 seconds. Input cannot instantly skip this reveal; Enter
becomes available after the first half-second. Then Party over shows final
score, best score and chapter/round reached. Restart run begins at table 1;
Menu returns to the party menu. Cups, tickets and saved high scores are kept.
Its editable illustration is `assets/backgrounds/PartyOver.png`.

## Project map

- `WhatTheCup.py`: shared session setup, application entry and timer loop.
- `GameScreens.py`: menu, story, HUD, messages and common drawing helpers.
- `RoundLogic.py`: round setup, shuffling, scoring and win/loss resolution.
- `InputControls.py`: keyboard bindings, click routing and navigation.
- `GameObjects.py`: cup sprites, click targets, text pens and sound feedback.
- `GameAudio.py`: a separate background-music channel with clean mute/close.
- `GameSettings.py`: preference validation, persistence, full-screen toggle and settings overlay.
- `UiMotion.py`: scene transitions, hover cues, cup lift easing and result particles.
- `GameViewport.py`: one logical canvas with scaled image/font rendering and inverse mouse coordinates.
- `SoundMixer.py`: independent master/music/effects gain and effect-channel lifetime.
- `AmbientScene.py`: bounded background glow and motes behind gameplay.
- `GameTheme.py`: process-only registration of the bundled pixel font.
- `GameConfig.py`: level scaling, colors and paths.
- `PartyArt.py`: small PNG loader, image placement and scalable UI borders.
- `assets/`: editable PNG cups, backgrounds, title and coin.
- `PauseMenu.py`: frozen-board pause overlay and Save & Menu / Save & Exit.
- `RunProgress.py`: validated, atomic active-run checkpoint storage.
- `VisualEffects.py`: points, earned-ticket and duplicate-conversion animations.
- `PartyStory.py`: narrative beats and chapter locations.
- `CupCatalog.py`: starter, 18 designs, rarity colors and single/ten-draw odds.
- `SkinAnimation.py`: synchronized frame clock for all visible cup art.
- `CupCollection.py`: odds, transactions and validated profile storage.
- `CollectionScreens.py`: cabinet, odds and animated draw reveal.
- `ScoreStore.py`: validated high-score loading and atomic writes.
- `TestGame.py`: deterministic gameplay, collection and layout regression tests.
- `QaPlayerFlow.py`: real Tk mouse/key-event player-flow QA with temporary saves.

`Game` constructs the main gameplay components: `Views` (`GameScreens`), `Rounds`
(`RoundLogic`), `Controls` (`InputControls`), and `cabinet` (`CupCabinet`).
It also constructs `Progress` (`RunProgress`), `PauseMenu` (`PauseMenu`) and
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

To trace a guess, start at `InputControls.OnClick()`, which calls
`RoundLogic.Choose()`. A correct guess goes to `ResolveCorrectGuess()`;
a mistake goes to `ResolveWrongGuess()`. The result is drawn through
`GameScreens.SetMessage()`. `Game.Update()` advances animations and refreshes
the window. The state gates in these methods prevent repeated input from
awarding a round twice.

The game uses built-in Turtle/Tkinter, original PNG pixel artwork,
nearest-pixel cup scaling and bundled Pixelify Sans lettering. Numbers use
bold Consolas for readability.
Short sound effects are original soft WAV chimes in `assets/sounds`, played asynchronously
on Windows. Other platforms stay silent; no system notification or bell is
used as a fallback. Press S to toggle sound. The desktop window is
1000 x 700. Runtime checks target Windows; an executable must be checked separately
after building.

## Verify

`python -B -m unittest -v TestGame`

`python -B QaPlayerFlow.py`

Both need a desktop session and isolate saves in temporary directories.
The player-flow check covers all ten chapters at actual animation speed,
a wrong guess and retry, keyboard selection, gacha, equip, persistence,
Endless, and pause. It takes a few minutes.

Optional screenshots: `python -B QaPlayerFlow.py --screenshots PATH`.
The screenshot option uses Pillow, which is also a runtime dependency for
fullscreen image scaling.
Screenshot mode brings the game to the foreground and captures a paused
shuffle in every chapter. Inspect those images as well as the final overview.
The tests also check that rendered cup images sit above the scenery, since a
correct visibility flag alone cannot detect a cup covered by the background.

Regression coverage includes text bounds, scaled image/font coordinates,
inverse mouse mapping, separate audio levels, old checkpoint compatibility,
countdown timing and bounded background-animation items.

Before a team handoff or a new executable build, check these in the actual window:

- Reveal a duplicate and wait: the cup must stay visible. Click Next (or press
  Enter) and verify it turns into the ticket without adding another refund.
- Draw a new cup, equip it, and check the menu cup, gameplay cups and title-bar icon.
- Win a round: inspect the points icon and the ticket icon when a ticket is earned.
- Pause during a shuffle, resume, then save and return to the menu. Restart
  the source game and use Resume run to check the frozen board is restored.
- Lose the last heart and check Party over, Play again and Menu.
- Inspect title, text, icons and buttons for clipping at the normal window size.

For consistent formatting, optionally install `RequirementsDev.txt`, then
run `python -m black .`. The formatter is not required to play or test the game.

## Team debugging for finals

Use Python 3.10 or newer with Tkinter. Run `python -B WhatTheCup.py` from a
terminal while debugging so error messages remain visible. `-B` prevents
generated bytecode folders. Start with the test commands above after a change.
Both checks receive temporary save paths directly and preserve player saves.

### Editing artwork

For future asset work, follow this project workflow:

1. Create or revise the artwork in a temporary drawing/export script.
2. Export the final artwork as PNG files into the appropriate `assets` folder.
3. Make the game load those PNGs through `PartyArt.LoadAssets()`; do not put
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
size so alignment and cup hitboxes stay correct. No art-generation scripts run during play. Pillow is used only to cache
nearest-neighbor versions of existing PNGs when the viewport scale changes.

| Folder | Editable files | Size |
| --- | --- | --- |
| `assets/cups` | Plain Cup, 18 rarity skins and three extra frames per skin (`Normal1.png`, `Normal2.png`, `Normal3.png`, for example); `Unknown.png` | 32 x 34, transparent |
| `assets/backgrounds` | Hall, kitchen, terrace, dawn and afterparty | 940 x 410 |
| `assets/backgrounds` | `MenuScene.png` | 940 x 410, dimmed full-room menu |
| `assets/backgrounds` | `CabinetReveal.png` (dimmed hall for gift opening and reveal) | 940 x 410 |
| `assets/backgrounds` | `PartyOver.png` | 936 x 252 |
| `assets/ui` | `Title.png`; `Coin.png` | 440 x 46; 24 x 24, transparent |
| `assets/ui` | `HeartFull.png`, `HeartEmpty.png` | 24 x 18, transparent |
| `assets/ui` | `NavPanel.png`; `SummaryPanel.png` | 408 x 467; 500 x 467, translucent |
| `assets/ui` | `AmbientGlow0.png` through `AmbientGlow2.png` | 48 x 48, transparent |
| `assets/ui` | `CoinHint.png` | 9 x 7, transparent |
| `assets/ui` | `AppIcon.png`; `AppIcon.ico` | Brass Keepsake window and executable icons |
| `assets/ui` | Small button icons and `Dark` variants | 16 x 16, transparent |
| `assets/ui` | Settings, audio, display, done, lock, batch, music and effects icons | 24 x 24, transparent |
| `assets/ui` | `Restart.png`, `Home.png`, `Exit.png` and `Dark` variants | 24 x 24, transparent |
| `assets/ui` | `Ticket.png`, `TicketDark.png` | 20 x 16, transparent; conversion reward scales to 80 x 64 |
| `assets/ui` | `LockBadge.png`; `Unlock0.png` through `Unlock3.png` | 32 x 34; 24 x 28, transparent |

The title is an editable brass-sign PNG. Menu statistics use separate labels
instead of slash-separated strings. Reward popups pair points with a coin
icon and earned tickets with a ticket icon.

The UI uses bundled Pixelify Sans, licensed under the SIL Open Font License
in `assets/fonts/Ofl.txt`. Windows loads it only for this process; the player
does not need to install the font. Dialogue wraps before the action buttons.
Numbers use bold Consolas for clear digit shapes while surrounding words keep
the pixel font. Cup number labels are larger than the small counter text.

`assets/sounds/LanternParty.wav` uses **Cozy Puzzle Stage Select** by MintoDog,
a loopable 100 BPM synth-and-sax puzzle track released under CC0. Source and license details
are in `assets/sounds/MusicCredits.txt`. It is converted to 22,050 Hz stereo,
16-bit PCM WAV and normalized to -22 LUFS. Music starts at 20%, Master at 80% and Game sounds at 70%. Use - and = to adjust by 5%; change
`DEFAULT_MUSIC_VOLUME` in `GameAudio.py` to tune the starting level.
All effects share a soft mallet timbre with gentle attacks and short tails.
Click, reveal, correct, wrong, win, unlock, ticket conversion, equip and pause
each use a separate WAV. Clicks play once per action; a muted game plays no
effects. Ticket conversion sounds only after Next, not while waiting.
`MusicCredits.txt` lists the music license and all effect filenames.
Music and each distinct effect use separate Windows audio channels, so a
button click does not cut off reward or music playback. S stops both channels;
closing the game releases the music device. Tests and QA leave music disabled.
Volume adjustment affects only this game's music channel, never Windows master
volume. The four `assets/ui/Unlock*.png` frames and `LockBadge.png` remain
editable image assets.

Lives use one filled heart per remaining life and empty hearts for lives lost.
Easy shows five heart slots, Normal three, and Hard one. To change audio,
replace `Reveal.wav`, `Correct.wav`, `Wrong.wav`, or `Win.wav` in
`assets/sounds` with short PCM WAV files. Keep the filenames; the game uses
Windows MCI audio channels through Python's standard library; no audio package is needed.

Backgrounds include scenery and the table, without character artwork.
Cups are scaled automatically for the cabinet,
table and draw reveal. Dialogue, scores and button text stay in Python, where
the team can change them directly. `PartyArt.py` names every image it loads;
a missing file reports its full path. Include the whole `assets` folder when
copying or submitting the project.

World artwork uses an original cozy countryside pixel-art direction: timber,
warm lanterns, muted foliage, copper kitchen details and layered forest skies.
Each location has its own palette. Keep the center cup lane visually quiet.
The menu backdrop contains no cup; the collection preview remains a separate image.
Characters appear only in the short story dialogue.

Read `GameConfig.py`, then `WhatTheCup.py`, `InputControls.py`, and
`RoundLogic.py` to follow gameplay. Open the drawing modules when working on
appearance. `self.Session` in a component is the same `Game` object that owns
the score, lives, current phase and sprites; it is not another saved game.

| Phase | What happens | Next phase |
| --- | --- | --- |
| `menu` | Resume a saved run or open New game; choose settings if no save exists | Saved phase, `menu_setup`, `story` or `reveal` |
| `menu_setup` | Choose a new mode and difficulty; Start replaces the checkpoint; Back keeps it | `menu`, `story` or `reveal` |
| `story` | Read one brief line, then press Play | `reveal` |
| `reveal` | Lift the cup holding the coin | `shuffle` |
| `shuffle` | Animate swaps and update numbered positions | `select` |
| `select` | Accept one valid cup choice | `resolving` |
| `resolving` | Lock input and calculate the result | `result`, `retry`, `over`, or `victory` |
| `result`, `retry` | Wait for Next or Retry | Next chapter or the same round |
| `paused` | Resume, Save & Menu, or Save & Exit | Previous phase, menu, or closed |
| `gacha_opening` | Gift opening; Enter skips to reveal | `gacha_reveal` |
| `gacha_reveal` | New cup: Equip or browse. Duplicate: Next starts conversion, then browse | `cabinet` |
| `batch_reveal` | Ten results; Next converts duplicates, then Done | `cabinet` |
| `last_reveal` | Show both opened cups and the coin after the last heart is lost | `over` |

Cup `cid` identifies the same object throughout a round. Cup `slot` changes
after a swap and matches the numbered table position. `CorrectId` indexes
the cup list, so selection compares the chosen object with the original cup.
This distinction is the first thing to check if a shuffle or guess goes wrong.

For a breakpoint, follow a click from `Controls.OnClick()` to
`Rounds.Choose()`, then the appropriate result method and `Views.SetMessage()`.
For collection issues, follow `Controls.CollectionAction()` to the cabinet
and `CupCollection.py`. Draws save before the opening animation begins;
skipping that animation cannot award another draw.

Keep the profile and high-score JSON files, plus `LanternRun.json` if present, when cleaning a player's copy. Missing saves
start fresh; deleting them resets that player's progress. Tests and QA belong
with the source so the team can repeat verification. The only generated files
to discard are `__pycache__`, `.pyc` files and abandoned `.tmp` files after the
game has closed. No downloaded assets or runtime packages are needed.

## Research applied

- https://www.nngroup.com/articles/progressive-disclosure/
- https://www.gamedeveloper.com/design/ux-design-alleviating-burdens-on-playing-gaming-through-better-interface-layout
- https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html
- https://igda-gasig.org/get-involved/sig-initiatives/resources-for-game-developers/sig-guidelines/
- https://gameaccessibilityguidelines.com/full-list/
- https://docs.python.org/3/library/tkinter.html

Secondary information lives in Help, the cabinet and Odds. Gameplay presents
one immediate instruction. Story text is short and player-paced; backgrounds
follow the chapter context. Cosmetic draw transactions do not change gameplay.


## Naming convention

Project-owned filenames, classes, methods, parameters, variables and constants
use PascalCase: `WhatTheCup.py`, `RoundLogic.py`, `LoadScores`, `ScorePath`
and `Self.CorrectId`. Use `python -B -m unittest TestGame` to run the suite;
its `load_tests` hook discovers PascalCase test methods.

Python special names (`__init__`, `__name__`, `__file__`), framework hooks
(`load_tests`, `setUp`, `tearDown`, `setUpClass`, `tearDownClass`) and external
APIs keep their required spelling. The same applies to external keyword arguments,
`pyproject.toml`, `.gitignore`, file extensions and third-party dependencies.
Asset directories remain grouped by purpose. Existing generated builds are unchanged.

Save filenames are `LanternProfile.json`, `LanternRun.json`,
`LanternSettings.json` and `WhatTheCupScores.json`. Older save filenames are
recognized so existing progress carries over. Serialized JSON keys, cup IDs,
canvas tags and input action IDs remain stable; these are data, not variable names.
`NamingCompatibility.py` resolves legacy serialized attribute names and
PascalCase image filenames. Player saves and generated builds remain ignored.
