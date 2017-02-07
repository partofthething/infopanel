"""Scenes."""

from rgbmatrix import graphics
from rgbinfopanel import sprites, helpers
from rgbinfopanel import colors

class Scene(object):
    def __init__(self, disp):
        self.disp = disp

    def draw_frame(self):
        raise NotImplementedError


class Welcome(Scene):
    """Just a welcome message."""
    def __init__(self, disp):
        Scene.__init__(self, disp)
        self.font = helpers.load_font('9x15B.bdf')

    def draw_frame(self):
        self.disp.rainbow_text(self.disp.canvas, self.font, 5, 20, 'HELLO!')


class Traffic(Scene):
    """A scene with some traffic info."""
    def __init__(self, disp):
        Scene.__init__(self, disp)
        self.i5 = sprites.Duration(0, self.disp.font.height)
        self.wa520 = sprites.Duration(0, self.disp.font.height * 2)
        self.update_traffic()
        self.vehicle = sprites.FancyText(0, self.disp.font.height * 3, 'VROOM!!')
        self.scroll = sprites.FancyText(disp.canvas.width, self.disp.font.height * 4)
        self.scroll.add('HECK ', colors.GREEN)
        self.scroll.add('YEAH', colors.RED)
        self.scroll.dx = -1
        self.scroll.ticks_per_movement = 1

    def draw_frame(self):
        for sprite in [self.i5, self.wa520, self.vehicle, self.scroll]:
            sprite.render(self.disp.canvas)

    def update_traffic(self):
        # slow if you put it every frame.
        self.i5.clear()
        self.i5.add('I90', lambda : int(self.disp.live_data['travel_time_i90']))
        self.wa520.clear()
        self.wa520.add('520', lambda: int(self.disp.live_data['travel_time_520']))



class Giraffes(Scene):
    """A field of giraffes saying things."""
    def __init__(self, disp):
        Scene.__init__(self, disp)
        self.giraffes = [sprites.Giraffe() for _i in range(3)]
        self.giraffes[1].flip_horizontal()
        self.giraffes[1].dx = -1
        self.giraffes[1].y = 18
        self.giraffes[2].ticks_per_movement = 2
        self.giraffes[2].y = 10
        for giraffe in self.giraffes:
            giraffe.phrases.extend([self.i5_time, self.wa520_time])

        self.plants = [sprites.Plant(x, y) for (x, y) in [(30, 10), (10, 20), (40, 5)]]

    def i5_time(self):
        return 'I90: {}'.format(self.disp.live_data['travel_time_i90'])

    def wa520_time(self):
        return '520: {}'.format(self.disp.live_data['travel_time_520'])

    def draw_frame(self):
        for plant in self.plants:
            plant.render(self.disp.canvas)
        for giraffe in self.giraffes:
            giraffe.render(self.disp.canvas)


