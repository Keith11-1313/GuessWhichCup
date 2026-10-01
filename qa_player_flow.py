"""Exercise real Tk mouse/key events with isolated saves.

Run python -B qa_player_flow.py. Optional --screenshots DIR needs Pillow.
This is a developer QA tool; the game has no Pillow dependency.
"""
import argparse
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

import what_the_cup as app
import cup_collection as collection


def run(screenshot_dir=None):
    saved_scores,saved_profile=app.SAVE_FILE,collection.PROFILE_FILE
    with tempfile.TemporaryDirectory() as folder:
        app.SAVE_FILE=Path(folder)/'scores.json'
        collection.PROFILE_FILE=Path(folder)/'profile.json'
        game=app.Game(run_loop=False)
        game.sound_enabled=False
        root=game.screen.getcanvas().winfo_toplevel()
        canvas=game.screen.getcanvas()._canvas
        captured=[]

        def pump(seconds=.04):
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                root.update()
                time.sleep(.004)

        def click(x,y):
            canvas.event_generate('<Button-1>',x=round(x-canvas.canvasx(0)),
                                  y=round(-y-canvas.canvasy(0)))
            pump(.015)

        def button(name):
            x1,y1,x2,y2=game.buttons[name]
            click((x1+x2)/2,(y1+y2)/2)

        def key(name):
            canvas.focus_force()
            canvas.event_generate('<KeyPress>',keysym=name)
            pump(.015)

        def wait_for(state,timeout=30):
            deadline=time.monotonic()+timeout
            while game.state!=state and time.monotonic()<deadline:
                pump()
            assert game.state==state,(state,game.state)

        def capture(name):
            if screenshot_dir:
                from PIL import ImageGrab
                screenshot_dir.mkdir(exist_ok=True,parents=True)
                game.screen.update(); root.update_idletasks()
                ImageGrab.grab(bbox=(root.winfo_rootx(),root.winfo_rooty(),
                    root.winfo_rootx()+root.winfo_width(),root.winfo_rooty()+root.winfo_height()
                    )).save(screenshot_dir/(name+'.png'))
                captured.append(name)

        try:
            pump(.1)
            capture('complete-menu')
            button('cabinet'); assert game.state=='cabinet'
            capture('complete-cabinet')
            button('odds'); assert game.state=='odds'
            capture('complete-odds')
            button('cabinet')
            with patch('cup_collection.random.randrange',return_value=7700):
                button('draw')
            assert game.state=='gacha_opening'
            capture('complete-draw-opening')
            wait_for('gacha_reveal'); capture('complete-draw-rare')
            button('equip:rare')
            assert collection.load_profile(collection.PROFILE_FILE)['equipped']=='rare'
            button('back'); button('diff:Easy'); button('start')
            for level in range(1,11):
                assert game.level==level
                assert game.state=='story'
                capture('complete-story-'+str(level))
                button('story_next'); assert game.story_page==1
                key('Return'); assert game.state=='reveal'
                assert {cup.sprite.shape() for cup in game.cups}=={'rare_cup'}
                capture('complete-game-'+str(level))
                wait_for('select')
                assert game.selection_hint()==f'Click a cup or press 1-{len(game.cups)}.'
                capture('complete-select-'+str(len(game.cups)))
                if level==1:
                    key('6'); assert game.state=='select'
                    wrong=next(cup.slot for cup in game.cups if cup.cid!=game.correct_id)
                    key(str(wrong+1)); assert game.state=='retry'
                    capture('complete-retry')
                    click(340,-266); assert game.state=='reveal'
                    wait_for('select')
                key(str(game.cups[game.correct_id].slot+1))
                assert game.state==('victory' if level==10 else 'result')
                if level<10:
                    click(340,-266)
                print('Verified Story chapter',level,flush=True)
            capture('complete-ending')
            key('m'); button('mode:Endless'); button('start')
            assert game.state=='reveal' and game.scene_location=='afterparty'
            capture('complete-endless')
            key('p'); assert game.state=='paused'
            key('p'); assert game.state=='reveal'
            wait_for('select')
            click(game.cups[game.correct_id].x,0)
            assert game.state=='result'
            key('Return'); assert game.level==2
            key('m'); button('cabinet')
            assert game.profile['tickets']==11
            assert collection.load_profile(collection.PROFILE_FILE)==game.profile
            print('Verified real mouse/key story, retry, all cup counts, gacha, equip, saves, Endless and pause.',flush=True)
            if screenshot_dir:
                from PIL import Image
                names=['complete-menu','complete-cabinet','complete-draw-rare',
                       'complete-story-4','complete-game-4','complete-game-7',
                       'complete-game-10','complete-endless','complete-ending']
                sheet=Image.new('RGB',(1500,1050),'#191522')
                for i,name in enumerate(names):
                    with Image.open(screenshot_dir/(name+'.png')) as photo:
                        photo.thumbnail((500,350))
                        sheet.paste(photo,((i%3)*500,(i//3)*350))
                sheet.save(screenshot_dir/'complete-review.png')
        finally:
            game.close()
            app.SAVE_FILE=saved_scores
            collection.PROFILE_FILE=saved_profile


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--screenshots',type=Path)
    run(parser.parse_args().screenshots)
