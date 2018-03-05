"""There are multiple sprites in any given scene."""

import random
import inspect
import sys
import logging
import datetime
import os

from PIL import Image as PILImage
from PIL import ImageSequence

from matplotlib import cm
import voluptuous as vol

from infopanel import helpers, colors, data


MAX_TICKS = 10000
GOOFY_EXCLAMATIONS = ['OW', 'HI', 'YUM', 'WOO', 'YES', 'CRAP', 'DANG', 'WHOOPS',
                      'YIKES', 'BYE', 'DAMN', 'SHIT', 'LOOK', 'NAY', 'YAWN', 'WHAT',
                      'WHY', 'GO', 'SAD', 'YAY', 'NUTS', 'NO', 'WOW', 'OOH', 'BOO',
                      'BRAVO', 'CHEERS', 'G\'DAY', 'NICE', 'WEE', 'TATA', 'DUH',
                      'DERP', 'MERP', 'YAH', 'HEY', 'HO', 'BOOP', 'HMM', 'YAYA', 'SUP',
                      'BOP']
PALLETE_SCHEMA = vol.Schema({vol.Any(int, str): list})

FRAMES_SCHEMA = vol.Schema([str])
LOG = logging.getLogger(__name__)

class Sprite(object):  # pylint: disable=too-many-instance-attributes
    """A thing that may be animated or not, and may move or not."""

    CONF = vol.Schema({vol.Optional('dx', default=0): int,
                       vol.Optional('dy', default=0): int,
                       vol.Optional('ticks_per_frame', default=1): int,
                       vol.Optional('ticks_per_movement', default=1): int,
                       vol.Optional('ticks_per_phrase', default=200): int,
                       vol.Optional('min_ticks_per_phrase', default=100): int,
                       vol.Optional('max_ticks_per_phrase', default=400): int,
                       vol.Optional('x', default=0): int,
                       vol.Optional('y', default=0): int,
                       vol.Optional('font_name', default='5x8.bdf'): str,
                       vol.Optional('phrases', default=['']): list,
                       vol.Optional('pallete', default={1: [255, 255, 255],
                                                        'text':[0, 255, 0],
                                                        'label':[255, 255, 0]}): PALLETE_SCHEMA,
                       vol.Optional('frames', default=None): FRAMES_SCHEMA,
                       vol.Optional('text', default=''): str,
                       vol.Optional('can_flip', default=True): bool})

    def __init__(self, max_x, max_y, data_source=None):
        """Construct a sprite."""
        self.x, self.y = None, None
        self.max_x, self.max_y = max_x, max_y
        self._frame_num = 0
        self._ticks = 0  # to allow slower changes of frames, could probably be itertools.cycle
        self.ticks_per_frame = None
        self.ticks_per_movement = None
        self.ticks_per_phrase = None
        self.min_ticks_per_phrase = None
        self.max_ticks_per_phrase = None
        self.pallete = None
        self.dx, self.dy = None, None
        self.font = None
        self.text = None
        self.phrases = None
        if data_source is None:
            data_source = data.InputData()
        self.data_source = data_source
        self.frames = []
        self._frame_delta = 0
        self.can_flip = None
        self._phrase_width = 0

    def __repr__(self):
        """Print out details of a sprite."""
        return ('<{} at {}, {}. dx/dy: ({}, {}), size: ({}, {})>'
                ''.format(self.__class__.__name__, self.x, self.y,
                          self.dx, self.dy, self.max_x, self.max_y))

    def apply_config(self, conf):
        """
        Validate and apply configuration to this sprite.

        Generally, each config item becomes a instance attribute.
        """
        conf = self.CONF(conf)
        for key, val in conf.items():
            if not hasattr(self, key):
                # this isn't a configurable attribute. May have special behavior.
                continue
            if getattr(self, key) is None:
                # allow subclasses to force non-None attributes in their constructors
                setattr(self, key, val)
        self.font = helpers.load_font(conf['font_name'])
        if conf['frames']:
            self._build_frames(conf['frames'])

        return conf

    def _build_frames(self, frames):
        """Convert user-input custom frames into usable frames."""
        new_frames = []
        for framestr in frames:
            frame = []
            for intstr in framestr.split():
                row = []
                for char in intstr:
                    row.append(int(char))
                frame.append(row)
            new_frames.append(frame)
        LOG.info('Built custom frames for %s.', self)
        self.frames = new_frames

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
        return len(self.frame[0])

    @property
    def height(self):
        """Height of the sprite."""
        return len(self.frame)

    @property
    def frame(self):
        """Get the current frame."""
        return self.frames[self._frame_num]

    def tick(self):
        """Update the animation ticks."""
        self._ticks += 1
        self.update_frame_num()
        self.check_movement()
        self.check_tick_bounds()
        self.check_frame_bounds()
        self.update_phrase()

    def update_frame_num(self):
        """Change frame num when there have been enough ticks."""
        if not self._ticks % self.ticks_per_frame:
            self._frame_num += self._frame_delta

    def check_movement(self):
        """Move if there have been enough ticks, and wrap."""
        if not self.dx and not self.dy:
            return

        if not self._ticks % self.ticks_per_movement:
            self.move()

        if self.x > self.max_x and self.dx > 0:
            if not self._maybe_flip():
                self.x = 0 - self.width - self._phrase_width
        elif self.x + self.width + self._phrase_width < 0 and self.dx < 0:
            if not self._maybe_flip():
                self.x = self.max_x

        if self.y - self.height > self.max_y and self.dy > 0:
            self.y = 0 - self.height
        elif self.y + self.height < 0 and self.dy < 0:
            self.y = self.max_y

    def _maybe_flip(self):
        if not self.can_flip:
            return False
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
        """Reverse back to first frame if all have been seen."""
        if len(self.frames) == 1:
            self._frame_delta = 0
        elif self._frame_num == len(self.frames) - 1:
            self._frame_delta = -1
        elif self._frame_num == 0:
            self._frame_delta = 1

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

    def render(self, display):
        """Render a frame and advance."""
        self._render_frame(display)
        self._render_phrase(display)
        self.tick()

    def _render_frame(self, display):
        """Render main part of the sprite."""
        # local variables for speed deep in the loop
        x = self.x
        pallete = self.pallete
        for yi, row in enumerate(self.frame):
            y = self.y + yi
            for xi, val in enumerate(row):
                if val:
                    red, green, blue = pallete[val]  # pylint: disable=unsubscriptable-object
                    display.set_pixel(x + xi, y, red, green, blue)

    def _render_phrase(self, display):
        """Render optional follower phrase."""
        # you could try to make text a FancyText object but then you have to double-
        # render all the motion an wrapping. It's too slow so this is just dumb text.
        if self.text:
            xtext = self.x + self.width + 1
            ytext = self.y + self.font.height
            if isinstance(self.text, Sprite):
                self.text.x = xtext
                self.text.y = ytext
                self._phrase_width = self.text.render(display)  # pylint:disable=no-member
            else:
                red, green, blue = self.pallete['text']  # pylint: disable=unsubscriptable-object
                self._phrase_width = display.text(self.font, xtext, ytext,
                                                  red, green, blue, self.text)

    def reinit(self):
        """
        Perform actions when the sprite gets put back on the screen.

        You could reset position or whatever here.
        """
        pass


class FancyText(Sprite):
    """Text with multiple colors and stuff that can move."""

    def __init__(self, max_x, max_y, data_source=None):
        """Construct a FancyText."""
        Sprite.__init__(self, max_x, max_y, data_source=data_source)
        self.frames = [[[]]]
        self._text = []
        self._width = 0

    def check_frame_bounds(self):
        """No frames, no frame delta. ."""
        self._frame_delta = 0

    def apply_config(self, conf):
        """Validate and apply configuration to this sprite."""
        conf = Sprite.apply_config(self, conf)
        if self.text:
            self.add(self.text, self.pallete['text'])  # pylint: disable=unsubscriptable-object
        return conf

    @property
    def width(self):
        """Width of the sprite."""
        return self._width

    def flip_horizontal(self):
        """Flip the sprite horizontally."""
        Sprite.flip_horizontal(self)

    @property
    def height(self):
        """Height of the sprite."""
        return self.font.height

    def add(self, text, color):
        """
        Add a section of text with a constant color.

        Color should be a r,g,b tuple.
        """
        self._text.append((text, color))

    def clear(self):
        """Remove all text."""
        self._text = []

    def render(self, display):
        """
        Render fancy text to screen.

        Can have lines that end with newline, and can have multiple colors.
        """
        x = 0
        self.tick()
        for text, rgb in self._text:
            if callable(text):
                text = str(text())  # for dynamic values
            r, g, b = rgb
            x += display.text(self.font, self.x + x, self.y, r, g, b, text)
        self._width = x
        return x

class Duration(FancyText):  # pylint:disable=too-many-instance-attributes
    """Text that represents a duration with a green-to-red color."""

    CONF = FancyText.CONF.extend({'label': vol.Coerce(str),
                                  vol.Optional('low_val', default=13.0):vol.Coerce(float),
                                  vol.Optional('high_val', default=23.0): vol.Coerce(float),
                                  vol.Optional('data_label'): vol.Coerce(str),
                                  vol.Optional('label_fmt', default='{}:'): str,
                                  vol.Optional('val_fmt', default='{}'): str})

    def __init__(self, max_x, max_y, data_source):
        """Construct a sprite."""
        FancyText.__init__(self, max_x, max_y, data_source=data_source)
        self.last_val = None
        self.color = None
        self.low_val = None
        self.high_val = None
        self.label = None
        self.value = None
        self.label_fmt = None
        self.val_fmt = None
        self.data_label = None
        self.cmap = colors.GREEN_RED

    def apply_config(self, conf):
        """Validate and apply configuration to this sprite."""
        conf = FancyText.apply_config(self, conf)
        if conf['data_label']:
            # make function to get live data off of object
            self.value = lambda: self._convert_data(self.data_source[conf['data_label']])
        self._make_text()
        return conf

    def _convert_data(self, val):  # pylint: disable=no-self-use
        try:
            return int(val)
        except ValueError:
            return None

    def _make_text(self):
        """Make elements of a duration with label and text."""
        FancyText.add(self, self.label_fmt.format(self.label), colors.rgb_from_name('yellow'))
        val = self.value() if callable(self.value) else self.value  # pylint: disable=not-callable
        if val is None:
            color = colors.interpolate_color(self.low_val, self.low_val, self.high_val, self.cmap)
            text = 'N/A'
        else:
            color = colors.interpolate_color(val, self.low_val, self.high_val, self.cmap)
            text = self.val_fmt.format(val)
        self.last_val = val
        FancyText.add(self, text, color)

    def update_color(self):
        """Update the interpolated color if value changed."""
        val = self.value() if callable(self.value) else self.value  # pylint: disable=not-callable
        if val != self.last_val:
            # only do lookup when things change for speed.
            self.clear()
            self._make_text()

    def render(self, display):
        """Render a frame and advance."""
        self.update_color()
        return FancyText.render(self, display)

class Temperature(Duration):
    """A temperature with color dependent on a high and low bound."""

    # updating defaults in a schema is broken in voluptuous 0.9.3 but fixed in master.
    # for now you will have to enter the lows and highs manually.
    # low_val with two different defaults gets treated as two keys and config value gets destroyed.
#     CONF = Duration.CONF.extend({vol.Optional('low_val', default=-15.0): vol.Coerce(float),
#                                  vol.Optional('high_val', default=28.0): vol.Coerce(float),
#                                  vol.Optional('label_fmt', default='{}'): str,
#                                  vol.Optional('val_fmt', default='{:> .1f}'): str
#                                  })

    def __init__(self, max_x, max_y, data_source=None):
        """Construct a sprite."""
        Duration.__init__(self, max_x, max_y, data_source)
        self.cmap = cm.jet  # pylint: disable=no-member
        self.label_fmt = '{}'  # until voluptuous bug fix is released
        self.val_fmt = '{:> .1f}'

    def _convert_data(self, val):
        try:
            return float(val)
        except ValueError:
            # can happen if data is 'unknown' or something.
            return None


class Giraffe(Sprite):
    """An animated Giraffe."""

    def __init__(self, max_x, max_y, data_source=None):
        """Construct a sprite."""
        Sprite.__init__(self, max_x, max_y, data_source)
        self.ticks_per_frame = 3
        self.pallete = {1: (255, 255, 0), 'text':[0, 255, 0]}
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

    def __init__(self, max_x, max_y, data_source=None):
        """Construct a sprite."""
        Sprite.__init__(self, max_x, max_y, data_source)
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

class BaseImage(Sprite):
    """Abstract image."""

    CONF = Sprite.CONF.extend({'path': vol.Coerce(str)})

    def apply_config(self, conf):
        """Validate and apply configuration to this sprite."""
        conf = Sprite.apply_config(self, conf)
        self.set_source_path(conf['path'])
        return conf

    def _render_frame(self, display):
        display.set_image(self.frame, self.x, self.y)

    def set_source_path(self, path):
        """Set this image source to a new path."""
        raise NotImplementedError

    def flip_horizontal(self):
        """Images can't flip... yet."""
        pass


class Image(BaseImage):
    """Bitmap image that doesn't animate."""

    def __init__(self, *args, **kwargs):
        """Construct a sprite."""
        BaseImage.__init__(self, *args, **kwargs)
        self._image = None

    def set_source_path(self, path):
        """Set this image source to a new path."""
        with PILImage.open(os.path.expandvars(path)) as image:
            image.thumbnail((self.max_x, self.max_y), PILImage.ANTIALIAS)
            self._image = image.convert('RGB')

    @property
    def frame(self):
        """Get the current frame."""
        return self._image

    @property
    def width(self):
        """Width of the sprite."""
        return self._image.size[0]

    @property
    def height(self):
        """Height of the sprite."""
        return self._image.size[1]


class AnimatedGif(BaseImage):
    """Animated gif sprite."""

    def set_source_path(self, path):
        """Set this image source to a new path."""
        image = PILImage.open(os.path.expandvars(path))
        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
        for frame in frames:
            frame.thumbnail((self.max_x, self.max_y), PILImage.ANTIALIAS)
        self.frames = [frame.convert('RGB') for frame in frames]
        self._frame_delta = 1

    def check_frame_bounds(self):
        """Roll back to first frame if all have been seen."""
        if self._frame_num == len(self.frames) - 1:
            self._frame_num = 0

    @property
    def width(self):
        """Width of the sprite."""
        width, _height = self.frame.size
        return width

    @property
    def height(self):
        """Height of the sprite."""
        _width, height = self.frame.size
        return height


class Reddit(FancyText):
    """The titles of some top posts in various subreddits."""

    CONF = FancyText.CONF.extend({'client_id': str,
                                  'client_secret': str,
                                  vol.Optional('user_agent', default='infopanel'): str,
                                  vol.Optional('subreddits',
                                               default=['worldnews', 'politics', 'news']):list,
                                  vol.Optional('num_headlines', default=5): int,
                                  vol.Optional('update_minutes', default=5): int})

    def __init__(self, *args, **kwargs):
        """Construct a sprite."""
        FancyText.__init__(self, *args, **kwargs)
        self._praw = None
        self.subreddits = None
        self.num_headlines = None
        self.update_minutes = None
        self._last_update_time = datetime.datetime.now()

    def apply_config(self, conf):
        """Validate and apply configuration to this sprite."""
        conf = FancyText.apply_config(self, conf)
        import praw
        self._praw = praw.Reddit(client_id=conf['client_id'],
                                 client_secret=conf['client_secret'],
                                 user_agent=conf['user_agent'])
        self.update_headlines()
        return conf

    def update_headlines(self):
        """Update sprite text based on current subreddit contents."""
        self.clear()
        try:
            headlines = self._praw.subreddit(
                '+'.join(self.subreddits)).hot(limit=self.num_headlines)
            for headline in headlines:
                self.add(headline.title + 10 * ' ', self.pallete['text'])  # pylint: disable=unsubscriptable-object
        except:  # pylint: disable=bare-except
            # possibly a connection error.
            self.add('Headlines N/A', self.pallete['text'])  # pylint: disable=unsubscriptable-object

    def update_phrase(self):
        """Occasionally update the headlines."""
        if not self._ticks % self.ticks_per_phrase:
            now = datetime.datetime.now()
            if now - self._last_update_time > datetime.timedelta(minutes=self.update_minutes):
                self.update_headlines()
                self._last_update_time = now

    def _maybe_flip(self):
        return False


def sprite_factory(config, data_source, disp):
    """Build sprites from config file."""
    sprites = {}
    for name, sprite_conf in config.items():
        for cls_name, cls in inspect.getmembers(sys.modules[__name__]):
            try:
                if sprite_conf['type'] == cls_name:
                    break
            except KeyError:
                LOG.error("%s", name)
                raise
        else:
            raise ValueError('{} is invalid sprite'.format(name))
        del sprite_conf['type']
        sprite = cls(disp.width, disp.height, data_source=data_source)  # pylint:disable=undefined-loop-variable
        sprite.apply_config(sprite_conf)
        sprites[name] = [sprite]  # track as list b/c copies will be added later and we track all.
        LOG.debug('Build %s', sprite)
    return sprites
