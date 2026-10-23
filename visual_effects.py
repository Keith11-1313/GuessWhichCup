"""Short canvas animations. Rewards are saved by gameplay, never by animation."""

from game_theme import label_width


class VisualEffects:
    def __init__(self, session):
        self.session = session
        self.kind = None
        self.frame = 0

    def clear(self):
        self.session.screen.getcanvas().delete("reward_fx")
        self.kind = None
        self.frame = 0

    def award(self, points, ticket):
        self.clear()
        self.kind = "award"
        self.points, self.ticket = points, ticket
        self.draw()

    def duplicate(self, skin):
        self.clear()
        self.kind = "duplicate"
        self.skin = skin
        self.draw()

    def update(self):
        if self.kind:
            self.frame += 1
            self.draw()

    def label(self, text, y, size, color):
        x = -label_width(text, size) / 2
        self.session.views.canvas_label(x, -y, text, size, color, ("reward_fx",))

    def draw(self):
        g = self.session
        canvas = g.screen.getcanvas()
        canvas.delete("reward_fx")
        if self.kind == "award":
            if self.frame >= 100:
                self.clear()
                return
            rise = min(42, self.frame * .55)
            canvas.create_rectangle(-143, 40-rise, 143, 119-rise, fill="#211b2c", outline="#947454", tags=("reward_fx",))
            canvas.create_image(-116, 64-rise, image=g.assets["coin"], tags=("reward_fx",))
            self.label(f"+{self.points:,} points", -64+rise, 18, "#ffe1a0")
            if self.ticket:
                canvas.create_image(-105, 96-rise, image=g.assets["icons"]["ticket"], tags=("reward_fx",))
                self.label("+1 ticket", -96+rise, 14, "#a9d7ab")
        elif self.kind == "duplicate":
            if self.frame < 45:
                size = max(0, 3 - self.frame // 12)
                image = g.assets["skins"][self.skin][size]
                canvas.create_image(0, -60, image=image, tags=("reward_fx",))
            else:
                image = g.assets["ticket_reward"]
                canvas.create_image(0, -60 - min(12, (self.frame-45)*.3), image=image, tags=("reward_fx",))
                self.label("+1 ticket", -118, 18, "#a9d7ab")
            if self.frame >= 100:
                self.kind = None  # Keep the converted ticket visible until navigation.
