"""Regression tests. All score writes use a temporary directory."""

from game_objects import input_canvas
from pathlib import Path
import random
import sys
from collections import Counter
import copy
import tempfile
import unittest
from unittest.mock import patch

import what_the_cup as app
import cup_collection as collection
import party_art
import game_objects
from game_config import DIFFICULTIES, STORY_LEVELS, level_settings
from score_store import load_scores, save_score


class StorageTests(unittest.TestCase):
    def test_invalid_saves(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scores.json"
            self.assertEqual(load_scores(path), {})
            for content in ("broken", "[]", '{"x":null,"y":true,"z":-1,"good":42}'):
                path.write_text(content)
                self.assertEqual(
                    load_scores(path), {"good": 42} if "good" in content else {}
                )

    def test_atomic_best_score(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scores.json"
            scores = {}
            self.assertTrue(save_score(path, scores, "story_normal", 120))
            self.assertFalse(save_score(path, scores, "story_normal", 100))
            self.assertEqual(load_scores(path), scores)
            with patch("score_store.os.replace", side_effect=OSError("denied")):
                self.assertFalse(save_score(path, scores, "story_normal", 200))
            self.assertEqual(load_scores(path)["story_normal"], 120)
            self.assertEqual(scores["story_normal"], 120)
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_difficulty_scales(self):
        for difficulty in DIFFICULTIES:
            previous = level_settings(1, difficulty)
            for level in range(2, 100):
                current = level_settings(level, difficulty)
                self.assertTrue(3 <= current[0] <= 6)
                self.assertGreater(current[1], previous[1])
                self.assertLessEqual(current[2], previous[2])
                self.assertLessEqual(current[3], previous[3])
                previous = current


class CollectionTests(unittest.TestCase):
    def test_exact_odds_and_all_boundaries(self):
        counts = Counter(collection.pick_skin(i) for i in range(10000))
        self.assertEqual(
            counts, {skin: weight for skin, _, _, weight, _ in collection.CUPS}
        )
        with self.assertRaises(ValueError):
            collection.pick_skin(10000)

    def test_draw_equip_reload_duplicate_and_insufficient_funds(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "profile.json"
            profile = collection.fresh_profile()
            profile["tickets"] = 30
            rng = random.Random()
            for skin, roll in zip(
                ("normal", "uncommon", "rare", "epic", "legendary", "mythic"),
                (0, 5000, 7700, 9200, 9800, 9980),
            ):
                before = profile["tickets"]
                with patch.object(rng, "randrange", return_value=roll):
                    result, status = collection.draw(path, profile, rng)
                self.assertEqual(result, skin)
                self.assertEqual(
                    profile["tickets"], before - (2 if skin == "normal" else 3)
                )
                self.assertTrue(collection.equip(path, profile, skin))
                self.assertEqual(collection.load_profile(path), profile)
            self.assertEqual(profile["draws"], 6)
            profile["tickets"] = 2
            original = copy.deepcopy(profile)
            self.assertIsNone(collection.draw(path, profile)[0])
            self.assertEqual(profile, original)
            self.assertFalse(collection.equip(path, profile, "unknown"))

    def test_failed_write_rolls_back_and_rewards_once(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "profile.json"
            profile = collection.fresh_profile()
            original = copy.deepcopy(profile)
            with patch("cup_collection.os.replace", side_effect=OSError("denied")):
                self.assertIsNone(collection.draw(path, profile)[0])
                self.assertEqual(collection.reward(path, profile, "Normal:1"), -1)
                self.assertFalse(collection.equip(path, profile, "normal"))
            self.assertEqual(profile, original)
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])
            self.assertEqual(collection.reward(path, profile, "Normal:1"), 1)
            self.assertEqual(collection.reward(path, profile, "Normal:1"), 0)
            self.assertEqual(collection.load_profile(path)["tickets"], 4)

    def test_invalid_profile_is_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "profile.json"
            for text in (
                "broken",
                "[]",
                "null",
                '{"tickets":true,"draws":-3,"owned":[{},"bad","mythic"],"equipped":"bad","rewards":[null,"x"]}',
            ):
                path.write_text(text)
                profile = collection.load_profile(path)
                self.assertEqual(profile["tickets"], 3)
                self.assertEqual(profile["equipped"], "normal")
                self.assertIn("normal", profile["owned"])


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.game = app.Game(
            run_loop=False,
            score_path=Path(cls.folder.name) / "scores.json",
            profile_path=Path(cls.folder.name) / "profile.json",
        )
        cls.game.sound_enabled = False

    @classmethod
    def tearDownClass(cls):
        cls.game.close()
        cls.folder.cleanup()

    def setUp(self):
        random.seed(27)
        self.game.profile = collection.fresh_profile()
        self.game.reward_failed = False
        self.game.mode = "Story"
        self.game.difficulty = "Normal"
        self.game.views.show_menu()

    def enter_round(self):
        while self.game.state == "story":
            self.game.controls.advance()

    def start_gameplay(self):
        self.game.rounds.start_game()
        self.enter_round()

    def finish_shuffle(self):
        self.enter_round()
        g = self.game
        g.rounds.begin_shuffle()
        for _ in range(g.swaps * (g.swap_duration + 1) + 2):
            if g.state == "select":
                break
            g.rounds.animate_swap()
        self.assertEqual(g.state, "select")
        self.assertEqual(sorted(c.slot for c in g.cups), list(range(len(g.cups))))
        for cup in g.cups:
            self.assertEqual(cup.x, g.slots[cup.slot])
            self.assertEqual(cup.y, 0)

    def click_button(self, name):
        x1, y1, x2, y2 = self.game.buttons[name]
        self.game.controls.on_click((x1 + x2) / 2, (y1 + y2) / 2)

    def test_contextual_cup_instructions(self):
        g = self.game
        for level, count in ((1, 3), (4, 4), (7, 5), (10, 6)):
            g.level = level
            g.rounds.start_level()
            self.finish_shuffle()
            text = " ".join(
                g.screen.getcanvas().itemcget(i, "text")
                for i in g.screen.getcanvas().find_all()
                if g.screen.getcanvas().type(i) == "text"
            )
            self.assertIn(f"press 1-{count}", text)
            if count != 6:
                self.assertNotIn("1-6", text)
            score, lives = g.score, g.lives
            g.rounds.choose(count)
            self.assertEqual((g.score, g.lives, g.state), (score, lives, "select"))
            g.controls.toggle_pause()
            g.controls.toggle_pause()
            self.assertEqual(
                g.rounds.selection_hint(), f"Click a cup or press 1-{count}."
            )

    def test_new_screens_text_bounds_and_action_spacing(self):
        g = self.game
        canvas = g.screen.getcanvas()

        def verify():
            g.screen.update()
            for item in canvas.find_all():
                if canvas.type(item) != "text":
                    continue
                label = canvas.itemcget(item, "text")
                left, top, right, bottom = canvas.bbox(item)
                self.assertGreaterEqual(left, -490, label)
                self.assertLessEqual(right, 490, label)
                self.assertGreaterEqual(top, -345, label)
                self.assertLessEqual(bottom, 345, label)
                for key, (x1, y1, x2, y2) in g.buttons.items():
                    if key.startswith("equip:") and g.state == "cabinet":
                        continue  # A card deliberately contains its own text.
                    intersects = left < x2 and right > x1 and top < -y1 and bottom > -y2
                    if intersects:
                        self.assertTrue(
                            x1 <= left and right <= x2 and -y2 <= top and bottom <= -y1,
                            (g.state, key, label, "text overlaps action"),
                        )

        for level in range(1, 11):
            g.level = level
            g.rounds.begin_chapter()
            verify()
            g.controls.advance()
            verify()
        g.cabinet.show_cabinet()
        verify()
        g.cabinet.show_odds()
        verify()
        for skin, roll in zip(
            ("normal", "uncommon", "rare", "epic", "legendary", "mythic"),
            (0, 5000, 7700, 9200, 9800, 9980),
        ):
            g.profile["tickets"] = 3
            g.cabinet.show_cabinet()
            with patch("cup_collection.random.randrange", return_value=roll):
                g.cabinet.draw_cup()
            g.controls.advance()
            verify()
        g.mode = "Endless"
        g.rounds.start_game()
        verify()

    def test_real_mouse_event_selects_number_button(self):
        g = self.game
        self.start_gameplay()
        self.finish_shuffle()
        canvas = input_canvas(g.screen)
        root = canvas.winfo_toplevel()
        cup = g.cups[g.correct_id]
        canvas.event_generate(
            "<Button-1>",
            x=round(cup.x - canvas.canvasx(0)),
            y=round(110 - canvas.canvasy(0)),
        )
        root.update()
        self.assertEqual(g.state, "result")
        self.assertGreater(g.score, 0)

    def test_story_dialogue_and_locations_are_playable(self):
        g = self.game
        settings = []
        for level in range(1, 11):
            g.level = level
            g.rounds.begin_chapter()
            self.assertEqual(g.state, "story")
            self.assertEqual(g.story_page, 0)
            self.assertEqual(g.cups, [])
            settings.append(g.scene_location)
            g.rounds.choose(0)
            self.assertEqual(g.state, "story")
            self.click_button("story_next")
            self.assertEqual((g.state, g.story_page), ("story", 1))
            self.click_button("story_next")
            self.assertEqual(g.state, "reveal")
            self.assertEqual(g.scene_location, settings[-1])
        self.assertEqual(
            settings, ["hall"] * 3 + ["kitchen"] * 3 + ["terrace"] * 3 + ["dawn"]
        )
        g.mode = "Endless"
        g.rounds.start_game()
        self.assertEqual((g.state, g.scene_location), ("reveal", "afterparty"))

    def test_cabinet_draw_animation_equip_and_fair_cups(self):
        g = self.game
        g.profile["tickets"] = 30
        self.click_button("cabinet")
        self.assertEqual(g.state, "cabinet")
        self.click_button("odds")
        self.assertEqual(g.state, "odds")
        g.controls.escape()
        for skin, roll in zip(
            ("normal", "uncommon", "rare", "epic", "legendary", "mythic"),
            (0, 5000, 7700, 9200, 9800, 9980),
        ):
            with patch("cup_collection.random.randrange", return_value=roll):
                self.click_button("draw")
            self.assertEqual(g.state, "gacha_opening")
            tickets = g.profile["tickets"]
            g.cabinet.draw_cup()
            self.assertEqual(g.profile["tickets"], tickets)
            for _ in range(48):
                if g.state == "gacha_opening":
                    g.cabinet.animate_draw()
            self.assertEqual(g.state, "gacha_reveal")
            self.assertEqual(g.pending_cup, skin)
            self.click_button("equip:" + skin)
            self.assertEqual(g.profile["equipped"], skin)
            self.assertEqual(
                collection.load_profile(g.profile_path)["equipped"], skin
            )
            self.start_gameplay()
            self.assertEqual({cup.sprite.shape() for cup in g.cups}, {skin + "_cup"})
            g.cabinet.show_cabinet()
        g.profile["tickets"] = 0
        g.cabinet.show_cabinet()
        self.click_button("draw")
        self.assertEqual(g.state, "cabinet")
        self.assertEqual(g.profile["tickets"], 0)

    def test_perfect_story_all_difficulties(self):
        g = self.game
        for difficulty in DIFFICULTIES:
            g.difficulty = difficulty
            self.start_gameplay()
            expected = 1000
            for level in range(1, STORY_LEVELS + 1):
                self.finish_shuffle()
                expected += level * 100 + (g.lives - 1) * 20
                g.rounds.choose(g.cups[g.correct_id].slot)
                score = g.score
                g.rounds.choose(0)  # Repeated input must not award points twice.
                self.assertEqual(g.score, score)
                if level < STORY_LEVELS:
                    self.assertEqual(g.state, "result")
                    g.controls.advance()
            self.assertEqual(g.state, "victory")
            self.assertEqual(g.score, expected)
            self.assertGreaterEqual(g.best_score(), expected)

    def test_wrong_retry_game_over(self):
        g = self.game
        self.start_gameplay()
        for lives in (2, 1, 0):
            self.finish_shuffle()
            wrong = next(c.slot for c in g.cups if c.cid != g.correct_id)
            g.rounds.choose(wrong)
            self.assertEqual(g.lives, lives)
            self.assertFalse(g.perfect)
            self.assertEqual(g.state, "retry" if lives else "over")
            if lives:
                g.controls.advance()
                self.assertEqual(g.level, 1)
        g.controls.advance()
        self.assertEqual(g.lives, 3)

    def test_endless_combo(self):
        g = self.game
        g.mode = "Endless"
        self.start_gameplay()
        for _ in range(15):
            self.finish_shuffle()
            g.rounds.choose(g.cups[g.correct_id].slot)
            g.controls.advance()
        self.assertEqual(g.combo, 15)
        self.assertEqual(g.level, 16)
        self.finish_shuffle()
        g.rounds.choose(next(c.slot for c in g.cups if c.cid != g.correct_id))
        self.assertEqual(g.combo, 0)

    def test_pause_interrupt_and_hitboxes(self):
        g = self.game
        self.start_gameplay()
        g.rounds.choose(0)
        self.assertEqual(g.state, "reveal")
        g.controls.toggle_pause()
        g.rounds.choose(0)
        self.assertEqual(g.state, "paused")
        g.controls.toggle_pause()
        g.rounds.begin_shuffle()
        g.rounds.animate_swap()
        g.controls.toggle_pause()
        g.controls.toggle_pause()
        self.finish_shuffle()
        cup = g.cups[g.correct_id]
        g.controls.on_click(
            cup.x, -140
        )  # Bare table outside the number button is not a hit.
        self.assertEqual(g.state, "select")
        g.rounds.choose(999)
        self.assertEqual(g.state, "select")
        g.controls.on_click(cup.x, 0)
        self.assertEqual(g.state, "result")
        self.start_gameplay()
        g.rounds.begin_shuffle()
        g.rounds.animate_swap()
        g.views.show_how_to_play()
        g.update()
        self.assertEqual(g.state, "how_to_play")
        g.controls.advance()
        self.assertEqual(g.state, "menu")

    def test_menu_navigation_and_no_sprite_leak(self):
        g = self.game
        g.controls.cycle_mode()
        self.assertEqual(g.mode, "Endless")
        g.controls.cycle_difficulty()
        self.assertEqual(g.difficulty, "Hard")
        count = len(g.screen.turtles())
        sprites = tuple(cup.sprite for cup in g.cup_pool)
        for _ in range(20):
            self.start_gameplay()
            g.views.show_menu()
        self.assertEqual(len(g.screen.turtles()), count)
        for level, expected in ((1, 3), (4, 4), (7, 5), (10, 6)):
            g.level = level
            g.rounds.start_level()
            self.assertEqual(len(g.cups), expected)
            self.assertEqual(tuple(cup.sprite for cup in g.cups), sprites[:expected])
            g.views.show_menu()
            self.assertTrue(all(not sprite.isvisible() for sprite in sprites))
        self.assertEqual(len(g.screen.turtles()), count)

    def test_failed_high_score_save_is_visible(self):
        g = self.game
        self.start_gameplay()
        self.finish_shuffle()
        g.scores = {}
        with patch("round_logic.save_score", return_value=False):
            g.rounds.choose(g.cups[g.correct_id].slot)
        self.assertTrue(g.save_failed)
        canvas = g.screen.getcanvas()
        messages = [
            canvas.itemcget(item, "text")
            for item in canvas.find_all()
            if canvas.type(item) == "text"
        ]
        self.assertIn("Save failed. Check folder permissions.", messages)

    def test_cup_images_are_above_the_background(self):
        g = self.game
        canvas = g.screen.getcanvas()
        for level, count in ((1, 3), (4, 4), (7, 5), (10, 6)):
            g.level = level
            g.rounds.start_level()
            g.screen.update()
            for phase in ("reveal", "shuffle", "select"):
                if phase == "shuffle":
                    g.rounds.begin_shuffle()
                    g.rounds.animate_swap()
                elif phase == "select":
                    self.finish_shuffle()
                g.screen.update()
                stack = list(canvas.find_all())
                image_name = str(g.assets["skins"][g.profile["equipped"]][2])
                cup_items = [
                    item
                    for item in stack
                    if canvas.type(item) == "image"
                    and canvas.itemcget(item, "image") == image_name
                ]
                self.assertEqual(len(cup_items), count)
                background_top = max(
                    stack.index(i) for i in canvas.find_withtag("scene")
                )
                self.assertTrue(all(stack.index(i) > background_top for i in cup_items))

    def test_png_assets_and_missing_file_message(self):
        g = self.game
        for images in g.assets["skins"].values():
            self.assertEqual((images[0].width(), images[0].height()), (32, 34))
        for name, image in g.assets["backgrounds"].items():
            size = (435, 410) if name == "menu" else (940, 410)
            self.assertEqual((image.width(), image.height()), size)
        for image in g.assets["portraits"].values():
            self.assertEqual((image.width(), image.height()), (96, 150))
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(party_art, "ASSET_FOLDER", Path(folder)):
                with self.assertRaisesRegex(FileNotFoundError, "normal.png"):
                    party_art.load_assets(g.screen)

    def test_heart_hud_matches_remaining_lives(self):
        g = self.game
        canvas = g.screen.getcanvas()
        for difficulty, settings in DIFFICULTIES.items():
            g.difficulty = difficulty
            for lives in range(settings["lives"] + 1):
                g.lives = lives
                g.views.draw_hud()
                images = [
                    canvas.itemcget(item, "image")
                    for item in canvas.find_withtag("hud_art")
                    if canvas.type(item) == "image"
                ]
                self.assertEqual(images.count(str(g.assets["heart_full"])), lives)
                self.assertEqual(
                    images.count(str(g.assets["heart_empty"])),
                    settings["lives"] - lives,
                )

    def test_footer_links_are_clickable_in_each_phase(self):
        g = self.game

        def click(action):
            x1, y1, x2, y2 = g.footer_actions[action]
            g.controls.on_click((x1 + x2) / 2, (y1 + y2) / 2)

        click("help")
        self.assertEqual(g.state, "how_to_play")
        click("escape")
        self.assertEqual(g.state, "menu")
        with patch.object(g, "close") as close:
            click("escape")
            close.assert_called_once()
        click("advance")
        self.assertEqual(g.state, "story")
        click("advance")
        self.assertEqual(g.story_page, 1)
        click("advance")
        self.assertEqual(g.state, "reveal")
        click("pause")
        self.assertEqual(g.state, "paused")
        previous = g.sound_enabled
        click("sound")
        self.assertNotEqual(g.sound_enabled, previous)
        click("pause")
        self.assertEqual(g.state, "reveal")
        self.finish_shuffle()
        click("menu")
        self.assertEqual(g.state, "menu")
        g.controls.open_cabinet_from_menu()
        click("escape")
        self.assertEqual(g.state, "menu")

    def test_endless_hint_is_gated_tracks_cup_and_expires(self):
        g = self.game
        canvas = g.screen.getcanvas()
        for mode, level, visible in (("Story", 10, False), ("Endless", 10, False),
                                     ("Endless", 11, True), ("Endless", 25, True)):
            g.mode, g.level = mode, level
            g.rounds.start_level()
            self.finish_shuffle()
            items = canvas.find_withtag("spark_hint")
            self.assertEqual(bool(items), visible)
            if visible:
                cup = g.cups[g.correct_id]
                self.assertEqual(canvas.coords(items[0]), [cup.x - 4, 58])
                g.controls.toggle_pause()
                remaining = g.hint_frames
                g.update()
                self.assertEqual(g.hint_frames, remaining)
                g.controls.toggle_pause()
                g.hint_frames = 1
                g.last_tick = 100
                g.frame_credit = 0
                with patch("what_the_cup.time.monotonic", return_value=100.05):
                    g.update()
                self.assertFalse(canvas.find_withtag("spark_hint"))
                g.views.show_spark_hint()
                g.rounds.choose(cup.slot)
                self.assertFalse(canvas.find_withtag("spark_hint"))
        g.views.show_menu()
        self.assertFalse(canvas.find_withtag("spark_hint"))

    @unittest.skipUnless(sys.platform == "win32", "Windows WAV playback backend")
    def test_custom_sound_playback_never_uses_system_alerts(self):
        import winsound

        with patch.object(winsound, "PlaySound") as playback:
            with patch.object(winsound, "MessageBeep") as system_alert:
                for kind in ("reveal", "correct", "wrong", "win"):
                    game_objects.tone(kind)
                    path, flags = playback.call_args.args
                    self.assertTrue(Path(path).is_file())
                    self.assertTrue(flags & winsound.SND_ASYNC)
                    self.assertTrue(flags & winsound.SND_NODEFAULT)
                self.assertEqual(playback.call_count, 4)
                system_alert.assert_not_called()

    def test_live_tk_errors_are_not_silenced(self):
        g = self.game
        with patch.object(g.screen, "update", side_effect=app.tkinter.TclError("bug")):
            with self.assertRaises(app.tkinter.TclError):
                g.update()
        self.assertTrue(g.running)

    def test_imperfect_ending_and_menu_clicks(self):
        g = self.game
        box = g.buttons["mode:Endless"]
        g.controls.on_click((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        self.assertEqual(g.mode, "Endless")
        g.mode = "Story"
        self.start_gameplay()
        g.perfect = False
        g.level = 10
        g.rounds.start_level()
        self.finish_shuffle()
        g.rounds.choose(g.cups[g.correct_id].slot)
        self.assertEqual(g.state, "victory")
        self.assertEqual(g.score, 1040)
        g.controls.on_click(0, 0)
        self.assertEqual(g.state, "victory")
        g.controls.escape()
        self.assertEqual(g.state, "menu")

    def test_elapsed_time_reveal_and_pause(self):
        g = self.game
        self.start_gameplay()
        g.reveal_frame = g.reveal_frames - 1
        g.last_tick = 100.0
        with patch("what_the_cup.time.monotonic", return_value=100.05):
            g.update()
        self.assertEqual(g.state, "shuffle")
        g.controls.toggle_pause()
        frames = g.swap_frame
        g.last_tick = 100.0
        with patch("what_the_cup.time.monotonic", return_value=101.0):
            g.update()
        self.assertEqual(g.swap_frame, frames)
        self.assertEqual(g.state, "paused")

    def test_text_stays_inside_window_and_layers_do_not_leak(self):
        g = self.game
        canvas = g.screen.getcanvas()

        def verify_text():
            g.screen.update()
            for item in canvas.find_all():
                if canvas.type(item) == "text":
                    text = canvas.itemcget(item, "text")
                    self.assertNotIn("\u00e2", text)
                    bounds = canvas.bbox(item)
                    self.assertGreaterEqual(bounds[0], -490, text)
                    self.assertLessEqual(bounds[2], 490, text)
                    self.assertGreaterEqual(bounds[1], -345, text)
                    self.assertLessEqual(bounds[3], 345, text)

        for mode in ("Story", "Endless"):
            g.mode = mode
            for difficulty in DIFFICULTIES:
                g.difficulty = difficulty
                g.views.show_menu()
                verify_text()
        g.views.show_how_to_play()
        verify_text()
        g.mode = "Story"
        self.start_gameplay()
        initial = len(canvas.find_all())
        for _ in range(20):
            g.views.draw_hud()
        self.assertEqual(len(canvas.find_all()), initial)
        for level in (1, 4, 7, 10):
            g.level = level
            g.rounds.start_level()
            verify_text()
            self.finish_shuffle()
            g.rounds.choose(g.cups[g.correct_id].slot)
            verify_text()

    def test_every_game_entry_draws_gameplay_instead_of_menu(self):
        g = self.game
        canvas = g.screen.getcanvas()
        for mode in ("Story", "Endless"):
            for difficulty in DIFFICULTIES:
                for entry in ("click", "enter", "restart", "help"):
                    g.mode = mode
                    g.difficulty = difficulty
                    g.views.show_menu()
                    if entry == "click":
                        x1, y1, x2, y2 = g.buttons["start"]
                        g.controls.on_click((x1 + x2) / 2, (y1 + y2) / 2)
                    elif entry == "enter":
                        g.controls.advance()
                    elif entry == "restart":
                        g.controls.restart()
                    else:
                        g.views.show_how_to_play()
                        g.controls.restart()
                    g.screen.update()
                    self.enter_round()
                    self.assertEqual(g.state, "reveal")
                    scene = [
                        canvas.coords(item)
                        for item in canvas.find_withtag("scene")
                        if canvas.type(item) == "rectangle"
                    ]
                    self.assertIn(
                        [-470.0, -236.0, 470.0, 174.0], scene, (mode, difficulty, entry)
                    )
                    self.assertIn(
                        [-470.0, 184.0, 470.0, 292.0], scene, (mode, difficulty, entry)
                    )
                    images = [
                        canvas.itemcget(item, "image")
                        for item in canvas.find_all()
                        if canvas.type(item) == "image"
                    ]
                    backgrounds = g.assets["backgrounds"]
                    expected = "hall" if mode == "Story" else "afterparty"
                    self.assertIn(str(backgrounds[expected]), images)
                    self.assertNotIn(str(backgrounds["menu"]), images)


if __name__ == "__main__":
    unittest.main()
