import math
import random
import sys
import turtle
import tkinter
import time
from party_art import register_cup, scenery, frame, pixel_title, guest
from party_story import CHAPTERS, SCENES, LOCATION_NAMES, location
import cup_collection as collection
from collection_screens import CupCabinet
from game_config import (COLORS, DIFFICULTIES, FRAME_MS, HEIGHT, SAVE_FILE, STORY_LEVELS, WIDTH, level_settings)
from score_store import load_scores, save_score

BG = COLORS['background']
WHITE = COLORS['white']
MUTED = COLORS['muted']
GOLD = COLORS['gold']


def make_writer(color=WHITE):
    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.penup()
    t.color(color)
    return t


def tone(kind, screen):
    if sys.platform == 'win32':
        try:
            import winsound
            winsound.MessageBeep(
                winsound.MB_OK if kind in ('correct', 'win')
                else winsound.MB_ICONEXCLAMATION
            )
            return
        except (ImportError, RuntimeError, OSError):
            pass

    try:
        screen.getcanvas().bell()
    except Exception:
        pass


class Cup:
    def __init__(self, cid, x, skin='normal'):
        self.cid = cid
        self.slot = cid
        self.x = x
        self.y = 0
        self.sprite = turtle.Turtle(visible=False)
        self.sprite.speed(0)
        self.sprite.penup()
        shape_name = skin + '_cup'
        self.sprite.shape(shape_name)
        self.sprite.setheading(90)
        self.sprite.goto(x, 0)
        self.sprite.showturtle()

    def render(self):
        self.sprite.goto(self.x, self.y)

    def hide(self):
        self.sprite.hideturtle()
        self.sprite.clear()
        try:
            if self.sprite in self.sprite.screen._turtles:
                self.sprite.screen._turtles.remove(self.sprite)
        except Exception:
            pass


class Game(CupCabinet):
    def __init__(self, run_loop=True):
        self.screen = turtle.Screen()
        self.screen.setup(WIDTH, HEIGHT)
        self.screen.title('Guess Which Cup | Lantern House | by @RENE')
        self.screen.bgcolor(BG)
        self.screen.tracer(0)
        register_cup(self.screen)
        self.running = True
        self.sound_enabled = True
        self.paused_state = None
        self.last_tick = time.monotonic()
        self.frame_credit = 0.0
        root = self.screen.getcanvas().winfo_toplevel()
        root.resizable(False, False)
        root.protocol('WM_DELETE_WINDOW', self.close)

        self.static = make_writer()
        self.footer = make_writer()
        self.menu_text = make_writer()
        self.hud_text = make_writer()
        self.message = make_writer()
        self.labels = make_writer(MUTED)

        self.ball = turtle.Turtle(visible=False)
        self.ball.speed(0)
        self.ball.penup()
        self.ball.shape('spark')
        self.ball.setheading(90)
        self.ball.color(GOLD)

        self.scores = load_scores(SAVE_FILE)
        self.profile = collection.load_profile(collection.PROFILE_FILE)
        self.story_page = 0
        self.reward_failed = False
        self.pending_cup = None
        self.mode = 'Story'
        self.difficulty = 'Normal'
        self.level = 1
        self.score = 0
        self.lives = 3

        # Endless combo and Story perfect tracking
        self.combo = 0
        self.perfect = True

        self.state = 'menu'
        self.cups = []
        self.slots = []
        self.correct_id = 0
        self.reveal_frame = 0
        self.reveal_frames = 0
        self.swaps = 0
        self.swap_duration = 30
        self.completed_swaps = 0
        self.swap_pair = None
        self.swap_frame = 0
        self.buttons = {}

        self.screen.onclick(self.on_click)
        self.screen.listen()

        for key in ('Return', 'space'):
            self.screen.onkeypress(self.advance, key)

        for key in ('m', 'M'):
            self.screen.onkeypress(self.show_menu, key)

        for key in ('h', 'H'):
            self.screen.onkeypress(self.show_how_to_play, key)

        for key in ('r', 'R'):
            self.screen.onkeypress(self.restart, key)

        for n in range(1, 7):
            self.screen.onkeypress(
                lambda number=n: self.choose(number - 1), str(n)
            )

        self.screen.onkeypress(self.escape, 'Escape')
        self.screen.onkeypress(self.toggle_pause, 'p')
        self.screen.onkeypress(self.toggle_sound, 's')
        self.screen.onkeypress(self.toggle_pause, 'P')
        self.screen.onkeypress(self.toggle_sound, 'S')
        for key in ('c','C'):
            self.screen.onkeypress(lambda: self.show_cabinet() if self.state=='menu' else None,key)
        self.screen.onkeypress(self.cycle_mode, 'Tab')
        self.screen.onkeypress(lambda: self.cycle_difficulty(-1), 'Left')
        self.screen.onkeypress(self.cycle_difficulty, 'Right')
        self.show_menu()
        self.screen.ontimer(self.update, FRAME_MS)
        if run_loop:
            self.screen.mainloop()

    def write(self, pen, x, y, text, size=16, color=WHITE, align='center'):
        pen.color(color)
        pen.goto(x, y)
        pen.write(text, align=align, font=('Segoe UI', size, 'bold' if size >= 16 else 'normal'))

    def rectangle(self, x1, y1, x2, y2, fill, outline=None):
        self.screen.getcanvas().create_rectangle(x1,-y2,x2,-y1,
            fill=fill, outline=outline or fill, width=0 if outline is None else 1,
            tags=(getattr(self, 'art_layer', 'scene'),))

    def draw_background(self, view='game'):
        self.static.clear()
        canvas = self.screen.getcanvas()
        for layer in ('scene','hud_art','choice_art','message_art','draw_fx'):
            canvas.delete(layer)
        self.art_layer = 'scene'
        scenery(self, menu=view == 'menu')
        pixel_title(self, 'GUESS WHICH CUP', -466, 306, 4)
        self.write(self.static, 467, 288, 'Lantern House', 16, GOLD, 'right')
        self.write(self.static, 467, 266, 'A night to remember', 10, MUTED, 'right')
        self.rectangle(-470,255,470,257,'#765465')
        if view != 'menu':
            frame(self,-470,-292,470,-184,'#241d30')
        self.draw_footer()

    def draw_button(self, name, text, x, y, width, active=False):
        fill = GOLD if active else '#342a41'
        frame(self,x-width/2,y-22,x+width/2,y+22,fill,
              '#ffe0a0' if active else '#715166')
        self.write(self.menu_text,x,y-8,text,12,'#2b2030' if active else WHITE)
        self.buttons[name]=(x-width/2,y-22,x+width/2,y+22)

    def clear_cups(self):
        for cup in self.cups:
            cup.hide()

        self.cups = []
        self.ball.hideturtle()
        self.labels.clear()

    # HOW TO PLAY

    def show_how_to_play(self):
        self.state='how_to_play'
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear(); self.hud_text.clear(); self.message.clear()
        self.buttons={}
        frame(self,-365,-156,365,224,'#241d30')
        self.write(self.menu_text,-330,177,'A little party trick',24,GOLD,'left')
        self.write(self.menu_text,-330,140,'Three moments. One spark to keep safe.',12,MUTED,'left')
        for y,title,detail in ((80,'Remember','Look for the spark underneath the lifted cup.'),
                               (8,'Follow','Track that cup as the table shuffles.'),
                               (-64,'Choose','Click its cup or press the matching number.')):
            self.rectangle(-330,y-16,-326,y+20,GOLD)
            self.write(self.menu_text,-306,y,title,16,WHITE,'left')
            self.write(self.menu_text,-306,y-26,detail,12,MUTED,'left')
        self.write(self.menu_text,-330,-132,'A correct pick earns points. A mistake costs one life.',11,MUTED,'left')
        self.set_message('Take your time','P pauses the round. Sound is optional. Results wait for you.')
        self.draw_button('back','Back to the party',312,-268,242,True)
        self.screen.update()

    def show_menu(self):
        self.state = 'menu'
        self.clear_cups()
        self.draw_background(view='menu')
        self.menu_text.clear()
        self.hud_text.clear()
        self.message.clear()
        self.buttons = {}
        frame(self,-8,-175,470,236,'#241d30')
        self.write(self.menu_text,24,198,'Your invitation',22,GOLD,'left')
        self.write(self.menu_text,24,167,'A hidden spark. A table full of friends.',12,WHITE,'left')

        self.rectangle(24,125,435,126,'#533f53')
        self.write(self.menu_text,24,99,'Choose your evening',12,MUTED,'left')
        self.draw_button('mode:Story','Story',125,65,190,self.mode=='Story')
        self.draw_button('mode:Endless','Endless',335,65,190,self.mode=='Endless')
        mode_detail = 'Ten chapters with Mira, Theo & Jun.' if self.mode=='Story' else 'The afterparty. Keep your streak alive.'
        self.write(self.menu_text,24,23,mode_detail,11,MUTED,'left')
        self.write(self.menu_text,24,-13,'Set the pace',12,MUTED,'left')
        for x,name in ((91,'Easy'),(231,'Normal'),(371,'Hard')):
            self.draw_button('diff:'+name,name,x,-49,122,self.difficulty==name)
        lives = DIFFICULTIES[self.difficulty]['lives']
        self.write(self.menu_text,24,-94,f'{lives} lives  /  Best score  {self.best_score():,}',11,MUTED,'left')
        self.draw_button('start','Join the party',152,-137,244,True)
        self.draw_button('howto','How to play',359,-137,142)
        frame(self,-470,-292,470,-197,'#211b2c')
        self.write(self.menu_text,-438,-230,'Your cups',16,WHITE,'left')
        self.write(self.menu_text,-438,-259,f"{len(self.profile['owned'])} / 6 collected   /   {self.profile['tickets']} tickets",12,MUTED,'left')
        self.draw_button('cabinet','Cup cabinet',321,-245,228)
        self.screen.update()

    def best_key(self):
        return f'{self.mode.lower()}_{self.difficulty.lower()}'

    def best_score(self):
        return int(self.scores.get(self.best_key(), 0))

    def save_high_score(self):
        if self.score > self.best_score():
            self.save_failed = not save_score(SAVE_FILE, self.scores, self.best_key(), self.score)

    def start_game(self):
        self.save_failed = False
        self.reward_failed = False
        self.score = 0
        self.level = 1
        self.lives = DIFFICULTIES[self.difficulty]['lives']

        # Reset combo/perfect for a new game
        self.combo = 0
        self.perfect = True

        self.begin_chapter()

    def draw_hud(self):
        self.hud_text.clear()
        self.screen.getcanvas().delete('hud_art')
        self.art_layer = 'hud_art'
        frame(self,-470,174,470,236,'#211b2c')
        self.rectangle(-166,186,-165,223,'#533f53')
        self.rectangle(142,186,143,223,'#533f53')
        self.write(self.hud_text,-445,209,f'{self.mode}  /  {self.difficulty}',12,WHITE,'left')
        self.write(self.hud_text,-445,185,f'Lives  {self.lives}',11,COLORS['danger'],'left')
        title = f'Chapter {self.level} of {STORY_LEVELS}' if self.mode=='Story' else f'Round {self.level}  /  Combo {self.combo}'
        self.write(self.hud_text,-12,207,title,13,GOLD)
        chapter = LOCATION_NAMES[location(self.mode,self.level)]
        self.write(self.hud_text,-12,185,chapter,10,MUTED)
        self.write(self.hud_text,443,207,f'Score  {self.score:,}',13,GOLD,'right')
        self.write(self.hud_text,443,185,f'Best  {self.best_score():,}',10,MUTED,'right')
        self.art_layer = 'scene'

    def set_message(self, text, detail='', color=WHITE):
        self.message.clear()
        self.screen.getcanvas().delete('message_art')
        self.write(self.message,-442,-222,text,18,color,'left')
        if self.state in ('result','retry','over','victory') and (getattr(self, 'save_failed', False) or self.reward_failed):
            detail = 'Save failed. Check folder permissions.'
        if detail:
            self.write(self.message,-442,-253,detail,12,MUTED,'left')
        if self.state in ('result','retry','over','victory'):
            label = 'Next' if self.state=='result' else 'Retry' if self.state=='retry' else 'Play again'
            self.art_layer='message_art'
            frame(self,239,-287,441,-245,GOLD,'#ffe0a0')
            self.art_layer='scene'
            self.write(self.message,340,-274,label,12,'#2b2030')
        self.draw_footer()

    def draw_footer(self):
        self.footer.clear()
        if self.state=='menu':
            left,right='Enter  Play    H  Help','Esc  Quit'
        elif self.state=='story':
            left,right='Enter  Continue' if self.story_page==0 else 'Enter  Play','M  Menu'
        elif self.state=='cabinet':
            left,right='Enter  Draw','Esc  Back'
        elif self.state=='gacha_opening':
            left,right='Enter  Reveal','Esc  Back'
        elif self.state in ('reveal','shuffle','select','paused'):
            left,right='P  Resume' if self.state=='paused' else 'P  Pause    S Sound','M  Menu'
        elif self.state in ('result','retry','over','victory'):
            left,right='Enter  Continue','M  Menu'
        else:
            left,right='','Esc  Back'
        self.write(self.footer,-464,-327,left,10,MUTED,'left')
        self.write(self.footer,464,-327,right,10,MUTED,'right')

    def selection_hint(self):
        return f'Click a cup or press 1-{len(self.cups)}.'

    def begin_chapter(self):
        if self.mode=='Story':
            self.story_page=0
            self.show_story()
        else:
            self.start_level()

    def show_story(self):
        self.state='story'
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear(); self.hud_text.clear(); self.message.clear()
        self.buttons={}
        setting,speaker,first,second=SCENES[self.level-1]
        frame(self,-470,174,470,236,'#211b2c')
        self.write(self.menu_text,-440,197,f'Chapter {self.level}',14,GOLD,'left')
        self.write(self.menu_text,440,197,LOCATION_NAMES[setting],14,WHITE,'right')
        self.write(self.menu_text,0,121,CHAPTERS[self.level-1][0],24,WHITE)
        colors={'Mira':('#829d8c','#36263b'),'Theo':('#b47b90','#b38361'),'Jun':('#8c9bbc','#272735')}
        shirt,hair=colors[speaker]
        guest(self,-53,-97,shirt,hair,6)
        self.write(self.message,-442,-220,speaker,16,GOLD,'left')
        self.write(self.message,-442,-252,(first,second)[self.story_page],13,WHITE,'left')
        self.draw_button('story_next','Continue' if self.story_page==0 else 'Play',340,-260,202,True)
        self.draw_footer()
        self.screen.update()

    def start_level(self):
        self.state = 'reveal'
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear()
        self.buttons = {}
        self.draw_hud()

        count, self.swaps, self.swap_duration, self.reveal_frames = \
            level_settings(self.level, self.difficulty)

        spacing = min(150, 760 / max(1, count - 1))
        self.slots = [
            (i - (count - 1) / 2) * spacing
            for i in range(count)
        ]

        self.cups = [
            Cup(i, self.slots[i], self.profile['equipped'])
            for i in range(count)
        ]

        for i, x in enumerate(self.slots):
            self.rectangle(x-15,-124,x+15,-96,'#312331')
            self.write(self.labels, x, -119, str(i + 1), 12, GOLD)

        self.correct_id = random.randrange(count)
        self.reveal_frame = 0
        self.completed_swaps = 0
        self.swap_pair = None
        self.state = 'reveal'
        self.last_tick = time.monotonic()
        self.frame_credit = 0.0

        special = self.cups[self.correct_id]
        special.y = 76
        special.render()

        self.ball.goto(special.x, -40)
        self.ball.showturtle()

        self.set_message(
            'Remember the spark',
            'Watch which cup holds it.'
        )

        self.play_tone('reveal')
        self.screen.listen()
        self.screen.update()

    def begin_shuffle(self):
        self.state = 'shuffle'
        self.ball.hideturtle()

        for cup in self.cups:
            cup.y = 0
            cup.render()

        self.set_message(
            'Follow the cup',
            ''
        )

    def animate_swap(self):
        if self.swap_pair is None:
            if self.completed_swaps >= self.swaps:
                self.state = 'select'
                self.set_message(
                    'Where is the spark?',
                    self.selection_hint()
                )
                return

            a, b = random.sample(self.cups, 2)
            self.swap_pair = (a, b, a.slot, b.slot)
            self.swap_frame = 0

        a, b, slot_a, slot_b = self.swap_pair
        self.swap_frame += 1

        t = min(1.0, self.swap_frame / self.swap_duration)
        eased = t * t * (3 - 2 * t)

        a.x = self.slots[slot_a] + \
            (self.slots[slot_b] - self.slots[slot_a]) * eased

        b.x = self.slots[slot_b] + \
            (self.slots[slot_a] - self.slots[slot_b]) * eased

        arc = math.sin(math.pi * t) * 37
        a.y = arc
        b.y = -arc

        a.render()
        b.render()

        if t >= 1:
            a.slot, b.slot = slot_b, slot_a
            a.x, b.x = self.slots[a.slot], self.slots[b.slot]
            a.y = b.y = 0

            a.render()
            b.render()

            self.completed_swaps += 1
            self.swap_pair = None

    def choose(self, slot):
        if self.state != 'select':
            return

        selected = next(
            (cup for cup in self.cups if cup.slot == slot), None
        )

        if selected is None:
            return

        # Lock the choice before screen.update can dispatch another input.
        self.state = 'resolving'
        correct = self.cups[self.correct_id]

        selected.y = 76
        selected.render()
        correct.y = 76
        correct.render()

        self.ball.goto(correct.x, -40)
        self.ball.showturtle()

        if selected is correct:

            # ENDLESS COMBO
            if self.mode == 'Endless':
                self.combo += 1
                combo_bonus = self.combo * 25
                points = (
                    self.level * 100
                    + (self.lives - 1) * 20
                    + combo_bonus
                )

            # STORY NORMAL SCORING
            else:
                points = self.level * 100 + (self.lives - 1) * 20

            reward_key = f'{self.difficulty}:{self.level}' if self.mode=='Story' else None
            earned = collection.reward(collection.PROFILE_FILE,self.profile,reward_key)
            self.reward_failed = earned == -1
            earned_text = '  /  +1 ticket' if earned==1 else ''
            self.score += points
            self.save_high_score()
            self.draw_hud()
            self.play_tone('correct')

            if self.mode == 'Story' and self.level >= STORY_LEVELS:
                self.state = 'victory'

                # PERFECT STORY BONUS
                if self.perfect:
                    self.score += 1000
                    self.save_high_score()

                    self.set_message(
                        'The wish came true',
                        'Mira: This house feels like home again. Thank you.',
                        GOLD
                    )
                    self.draw_hud()
                    self.write(self.message,-442,-279,'+1,000 perfect bonus',10,GOLD,'left')
                else:
                    self.set_message(
                        'The wish came true',
                        'Mira: Same time next year? Your seat will be here.'
                    )

                self.play_tone('win')

            else:
                self.state = 'result'

                if self.mode == 'Endless':
                    self.set_message(
                        'Found it',
                        f'+{points} points{earned_text}'
                    )
                else:
                    self.set_message(
                        'Found it',
                        f'+{points} points{earned_text}'
                    )


        else:
            self.lives -= 1

            # Combo Break
            if self.mode == 'Endless':
                self.combo = 0

            # Perfect Break
            else:
                self.perfect = False

            self.draw_hud()
            self.play_tone('wrong')

            if self.lives > 0:
                self.state = 'retry'

                self.set_message(
                    'Not this cup',
                    f'{self.lives} lives left.'
                )

            else:
                self.state = 'over'

                self.set_message(
                    'Party over',
                    f'Final score: {self.score:,}'
                )

    def on_click(self, x, y):
        if self.state == 'menu':
            for key, (x1, y1, x2, y2) in list(self.buttons.items()):
                if x1 <= x <= x2 and y1 <= y <= y2:

                    if key.startswith('mode:'):
                        self.mode = key.split(':', 1)[1]
                        self.show_menu()

                    elif key.startswith('diff:'):
                        self.difficulty = key.split(':', 1)[1]
                        self.show_menu()

                    elif key == 'start':
                        self.start_game()

                    elif key == 'cabinet':
                        self.show_cabinet()

                    elif key == 'howto':
                        self.show_how_to_play()

                    return

        elif self.state in ('story','cabinet','odds','gacha_reveal'):
            for key,(x1,y1,x2,y2) in list(self.buttons.items()):
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.collection_action(key)
                    return

        elif self.state == 'how_to_play':
            if 'back' in self.buttons:
                x1, y1, x2, y2 = self.buttons['back']

                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.show_menu()

        elif self.state == 'select':
            for cup in self.cups:
                if (abs(x-cup.x)<=48 and -51<=y<=51) or (abs(x-cup.x)<=15 and -124<=y<=-96):
                    self.choose(cup.slot)
                    return

        elif self.state in ('result', 'retry', 'over', 'victory') and 239 <= x <= 441 and -287 <= y <= -245:
            self.advance()

    def advance(self):
        if self.state == 'menu':
            self.start_game()

        elif self.state == 'how_to_play':
            self.show_menu()

        elif self.state=='story':
            if self.story_page==0:
                self.story_page=1
                self.show_story()
            else:
                self.start_level()

        elif self.state=='gacha_reveal':
            self.show_cabinet()

        elif self.state=='gacha_opening':
            self.reveal_draw()

        elif self.state=='cabinet':
            self.draw_cup()

        elif self.state in ('over', 'victory'):
            self.start_game()

        elif self.state == 'result':
            self.level += 1
            self.begin_chapter()

        elif self.state == 'retry':
            self.start_level()

    def restart(self):
        self.start_game()

    def play_tone(self, kind):
        if self.sound_enabled:
            tone(kind, self.screen)

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.screen.title('Guess Which Cup | Lantern House | Sound ' +
                          ('on' if self.sound_enabled else 'off'))

    def cycle_mode(self):
        if self.state == 'menu':
            self.mode = 'Endless' if self.mode == 'Story' else 'Story'
            self.show_menu()

    def cycle_difficulty(self, direction=1):
        if self.state == 'menu':
            names = list(DIFFICULTIES)
            self.difficulty = names[(names.index(self.difficulty)+direction) % len(names)]
            self.show_menu()

    def toggle_pause(self):
        if self.state == 'paused':
            self.state = self.paused_state
            self.last_tick = time.monotonic()
            self.frame_credit = 0.0
            if self.state == 'select':
                self.set_message('Where is the spark?', self.selection_hint())
            elif self.state == 'reveal':
                self.set_message('Remember the spark', 'Watch which cup holds it.')
            else:
                self.set_message('Follow the cup', '')
        elif self.state in ('reveal', 'shuffle', 'select'):
            self.paused_state = self.state
            self.state = 'paused'
            self.set_message('Paused', '')

    def escape(self):
        if self.state == 'menu':
            self.close()
        elif self.state in ('odds','gacha_reveal','gacha_opening'):
            self.show_cabinet()
        else:
            self.show_menu()

    def close(self):
        self.running = False
        self.screen.bye()

    def update(self):
        if not self.running:
            return
        try:
            now = time.monotonic()
            # Use elapsed time so the difficulty does not depend on render speed.
            self.frame_credit += min(now-self.last_tick, 0.1) * 1000 / FRAME_MS
            self.last_tick = now
            steps = int(self.frame_credit)
            self.frame_credit -= steps
            for _ in range(steps):
                if self.state == 'reveal':
                    self.reveal_frame += 1
                    if self.reveal_frame >= self.reveal_frames:
                        self.begin_shuffle()
                elif self.state == 'shuffle':
                    self.animate_swap()
                elif self.state == 'gacha_opening':
                    self.animate_draw()
            self.screen.update()
            if self.running:
                self.screen.ontimer(self.update, FRAME_MS)
        except (turtle.Terminator, tkinter.TclError):
            self.running = False


if __name__ == '__main__':
    Game()
