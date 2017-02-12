"""Scenes. One of these will be active at any given time."""

import itertools
import time
import inspect
import sys
import copy
import logging
import os

from PIL import Image as PILImage
from PIL import ImageSequence

from infopanel import sprites, helpers


LOG = logging.getLogger(__name__)

class Scene(object):
    """A single screen's worth of sprites."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.sprites = []

    def draw_frame(self, display):
        """Render all sprites in this scene to display."""
        for sprite in self.sprites:
            sprite.render(display)

    def apply_config(self, conf, existing_sprites):
        """Apply optional extra config."""
        pass

class Blank(Scene):
    """Just a blank screen."""
    def draw_frame(self, display):
        time.sleep(1.0)

class Image(Scene):
    """Full screen bitmap image."""
    def __init__(self, width, height, path):
        Scene.__init__(self, width, height)
        with PILImage.open(os.path.expandvars(path)) as image:
            image.thumbnail((self.width, self.height), PILImage.ANTIALIAS)
            self.image = image.convert('RGB')

    def draw_frame(self, display):
        display.set_image(self.image)


class AnimatedGif(Scene):
    """Full screen animated gif."""
    def __init__(self, width, height, path):
        Scene.__init__(self, width, height)
        self.image = PILImage.open(os.path.expandvars(path))

        frames = [frame.copy() for frame in ImageSequence.Iterator(self.image)]
        for frame in frames:
            frame.thumbnail((self.width, self.height), PILImage.ANTIALIAS)
        self.frames = itertools.cycle([frame.convert('RGB') for frame in frames])
        self.delay = 0.05

    def draw_frame(self, display):
        display.set_image(next(self.frames))
        time.sleep(self.delay)


class Welcome(Scene):
    """Just a welcome message."""
    def __init__(self, width, height):
        Scene.__init__(self, width, height)
        self.font = helpers.load_font('9x15B.bdf')

    def draw_frame(self, display):
        display.rainbow_text(self.font, 5, 20, 'HELLO!')


class Giraffes(Scene):
    """A field of giraffes saying things."""

    def __init__(self, width, height, extra_phrases, extra_phrase_frequency):
        Scene.__init__(self, width, height)
        self._extra_phrases = extra_phrases
        self._extra_phrase_frequency = extra_phrase_frequency
        self.sprites = [sprites.Giraffe() for _i in range(3)]
        self.sprites[1].flip_horizontal()
        self.sprites[1].dx = -1
        self.sprites[1].y = 18
        self.sprites[2].ticks_per_movement = 2
        self.sprites[2].y = 10
        for (x, y) in [(30, 10), (10, 20), (40, 5)]:
            plant = sprites.Plant()
            plant.x, plant.y = x, y
            self.sprites.append(plant)
        for sprite in self.sprites:
            sprite.apply_config({})  # set defaults on everything else.

    def apply_config(self, conf, existing_sprites):
        """Apply Giraffe-specific configuration entries."""
        for sprite in self.sprites:
            if isinstance(sprite, sprites.Giraffe):
                for extra_phrase in self._extra_phrases:
                    phrase_sprite = existing_sprites[extra_phrase]
                    sprite.phrases.extend([phrase_sprite] * self._extra_phrase_frequency)



def scene_factory(width, height, conf, existing_sprites):  # pylint: disable=too-many-locals
    """Build scenes from config."""
    scenes = {}
    cls = None
    for name, scene_data in conf.items():
        for cls_name, cls in inspect.getmembers(sys.modules[__name__]):
            if scene_data['type'] == cls_name:
                break
        else:
            raise ValueError('{} is invalid active_scene'.format(name))
        del scene_data['type']
        if 'sprites' in scene_data:
            sprites_to_add = scene_data.pop('sprites')
        else:
            sprites_to_add = []
        scene = cls(width, height, **scene_data)
        for sprite_data in sprites_to_add:
            for spritename, spriteparams in sprite_data.items():  # should be only one
                # each active_scene gets independent copies of the sprites
                sprite = copy.copy(existing_sprites[spritename])
                for param, val in spriteparams.items():
                    if not hasattr(sprite, param):
                        raise ValueError('Invalid sprite parameter for {}: {}'
                                         ''.format(sprite, param))
                    setattr(sprite, param, val)
            scene.sprites.append(sprite)

        for sprite in scene.sprites:
            sprite.max_x = width
            sprite.max_y = height

        scene.apply_config(conf, existing_sprites)

        scenes[name] = scene
    return scenes
