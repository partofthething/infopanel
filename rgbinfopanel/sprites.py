"""There are multiple sprites in any given scene."""

import random

from matplotlib import cm
from rgbmatrix import graphics

from rgbinfopanel import helpers, colors


MAX_TICKS = 10000
GOOFY_EXCLAMATIONS = ['OW', 'HI', 'YUM', 'WOO', 'YES', 'CRAP', 'DANG', 'WHOOPS',
                      'YIKES', 'BYE', 'DAMN', 'SHIT', 'LOOK', 'NAY', 'YAWN', 'WHAT',
                      'WHY', 'GO', 'SAD', 'YAY', 'NUTS', 'NO', 'WOW', 'OOH', 'BOO',
                      'BRAVO', 'CHEERS', 'G\'DAY', 'NICE', 'WEE', 'TATA', 'DUH',
                      'DERP', 'MERP', 'YAH', 'HEY', 'HO', 'BOOP', 'HMM', 'YAYA', 'SUP',
                      'BOP']


class Sprite(object):  # pylint: disable=too-many-instance-attributes
    """A thing that may be animated or not, and may move or not."""

    frames = [[[]]]

    def __init__(self, x=0, y=0):
        self.x, self.y = x, y
        self.canvas = None
        self._frame_num = 0
        self._ticks = 0  # to allow slower changes of frames, could probably be itertools.cycle
        self.ticks_per_frame = 1
        self.ticks_per_movement = 1
        self.ticks_per_phrase = 200
        self.min_ticks_per_phrase = 100
        self.max_ticks_per_phrase = 400
        self.pallete = {1: (255, 255, 255)}
        self.dx, self.dy = 0, 0
        self.font = helpers.load_font('5x8.bdf')
        self.text = ''
        self.phrases = ['']

    def flip_horizontal(self):
        """Flip the sprite horizontally."""
        flipped = []
        for frame in self.frames:
            flipped_frame = []
            for row in frame:
                flipped_row = row[:]
                flipped_row.reverse()
                flipped_frame.append(flipped_row)
            flipped.append(flipped_frame)
        self.frames = flipped

    @property
    def width(self):
        """Width of the sprite."""
        return len(self.frames[0][0])

    @property
    def height(self):
        """Height of the sprite."""
        return len(self.frames[0])

    @property
    def frame(self):
        """Get the current frame, and advance the ticks."""
        pixels = self.frames[self._frame_num]
        self._ticks += 1
        self.update_frame_num()
        self.check_movement()
        self.check_tick_bounds()
        self.check_frame_bounds()
        self.update_phrase()
        return pixels

    def update_frame_num(self):
        """Change frame num when there have been enough ticks."""
        if not self._ticks % self.ticks_per_frame:
            self._frame_num += 1

    def check_movement(self):
        """Move if there have been enough ticks, and wrap."""
        if not self.dx and not self.dy:
            return

        if not self._ticks % self.ticks_per_movement:
            self.move()

        if self.x > self.canvas.width and self.dx > 0:
            if not self._maybe_flip():
                self.x = 0 - self.width
        elif self.x + self.width < 0 and self.dx < 0:
            if not self._maybe_flip():
                self.x = self.canvas.width

        if self.y > self.canvas.height and self.dy > 0:
            self.y = 0
        elif self.y + self.height < 0 and self.dy < 0:
            self.y = self.canvas.height

    def _maybe_flip(self):
        multiplier = random.choice([1, -1])
        self.dx *= multiplier
        if multiplier == -1:
            self.flip_horizontal()
            return True
        return False

    def check_tick_bounds(self):
        """
        Reset ticks when it reaches some high bound.

        This allows you to not have individual counters for everything.
        """
        if self._ticks > MAX_TICKS:
            self._ticks = 0

    def check_frame_bounds(self):
        """Roll back to first frame if all have been seen."""
        if self._frame_num >= len(self.frames):
            self._frame_num = 0

    def update_phrase(self):
        """Change the phrase the thing is saying."""
        if not self._ticks % self.ticks_per_phrase:
            text_src = random.choice(self.phrases)
            min_ticks = self.min_ticks_per_phrase
            if callable(text_src):
                # allow callable helpers for current date, time, etc.
                text_src = text_src()
                min_ticks *= 2
            elif isinstance(self.text, Sprite):
                # allow nested sprites to be passed to get extra-fancy (traffic)
                min_ticks *= 2  # let live data stay a bit longer

            self.text = text_src
            self.ticks_per_phrase = random.randint(min_ticks, self.max_ticks_per_phrase)

    def move(self):
        """Move around on the screen."""
        self.x += self.dx
        self.y += self.dy


    def render(self, canvas):
        """Render a frame and advance."""
        self.canvas = canvas  # keep up to date with double-buffered frame or risk flickering.
        # local variables for speed deep in the loop
        x = self.x
        pallete = self.pallete

        for yi, row in enumerate(self.frame):
            y = self.y + yi
            for xi, val in enumerate(row):
                if val:
                    red, green, blue = pallete[val]
                    canvas.SetPixel(x + xi, y, red, green, blue)
        # you could try to make text a FancyText object but then you have to double-
        # render all the motion an wrapping. It's too slow so this is just dumb text.
        if self.text:
            xtext = x + self.width + 1
            ytext = self.y + self.font.height
            if isinstance(self.text, Sprite):
                self.text.x = xtext
                self.text.y = ytext
                self.text.render(canvas)
            else:
                graphics.DrawText(canvas, self.font, xtext, ytext,
                                  colors.GREEN, self.text)


class FancyText(Sprite):
    """Text with multiple colors and stuff that can move."""

    def __init__(self, x=0, y=0, text=None):
        Sprite.__init__(self, x, y)
        self.frames = [[[]]]
        self._text = []
        if text:
            self.add(text, colors.GREEN)
        self._width = 0

    @property
    def width(self):
        return self._width

    def flip_horizontal(self):
        Sprite.flip_horizontal(self)

    @property
    def height(self):
        return self.font.height

    def add(self, text, color):
        """Add a section of text with a constant color."""
        self._text.append((text, color))

    def clear(self):
        """Remove all text."""
        self._text = []

    def render(self, canvas):
        """
        Render fancy text to screen.

        Can have lines that end with newline, and can have multiple colors.
        """
        self.canvas = canvas
        x = 0
        dummy = self.frame  # to tick the ticks.
        for text, color in self._text:
            if callable(text):
                text = str(text())  # for dynamic values
            x += graphics.DrawText(canvas, self.font, self.x + x, self.y, color, text)
        self._width = x

class Duration(FancyText):
    """Text that represents a duration with a green-to-red color."""

    def __init__(self, x=0, y=0, text=None):
        FancyText.__init__(self, x, y, text)
        self.last_val = None
        self.color = None
        self.low_val = 13.0
        self.high_val = 23.0
        self.value = None
        self.cmap = colors.GREEN_RED
        self.label_fmt = '{}:'
        self.val_fmt = '{}'

    def add(self, label, value):
        FancyText.add(self, self.label_fmt.format(label), colors.YELLOW)
        val = value() if callable(value) else value
        color = colors.interpolate_color(val, self.low_val, self.high_val, self.cmap)
        self.last_val = val
        self.basis = (label, value)
        self.value = value
        FancyText.add(self, self.val_fmt.format(val), color)

    def update_color(self):
        """Update the interpolated color if value changed."""
        val = self.value() if callable(self.value) else self.value  # pylint: disable=not-callable
        if val != self.last_val:
            # only do lookup when things change for speed.
            self.clear()
            self.add(*self.basis)

    def render(self, canvas):
        self.update_color()
        FancyText.render(self, canvas)

class Temperature(Duration):
    def __init__(self, x=0, y=0, text=None):
        Duration.__init__(self, x, y, text)
        self.low_val = -15
        self.high_val = 28.0
        self.cmap = cm.jet
        self.label_fmt = '{}'
        self.val_fmt = '{:> .1f}'


class Giraffe(Sprite):
    """An animated Giraffe."""

    def __init__(self):
        Sprite.__init__(self)
        self.ticks_per_frame = 3
        self.pallete = {1: (255, 255, 0)}
        self.dx = 1
        self.phrases = [''] * 6 + GOOFY_EXCLAMATIONS + [helpers.day_of_week,
                                                        helpers.time_now,
                                                        helpers.date]

        self.frames = [[[0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 1],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 1, 1, 0],
                        [0, 1, 1, 1, 0],
                        [1, 1, 1, 1, 0],
                        [1, 0, 0, 1, 0],
                        [1, 0, 0, 0, 1],
                        [1, 0, 0, 0, 1]],

                       [[0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 1],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 0, 1, 1, 0],
                        [0, 1, 1, 1, 0],
                        [1, 1, 1, 1, 0],
                        [1, 0, 0, 1, 0],
                        [1, 0, 0, 1, 0],
                        [0, 1, 1, 0, 0]]]


class Plant(Sprite):
    """A tropical plant."""
    def __init__(self, x=0, y=0):
        Sprite.__init__(self, x, y)
        self.frames = [[[0, 1, 1, 1, 1, 0],
                        [1, 0, 0, 1, 0, 1],
                        [1, 0, 2, 0, 0, 1],
                        [0, 0, 2, 0, 0, 0],
                        [0, 0, 2, 2, 0, 0],
                        [0, 0, 2, 2, 0, 0]],

                       [[1, 1, 1, 1, 1, 0],
                        [1, 0, 0, 1, 0, 1],
                        [0, 0, 0, 2, 1, 0],
                        [0, 0, 0, 2, 0, 0],
                        [0, 0, 2, 2, 0, 0],
                        [0, 0, 2, 2, 0, 0]]]

        self.ticks_per_frame = random.randint(10, 20)
        self.pallete = {1: (0, 240, 0),
                        2: (165, 42, 42)}
