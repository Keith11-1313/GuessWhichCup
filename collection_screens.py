"""Cup cabinet screens, kept separate from round gameplay."""
import cup_collection as collection
from party_art import frame
from game_config import COLORS


class CupCabinet:
    def cabinet_shell(self,state):
        self.state=state
        self.clear_cups()
        self.draw_background()
        self.menu_text.clear(); self.hud_text.clear(); self.message.clear()
        self.buttons={}

    def show_cabinet(self,notice=''):
        self.cabinet_shell('cabinet')
        frame(self,-470,174,470,236,'#211b2c')
        self.write(self.menu_text,-440,202,'Cup cabinet',18,COLORS['gold'],'left')
        self.write(self.menu_text,440,204,f"Tickets  {self.profile['tickets']}",16,COLORS['white'],'right')
        self.write(self.menu_text,440,184,'Earn one for each new win.',10,COLORS['muted'],'right')
        for index,(skin,name,rarity,weight,color) in enumerate(collection.CUPS):
            x=(-306,0,306)[index%3]; y=96 if index<3 else -66
            owned=skin in self.profile['owned']
            active=self.profile['equipped']==skin
            frame(self,x-132,y-72,x+132,y+72,'#302539',color if active else '#715166')
            hidden=skin=='mythic' and not owned
            self.write(self.menu_text,x,y+47,'Unseen cup' if hidden else name,13,color)
            self.write(self.menu_text,x,y+27,'???' if hidden else rarity,10,COLORS['muted'])
            self.static.shape('secret_preview' if hidden else skin+'_preview')
            self.static.goto(x,y-14)
            self.static.stamp()
            self.write(self.menu_text,x,y-67,'Equipped' if active else 'Click to equip' if owned else 'Locked',10,color if owned else COLORS['muted'])
            if owned:
                self.buttons['equip:'+skin]=(x-132,y-72,x+132,y+72)
        self.write(self.menu_text,-440,-215,notice or 'A little surprise from the party.',13,COLORS['white'],'left')
        self.draw_button('draw','Draw / 3 tickets',-290,-254,284,self.profile['tickets']>=collection.DRAW_COST)
        self.draw_button('odds','Odds',26,-254,174)
        self.draw_button('back','Back',322,-254,202)
        self.draw_footer()
        self.screen.update()

    def show_odds(self):
        self.cabinet_shell('odds')
        frame(self,-310,-155,310,224,'#241d30')
        self.write(self.menu_text,-277,179,'Every draw, every chance',21,COLORS['gold'],'left')
        for index,(_,name,rarity,weight,color) in enumerate(collection.CUPS):
            y=129-index*41
            self.write(self.menu_text,-277,y,rarity,14,color,'left')
            self.write(self.menu_text,275,y,f'{weight/100:g}%',14,COLORS['white'],'right')
        self.set_message('Three tickets per draw','Duplicates return one ticket. Cups are cosmetic.')
        self.draw_button('cabinet','Back',340,-260,202,True)
        self.screen.update()

    def draw_cup(self):
        if self.state!='cabinet':
            return
        skin,status=collection.draw(collection.PROFILE_FILE,self.profile)
        if skin is None:
            self.show_cabinet(status)
            return
        self.pending_cup=skin
        self.draw_status=status
        self.draw_frame=0
        self.cabinet_shell('gacha_opening')
        self.set_message('Opening your gift','')
        self.animate_draw()

    def animate_draw(self):
        self.draw_frame+=1
        if self.draw_frame>=48:
            self.reveal_draw()
            return
        self.screen.getcanvas().delete('draw_fx')
        self.art_layer='draw_fx'
        center=32
        width=28+self.draw_frame//2
        frame(self,-width,center-50,width,center+50,'#594050','#f2bf68')
        for i in range(8):
            x=-160+(i*43)%320
            y=-60+(i*31+self.draw_frame*3)%180
            self.rectangle(x,y,x+3,y+3,'#f2bf68')
        self.art_layer='scene'

    def reveal_draw(self):
        skin,status=self.pending_cup,self.draw_status
        self.cabinet_shell('gacha_reveal')
        _,name,rarity,_,color=next(cup for cup in collection.CUPS if cup[0]==skin)
        self.write(self.menu_text,0,161,rarity,18,color)
        self.static.shape(skin+'_hero'); self.static.goto(0,60); self.static.stamp()
        self.write(self.menu_text,0,-70,name,22,color)
        self.set_message('Already yours' if status=='duplicate' else 'A new cup',
                         'One ticket returned.' if status=='duplicate' else 'Equip it for your next game.')
        self.draw_button('equip:'+skin,'Equip',80,-260,202,True)
        self.draw_button('cabinet','Keep browsing',340,-260,202)
        self.play_tone('win')
        self.screen.update()

    def collection_action(self,key):
        if key=='story_next':
            self.advance()
        elif key=='draw':
            self.draw_cup()
        elif key=='odds':
            self.show_odds()
        elif key=='back':
            self.show_menu()
        elif key=='cabinet':
            self.show_cabinet()
        elif key.startswith('equip:'):
            skin=key.split(':',1)[1]
            if collection.equip(collection.PROFILE_FILE,self.profile,skin):
                self.show_cabinet('Cup equipped.')
            else:
                self.show_cabinet('Could not save. Try again.')
