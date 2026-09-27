

import json
import math
import random
import sys
import turtle
import tkinter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUP_GIF = ROOT / 'cup.gif'
SAVE_FILE = ROOT / 'what_the_cup_scores.json'
WIDTH, HEIGHT = 1000, 700
FRAME_MS = 17
STORY_LEVELS = 10
BG = '#131a2e'
WHITE = '#f4f7ff'
MUTED = '#b8c4e1'
GOLD = '#f9cf49'
DIFFICULTIES = {
    'Easy':   {'extra_swaps': 0, 'duration': 1.35, 'reveal': 1.45, 'lives': 5},
    'Normal': {'extra_swaps': 2, 'duration': 1.00, 'reveal': 1.00, 'lives': 3},
    'Hard':   {'extra_swaps': 5, 'duration': 0.72, 'reveal': 0.70, 'lives': 2},
}


def level_settings(level, difficulty):
    tune = DIFFICULTIES[difficulty]
    cups = min(6, 3 + (level - 1) // 3)
    swaps = 4 + level * 2 + tune['extra_swaps']
    frames = max(9, round(max(15, 45 - (level - 1) * 3) * tune['duration']))
    reveal = max(65, round(max(100, 175 - (level - 1) * 6) * tune['reveal']))
    return cups, swaps, frames, reveal


def load_scores():
    try:
        data = json.loads(SAVE_FILE.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def make_writer(color=WHITE):
    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.penup()
    t.color(color)
    return t


def tone(kind, screen):
    sounds = {
        'reveal': [(700, 90)], 'correct': [(700, 80), (1000, 130)],
        'wrong': [(330, 150), (240, 180)], 'win': [(620, 70), (820, 80), (1100, 140)]
    }
    if sys.platform == 'win32':
        try:
            import winsound
            # MessageBeep doesn't block the GUI animation like Beep does.
            winsound.MessageBeep(winsound.MB_OK if kind in ('correct', 'win') else winsound.MB_ICONEXCLAMATION)
            return
        except (ImportError, RuntimeError, OSError):
            pass
    try:
        screen.getcanvas().bell()
    except Exception:
        pass


class Cup:
    def __init__(self, cid, x):
        self.cid = cid
        self.slot = cid
        self.x = x
        self.y = 0
        self.sprite = turtle.Turtle(visible=False)
        self.sprite.speed(0)
        self.sprite.penup()
        self.sprite.shape('gold_cup')
        self.sprite.goto(x, 0)
        self.sprite.showturtle()

    def render(self):
        self.sprite.goto(self.x, self.y)

    def hide(self):
        self.sprite.hideturtle()


class Game:
    def __init__(self):
        if not CUP_GIF.exists():
            raise FileNotFoundError('cup.gif is missing. Extract the entire ZIP into one folder.')
        self.screen = turtle.Screen()
        self.screen.setup(WIDTH, HEIGHT)
        self.screen.title('GUESS WHICH CUP!| by @RENE')
        self.screen.bgcolor(BG)
        self.screen.tracer(0)
        self.screen.register_shape('gold_cup', str(CUP_GIF))

        self.static = make_writer()
        self.menu_text = make_writer()
        self.hud_text = make_writer()
        self.message = make_writer()
        self.labels = make_writer(MUTED)
        self.ball = turtle.Turtle(visible=False)
        self.ball.speed(0)
        self.ball.penup()
        self.ball.shape('circle')
        self.ball.shapesize(0.85)
        self.ball.color(GOLD)

        self.scores = load_scores()
        self.mode = 'Story'
        self.difficulty = 'Normal'
        self.level = 1
        self.score = 0
        self.lives = 3
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
        self.result_good = False
        self.buttons = {}

        self.screen.onclick(self.on_click)
        self.screen.listen()
        for key in ('Return', 'space'):
            self.screen.onkeypress(self.advance, key)
        for key in ('m', 'M'):
            self.screen.onkeypress(self.show_menu, key)
        for key in ('r', 'R'):
            self.screen.onkeypress(self.restart, key)
        for n in range(1, 7):
            self.screen.onkeypress(lambda number=n: self.choose(number - 1), str(n))
        self.screen.onkeypress(self.screen.bye, 'Escape')
        self.show_menu()
        self.screen.ontimer(self.update, FRAME_MS)
        self.screen.mainloop()

    def write(self, pen, x, y, text, size=16, color=WHITE, align='center'):
        pen.color(color)
        pen.goto(x, y)
        pen.write(text, align=align, font=('Arial', size, 'bold'))

    def rectangle(self, x1, y1, x2, y2, fill, outline=None):
        p = self.static
        p.goto(x1, y1)
        p.setheading(0)
        p.color(outline or fill, fill)
        p.pendown()
        p.begin_fill()
        for _ in range(2):
            p.forward(x2 - x1)
            p.left(90)
            p.forward(y2 - y1)
            p.left(90)
        p.end_fill()
        p.penup()

    def draw_background(self):
        self.static.clear()
        self.rectangle(-460, -165, 460, -157, '#304364')
        self.rectangle(-465, -176, 465, -168, '#17243d')
        self.write(self.static, 0, 283, 'GUESS WHICH CUP!', 32, GOLD)
        self.write(self.static, 0, 251, '@RENE', 12, MUTED)
        self.write(self.static, 0, -309,
                   'CLICK A CUP or 1–6   •   ENTER: continue   •   R: restart   •   M: menu   •   ESC: exit',
                   11, MUTED)

    def draw_button(self, name, text, x, y, width, active=False):
        color = '#e3b132' if active else '#293a5b'
        edge = GOLD if active else '#627495'
        self.rectangle(x-width/2, y-19, x+width/2, y+19, color, edge)
        self.write(self.menu_text, x, y-7, text, 13, '#111b30' if active else WHITE)
        self.buttons[name] = (x-width/2, y-19, x+width/2, y+19)

    def clear_cups(self):
        for cup in self.cups:
            cup.hide()
        self.cups = []
        self.ball.hideturtle()
        self.labels.clear()

    def show_menu(self):
        self.state = 'menu'
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear()
        self.hud_text.clear()
        self.message.clear()
        self.buttons = {}
        self.write(self.menu_text, 0, 181, 'Choose your game mode', 19)
        self.draw_button('mode:Story', 'STORY  (10 levels)', -180, 120, 250, self.mode == 'Story')
        self.draw_button('mode:Endless', 'ENDLESS', 180, 120, 250, self.mode == 'Endless')
        self.write(self.menu_text, 0, 56, 'Choose your difficulty', 19)
        self.draw_button('diff:Easy', 'EASY  •  5 lives', -250, -1, 185, self.difficulty == 'Easy')
        self.draw_button('diff:Normal', 'NORMAL  •  3 lives', 0, -1, 185, self.difficulty == 'Normal')
        self.draw_button('diff:Hard', 'HARD  •  2 lives', 250, -1, 185, self.difficulty == 'Hard')
        self.draw_button('start', 'START GAME', 0, -97, 270, True)
        self.write(self.menu_text, 0, -215,
                   'Story: clear all 10 levels  |  Endless: survive as long as you can', 13, MUTED)
        self.write(self.menu_text, 0, -242,
                   'Higher difficulty = faster shuffles, more swaps and shorter reveals', 11, MUTED)
        self.screen.update()

    def best_key(self):
        return f'{self.mode.lower()}_{self.difficulty.lower()}'

    def best_score(self):
        return int(self.scores.get(self.best_key(), 0))

    def save_high_score(self):
        if self.score <= self.best_score():
            return
        self.scores[self.best_key()] = self.score
        try:
            SAVE_FILE.write_text(json.dumps(self.scores, indent=2), encoding='utf-8')
        except OSError:
            pass

    def start_game(self):
        self.score = 0
        self.level = 1
        self.lives = DIFFICULTIES[self.difficulty]['lives']
        self.start_level()

    def draw_hud(self):
        self.hud_text.clear()
        self.write(self.hud_text, -427, 207,
                   f'{self.mode.upper()}  |  {self.difficulty.upper()}  |  LEVEL {self.level}',
                   14, WHITE, 'left')
        self.write(self.hud_text, -427, 170, f'LIVES: {"♥" * self.lives}', 15, '#ff8294', 'left')
        self.write(self.hud_text, 430, 207, f'SCORE: {self.score}', 14, GOLD, 'right')
        self.write(self.hud_text, 430, 170, f'BEST: {self.best_score()}', 14, MUTED, 'right')
        if self.mode == 'Story':
            self.write(self.hud_text, 0, 213, f'CHAPTER {self.level}/{STORY_LEVELS}', 13, MUTED)

    def set_message(self, text, detail=''):
        self.message.clear()
        self.write(self.message, 0, -214, text, 18, WHITE)
        if detail:
            self.write(self.message, 0, -246, detail, 12, MUTED)

    def start_level(self):
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear()
        self.buttons = {}
        self.draw_hud()
        count, self.swaps, self.swap_duration, self.reveal_frames = level_settings(self.level, self.difficulty)
        spacing = min(150, 760 / max(1, count-1))
        self.slots = [(i - (count-1)/2)*spacing for i in range(count)]
        self.cups = [Cup(i, self.slots[i]) for i in range(count)]
        for i, x in enumerate(self.slots):
            self.write(self.labels, x, -107, str(i+1), 15, MUTED)
        self.correct_id = random.randrange(count)
        self.reveal_frame = 0
        self.completed_swaps = 0
        self.swap_pair = None
        self.state = 'reveal'
        special = self.cups[self.correct_id]
        special.y = 76
        special.render()
        self.ball.goto(special.x, -40)
        self.ball.showturtle()
        self.set_message('MEMORIZE THE BALL!', 'Follow the golden cup when it moves.')
        tone('reveal', self.screen)

    def begin_shuffle(self):
        self.state = 'shuffle'
        self.ball.hideturtle()
        for cup in self.cups:
            cup.y = 0
            cup.render()
        self.set_message('SHUFFLING...', f'Watch closely: {self.swaps} swaps this round.')

    def animate_swap(self):
        if self.swap_pair is None:
            if self.completed_swaps >= self.swaps:
                self.state = 'select'
                self.set_message('WHERE IS THE BALL?', 'Click a cup or press its number (1–6).')
                return
            a, b = random.sample(self.cups, 2)
            self.swap_pair = (a, b, a.slot, b.slot)
            self.swap_frame = 0
        a, b, slot_a, slot_b = self.swap_pair
        self.swap_frame += 1
        t = min(1.0, self.swap_frame/self.swap_duration)
        eased = t*t*(3 - 2*t)
        a.x = self.slots[slot_a] + (self.slots[slot_b]-self.slots[slot_a])*eased
        b.x = self.slots[slot_b] + (self.slots[slot_a]-self.slots[slot_b])*eased
        arc = math.sin(math.pi*t)*37
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
        selected = next((cup for cup in self.cups if cup.slot == slot), None)
        if selected is None:
            return
        correct = self.cups[self.correct_id]
        selected.y = 76
        selected.render()
        correct.y = 76
        correct.render()
        self.ball.goto(correct.x, -40)
        self.ball.showturtle()
        if selected is correct:
            self.score += self.level * 100 + (self.lives-1)*20
            self.save_high_score()
            self.draw_hud()
            tone('correct', self.screen)
            if self.mode == 'Story' and self.level >= STORY_LEVELS:
                self.state = 'victory'
                self.set_message('STORY COMPLETE! YOU ARE THE CUP MASTER!',
                                 f'Final score: {self.score}  •  ENTER: play again  •  M: menu')
                tone('win', self.screen)
            else:
                self.state = 'result'
                self.set_message('CORRECT! GREAT MEMORY!',
                                 f'+{self.level*100+(self.lives-1)*20} points  •  ENTER: next level')
        else:
            self.lives -= 1
            self.draw_hud()
            tone('wrong', self.screen)
            if self.lives > 0:
                self.state = 'retry'
                self.set_message('WRONG CUP!', f'{self.lives} lives left  •  ENTER: retry level')
            else:
                self.state = 'over'
                self.set_message('GAME OVER!', f'Score: {self.score}  •  ENTER: retry  •  M: menu')

    def on_click(self, x, y):
        if self.state == 'menu':
            for key, (x1, y1, x2, y2) in self.buttons.items():
                if x1 <= x <= x2 and y1 <= y <= y2:
                    if key.startswith('mode:'):
                        self.mode = key.split(':', 1)[1]
                        self.show_menu()
                    elif key.startswith('diff:'):
                        self.difficulty = key.split(':', 1)[1]
                        self.show_menu()
                    elif key == 'start':
                        self.start_game()
                    return
        elif self.state == 'select':
            # Actual hitbox approximates 81x108 cup sprite, centered at y=0.
            for cup in self.cups:
                if abs(x-cup.x) <= 43 and -53 <= y <= 55:
                    self.choose(cup.slot)
                    return

    def advance(self):
        if self.state in ('menu', 'over', 'victory'):
            self.start_game()
        elif self.state == 'result':
            self.level += 1
            self.start_level()
        elif self.state == 'retry':
            self.start_level()

    def restart(self):
        self.start_game()

    def update(self):
        try:
            if self.state == 'reveal':
                self.reveal_frame += 1
                if self.reveal_frame >= self.reveal_frames:
                    self.begin_shuffle()
            elif self.state == 'shuffle':
                self.animate_swap()
            self.screen.update()
            self.screen.ontimer(self.update, FRAME_MS)
        except (turtle.Terminator, tkinter.TclError):
            return


if __name__ == '__main__':
    Game()
