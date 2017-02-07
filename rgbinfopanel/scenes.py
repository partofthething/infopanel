"""Scenes. One of these will be active at any given time."""


from rgbmatrix import graphics
from rgbinfopanel import sprites, helpers
from rgbinfopanel import colors
from PIL import Image

class Scene(object):
    def __init__(self, disp):
        self.disp = disp
        self.common_sprites = []
        self.active = False

        # build some data sources that are available to all sprites.
        self.i5 = sprites.Duration()
        self.i5.add('I90', lambda : int(self.disp.live_data['travel_time_i90']))
        self.wa520 = sprites.Duration()
        self.wa520.add('520', lambda: int(self.disp.live_data['travel_time_520']))
        self.daily_high = sprites.Temperature()
        self.daily_high.add('H', lambda: float(self.disp.live_data['daily_high']))
        self.daily_low = sprites.Temperature()
        self.daily_low.add('L', lambda: float(self.disp.live_data['daily_low']))
        self.current = sprites.Temperature()
        self.current.add('C', lambda: float(self.disp.live_data['current_temp']))
        self.common_sprites.extend([self.i5, self.wa520, self.daily_high,
                                    self.daily_low, self.current])

    def clear(self):
        self.disp.canvas.Clear()

    def draw_frame(self):
        raise NotImplementedError

    def buffer(self):
        self.disp.canvas = self.disp.matrix.SwapOnVSync(self.disp.canvas)


class FullImage(Scene):
    """
    Full screen bitmap image.

    Notes
    -----
    Currently, this crashes the library every once in a while. Unstable!!
    """
    def __init__(self, disp, fname):
        Scene.__init__(self, disp)
        self.image = Image.open(fname)
        self.image.thumbnail((self.disp.matrix.width, self.disp.matrix.height), Image.ANTIALIAS)
        self.image = self.image.convert('RGB')

    def draw_frame(self):
        self.disp.canvas.SetImage(self.image)


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
        self.i5.y = self.disp.font.height
        self.wa520.y = self.disp.font.height * 2
        self.daily_high.x = 33
        self.daily_high.y = self.disp.font.height
        self.daily_low.y = self.disp.font.height * 2
        self.daily_low.x = 33

        self.vehicle = sprites.FancyText(0, self.disp.font.height * 3, 'VROOM!!')
        self.scroll = sprites.FancyText(disp.canvas.width, self.disp.font.height * 4)
        self.scroll.add('HECK ', colors.GREEN)
        self.scroll.add('YEAH', colors.BLUE)
        self.scroll.dx = -1
        self.scroll.ticks_per_movement = 1

    def draw_frame(self):
        for sprite in [self.i5, self.wa520, self.daily_high, self.daily_low,
                       self.vehicle, self.scroll]:
            sprite.render(self.disp.canvas)


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
            giraffe.phrases.extend(3 * self.common_sprites)

        self.plants = [sprites.Plant(x, y) for (x, y) in [(30, 10), (10, 20), (40, 5)]]

    def draw_frame(self):
        for plant in self.plants:
            plant.render(self.disp.canvas)
        for giraffe in self.giraffes:
            giraffe.render(self.disp.canvas)


