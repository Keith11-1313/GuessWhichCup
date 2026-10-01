"""Regression tests. All score writes use a temporary directory."""
from pathlib import Path
import random
from collections import Counter
import copy
import tempfile
import unittest
from unittest.mock import patch

import what_the_cup as app
import cup_collection as collection
from game_config import DIFFICULTIES, STORY_LEVELS, level_settings
from score_store import load_scores, save_score


class StorageTests(unittest.TestCase):
    def test_invalid_saves(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'scores.json'
            self.assertEqual(load_scores(path), {})
            for content in ('broken', '[]', '{"x":null,"y":true,"z":-1,"good":42}'):
                path.write_text(content)
                self.assertEqual(load_scores(path), {'good':42} if 'good' in content else {})

    def test_atomic_best_score(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'scores.json'
            scores = {}
            self.assertTrue(save_score(path,scores,'story_normal',120))
            self.assertFalse(save_score(path,scores,'story_normal',100))
            self.assertEqual(load_scores(path), scores)
            with patch('score_store.os.replace', side_effect=OSError('denied')):
                self.assertFalse(save_score(path,scores,'story_normal',200))
            self.assertEqual(load_scores(path)['story_normal'],120)
            self.assertEqual(scores['story_normal'],120)
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])

    def test_difficulty_scales(self):
        for difficulty in DIFFICULTIES:
            previous = level_settings(1,difficulty)
            for level in range(2,100):
                current = level_settings(level,difficulty)
                self.assertTrue(3 <= current[0] <= 6)
                self.assertGreater(current[1],previous[1])
                self.assertLessEqual(current[2],previous[2])
                self.assertLessEqual(current[3],previous[3])
                previous = current


class CollectionTests(unittest.TestCase):
    def test_exact_odds_and_all_boundaries(self):
        counts=Counter(collection.pick_skin(i) for i in range(10000))
        self.assertEqual(counts,{skin:weight for skin,_,_,weight,_ in collection.CUPS})
        with self.assertRaises(ValueError):
            collection.pick_skin(10000)

    def test_draw_equip_reload_duplicate_and_insufficient_funds(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'profile.json'
            profile=collection.fresh_profile()
            profile['tickets']=30
            rng=random.Random()
            for skin,roll in zip(('normal','uncommon','rare','epic','legendary','mythic'),(0,5000,7700,9200,9800,9980)):
                before=profile['tickets']
                with patch.object(rng,'randrange',return_value=roll):
                    result,status=collection.draw(path,profile,rng)
                self.assertEqual(result,skin)
                self.assertEqual(profile['tickets'],before-(2 if skin=='normal' else 3))
                self.assertTrue(collection.equip(path,profile,skin))
                self.assertEqual(collection.load_profile(path),profile)
            self.assertEqual(profile['draws'],6)
            profile['tickets']=2
            original=copy.deepcopy(profile)
            self.assertIsNone(collection.draw(path,profile)[0])
            self.assertEqual(profile,original)
            self.assertFalse(collection.equip(path,profile,'unknown'))

    def test_failed_write_rolls_back_and_rewards_once(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'profile.json'
            profile=collection.fresh_profile()
            original=copy.deepcopy(profile)
            with patch('cup_collection.os.replace',side_effect=OSError('denied')):
                self.assertIsNone(collection.draw(path,profile)[0])
                self.assertEqual(collection.reward(path,profile,'Normal:1'),-1)
                self.assertFalse(collection.equip(path,profile,'normal'))
            self.assertEqual(profile,original)
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])
            self.assertEqual(collection.reward(path,profile,'Normal:1'),1)
            self.assertEqual(collection.reward(path,profile,'Normal:1'),0)
            self.assertEqual(collection.load_profile(path)['tickets'],4)

    def test_invalid_profile_is_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'profile.json'
            for text in ('broken','[]','null','{"tickets":true,"draws":-3,"owned":[{},"bad","mythic"],"equipped":"bad","rewards":[null,"x"]}'):
                path.write_text(text)
                profile=collection.load_profile(path)
                self.assertEqual(profile['tickets'],3)
                self.assertEqual(profile['equipped'],'normal')
                self.assertIn('normal',profile['owned'])


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.saved_path = app.SAVE_FILE
        cls.profile_path = collection.PROFILE_FILE
        collection.PROFILE_FILE = Path(cls.folder.name)/'profile.json'
        app.SAVE_FILE = Path(cls.folder.name)/'scores.json'
        cls.game = app.Game(run_loop=False)
        cls.game.sound_enabled = False

    @classmethod
    def tearDownClass(cls):
        cls.game.close()
        app.SAVE_FILE = cls.saved_path
        collection.PROFILE_FILE = cls.profile_path
        cls.folder.cleanup()

    def setUp(self):
        random.seed(27)
        self.game.profile=collection.fresh_profile()
        self.game.reward_failed=False
        self.game.mode = 'Story'
        self.game.difficulty = 'Normal'
        self.game.show_menu()

    def enter_round(self):
        while self.game.state=='story':
            self.game.advance()

    def start_gameplay(self):
        self.game.start_game()
        self.enter_round()

    def finish_shuffle(self):
        self.enter_round()
        g = self.game
        g.begin_shuffle()
        for _ in range(g.swaps*(g.swap_duration+1)+2):
            if g.state == 'select':
                break
            g.animate_swap()
        self.assertEqual(g.state,'select')
        self.assertEqual(sorted(c.slot for c in g.cups),list(range(len(g.cups))))
        for cup in g.cups:
            self.assertEqual(cup.x,g.slots[cup.slot])
            self.assertEqual(cup.y,0)

    def click_button(self,name):
        x1,y1,x2,y2=self.game.buttons[name]
        self.game.on_click((x1+x2)/2,(y1+y2)/2)

    def test_contextual_cup_instructions(self):
        g=self.game
        for level,count in ((1,3),(4,4),(7,5),(10,6)):
            g.level=level; g.start_level(); self.finish_shuffle()
            text=' '.join(g.screen.getcanvas().itemcget(i,'text') for i in g.screen.getcanvas().find_all()
                          if g.screen.getcanvas().type(i)=='text')
            self.assertIn(f'press 1-{count}',text)
            if count!=6:
                self.assertNotIn('1-6',text)
            score,lives=g.score,g.lives
            g.choose(count)
            self.assertEqual((g.score,g.lives,g.state),(score,lives,'select'))
            g.toggle_pause(); g.toggle_pause()
            self.assertEqual(g.selection_hint(),f'Click a cup or press 1-{count}.')

    def test_new_screens_text_bounds_and_action_spacing(self):
        g=self.game
        canvas=g.screen.getcanvas()
        def verify():
            g.screen.update()
            for item in canvas.find_all():
                if canvas.type(item)!='text':
                    continue
                label=canvas.itemcget(item,'text')
                left,top,right,bottom=canvas.bbox(item)
                self.assertGreaterEqual(left,-490,label)
                self.assertLessEqual(right,490,label)
                self.assertGreaterEqual(top,-345,label)
                self.assertLessEqual(bottom,345,label)
                for key,(x1,y1,x2,y2) in g.buttons.items():
                    if key.startswith('equip:') and g.state=='cabinet':
                        continue  # A card deliberately contains its own text.
                    intersects=left<x2 and right>x1 and top<-y1 and bottom>-y2
                    if intersects:
                        self.assertTrue(x1<=left and right<=x2 and -y2<=top and bottom<=-y1,
                                        (g.state,key,label,'text overlaps action'))
        for level in range(1,11):
            g.level=level; g.begin_chapter(); verify()
            g.advance(); verify()
        g.show_cabinet(); verify()
        g.show_odds(); verify()
        for skin,roll in zip(('normal','uncommon','rare','epic','legendary','mythic'),(0,5000,7700,9200,9800,9980)):
            g.profile['tickets']=3
            g.show_cabinet()
            with patch('cup_collection.random.randrange',return_value=roll):
                g.draw_cup()
            g.advance(); verify()
        g.mode='Endless'; g.start_game(); verify()

    def test_real_mouse_event_selects_number_button(self):
        g=self.game
        self.start_gameplay(); self.finish_shuffle()
        canvas=g.screen.getcanvas()._canvas
        root=canvas.winfo_toplevel()
        cup=g.cups[g.correct_id]
        canvas.event_generate('<Button-1>',x=round(cup.x-canvas.canvasx(0)),
                              y=round(110-canvas.canvasy(0)))
        root.update()
        self.assertEqual(g.state,'result')
        self.assertGreater(g.score,0)

    def test_story_dialogue_and_locations_are_playable(self):
        g=self.game
        settings=[]
        for level in range(1,11):
            g.level=level; g.begin_chapter()
            self.assertEqual(g.state,'story')
            self.assertEqual(g.story_page,0)
            self.assertEqual(g.cups,[])
            settings.append(g.scene_location)
            g.choose(0)
            self.assertEqual(g.state,'story')
            self.click_button('story_next')
            self.assertEqual((g.state,g.story_page),('story',1))
            self.click_button('story_next')
            self.assertEqual(g.state,'reveal')
            self.assertEqual(g.scene_location,settings[-1])
        self.assertEqual(settings,['hall']*3+['kitchen']*3+['terrace']*3+['dawn'])
        g.mode='Endless'; g.start_game()
        self.assertEqual((g.state,g.scene_location),('reveal','afterparty'))

    def test_cabinet_draw_animation_equip_and_fair_cups(self):
        g=self.game
        g.profile['tickets']=30
        self.click_button('cabinet')
        self.assertEqual(g.state,'cabinet')
        self.click_button('odds')
        self.assertEqual(g.state,'odds')
        g.escape()
        for skin,roll in zip(('normal','uncommon','rare','epic','legendary','mythic'),(0,5000,7700,9200,9800,9980)):
            with patch('cup_collection.random.randrange',return_value=roll):
                self.click_button('draw')
            self.assertEqual(g.state,'gacha_opening')
            tickets=g.profile['tickets']
            g.draw_cup()
            self.assertEqual(g.profile['tickets'],tickets)
            for _ in range(48):
                if g.state=='gacha_opening':
                    g.animate_draw()
            self.assertEqual(g.state,'gacha_reveal')
            self.assertEqual(g.pending_cup,skin)
            self.click_button('equip:'+skin)
            self.assertEqual(g.profile['equipped'],skin)
            self.assertEqual(collection.load_profile(collection.PROFILE_FILE)['equipped'],skin)
            self.start_gameplay()
            self.assertEqual({cup.sprite.shape() for cup in g.cups},{skin+'_cup'})
            g.show_cabinet()
        g.profile['tickets']=0
        g.show_cabinet(); self.click_button('draw')
        self.assertEqual(g.state,'cabinet')
        self.assertEqual(g.profile['tickets'],0)

    def test_perfect_story_all_difficulties(self):
        g = self.game
        for difficulty in DIFFICULTIES:
            g.difficulty = difficulty
            self.start_gameplay()
            expected = 1000
            for level in range(1,STORY_LEVELS+1):
                self.finish_shuffle()
                expected += level*100+(g.lives-1)*20
                g.choose(g.cups[g.correct_id].slot)
                score = g.score
                g.choose(0)  # Repeated input must not award points twice.
                self.assertEqual(g.score,score)
                if level < STORY_LEVELS:
                    self.assertEqual(g.state,'result')
                    g.advance()
            self.assertEqual(g.state,'victory')
            self.assertEqual(g.score,expected)
            self.assertGreaterEqual(g.best_score(),expected)

    def test_wrong_retry_game_over(self):
        g = self.game
        self.start_gameplay()
        for lives in (2,1,0):
            self.finish_shuffle()
            wrong = next(c.slot for c in g.cups if c.cid != g.correct_id)
            g.choose(wrong)
            self.assertEqual(g.lives,lives)
            self.assertFalse(g.perfect)
            self.assertEqual(g.state,'retry' if lives else 'over')
            if lives:
                g.advance()
                self.assertEqual(g.level,1)
        g.advance()
        self.assertEqual(g.lives,3)

    def test_endless_combo(self):
        g = self.game
        g.mode = 'Endless'
        self.start_gameplay()
        for _ in range(15):
            self.finish_shuffle()
            g.choose(g.cups[g.correct_id].slot)
            g.advance()
        self.assertEqual(g.combo,15)
        self.assertEqual(g.level,16)
        self.finish_shuffle()
        g.choose(next(c.slot for c in g.cups if c.cid != g.correct_id))
        self.assertEqual(g.combo,0)

    def test_pause_interrupt_and_hitboxes(self):
        g = self.game
        self.start_gameplay()
        g.choose(0)
        self.assertEqual(g.state,'reveal')
        g.toggle_pause()
        g.choose(0)
        self.assertEqual(g.state,'paused')
        g.toggle_pause()
        g.begin_shuffle()
        g.animate_swap()
        g.toggle_pause()
        g.toggle_pause()
        self.finish_shuffle()
        cup = g.cups[g.correct_id]
        g.on_click(cup.x,-140)  # Bare table outside the number button is not a hit.
        self.assertEqual(g.state,'select')
        g.choose(999)
        self.assertEqual(g.state,'select')
        g.on_click(cup.x,0)
        self.assertEqual(g.state,'result')
        self.start_gameplay()
        g.begin_shuffle()
        g.animate_swap()
        g.show_how_to_play()
        g.update()
        self.assertEqual(g.state,'how_to_play')
        g.advance()
        self.assertEqual(g.state,'menu')

    def test_menu_navigation_and_no_sprite_leak(self):
        g = self.game
        g.cycle_mode()
        self.assertEqual(g.mode,'Endless')
        g.cycle_difficulty()
        self.assertEqual(g.difficulty,'Hard')
        count = len(g.screen.turtles())
        for _ in range(20):
            self.start_gameplay()
            g.show_menu()
        self.assertEqual(len(g.screen.turtles()),count)

    def test_imperfect_ending_and_menu_clicks(self):
        g = self.game
        box = g.buttons['mode:Endless']
        g.on_click((box[0]+box[2])/2, (box[1]+box[3])/2)
        self.assertEqual(g.mode,'Endless')
        g.mode = 'Story'
        self.start_gameplay()
        g.perfect = False
        g.level = 10
        g.start_level()
        self.finish_shuffle()
        g.choose(g.cups[g.correct_id].slot)
        self.assertEqual(g.state,'victory')
        self.assertEqual(g.score,1040)
        g.on_click(0,0)
        self.assertEqual(g.state,'victory')
        g.escape()
        self.assertEqual(g.state,'menu')

    def test_elapsed_time_reveal_and_pause(self):
        g = self.game
        self.start_gameplay()
        g.reveal_frame = g.reveal_frames-1
        g.last_tick = 100.0
        with patch('what_the_cup.time.monotonic',return_value=100.05):
            g.update()
        self.assertEqual(g.state,'shuffle')
        g.toggle_pause()
        frames = g.swap_frame
        g.last_tick = 100.0
        with patch('what_the_cup.time.monotonic',return_value=101.0):
            g.update()
        self.assertEqual(g.swap_frame,frames)
        self.assertEqual(g.state,'paused')

    def test_text_stays_inside_window_and_layers_do_not_leak(self):
        g = self.game
        canvas = g.screen.getcanvas()
        def verify_text():
            g.screen.update()
            for item in canvas.find_all():
                if canvas.type(item) == 'text':
                    text = canvas.itemcget(item,'text')
                    self.assertNotIn('\u00e2',text)
                    bounds = canvas.bbox(item)
                    self.assertGreaterEqual(bounds[0],-490,text)
                    self.assertLessEqual(bounds[2],490,text)
                    self.assertGreaterEqual(bounds[1],-345,text)
                    self.assertLessEqual(bounds[3],345,text)
        for mode in ('Story','Endless'):
            g.mode=mode
            for difficulty in DIFFICULTIES:
                g.difficulty=difficulty
                g.show_menu()
                verify_text()
        g.show_how_to_play()
        verify_text()
        g.mode='Story'; self.start_gameplay()
        initial = len(canvas.find_all())
        for _ in range(20):
            g.draw_hud()
        self.assertEqual(len(canvas.find_all()),initial)
        for level in (1,4,7,10):
            g.level=level; g.start_level()
            verify_text()
            self.finish_shuffle()
            g.choose(g.cups[g.correct_id].slot)
            verify_text()

    def test_every_game_entry_draws_gameplay_instead_of_menu(self):
        g = self.game
        canvas = g.screen.getcanvas()
        for mode in ('Story','Endless'):
            for difficulty in DIFFICULTIES:
                for entry in ('click','enter','restart','help'):
                    g.mode=mode; g.difficulty=difficulty; g.show_menu()
                    if entry == 'click':
                        x1,y1,x2,y2=g.buttons['start']
                        g.on_click((x1+x2)/2,(y1+y2)/2)
                    elif entry == 'enter':
                        g.advance()
                    elif entry == 'restart':
                        g.restart()
                    else:
                        g.show_how_to_play(); g.restart()
                    g.screen.update()
                    self.enter_round()
                    self.assertEqual(g.state,'reveal')
                    scene=[canvas.coords(item) for item in canvas.find_withtag('scene')
                           if canvas.type(item)=='rectangle']
                    self.assertIn([-470.0,-236.0,470.0,174.0],scene,(mode,difficulty,entry))
                    self.assertIn([-470.0,184.0,470.0,292.0],scene,(mode,difficulty,entry))
                    images=[canvas.itemcget(item,'image') for item in canvas.find_all()
                            if canvas.type(item)=='image']
                    self.assertNotIn(str(g.screen._party_images[2]),images)


if __name__ == '__main__':
    unittest.main()
