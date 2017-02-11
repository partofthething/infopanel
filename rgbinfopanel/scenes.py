"""Scenes. One of these will be active at any given time."""

import itertools
import time
import inspect
import sys
import copy

import PIL

from rgbinfopanel import sprites, helpers


class Scene(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.sprites = []

    def draw_frame(self, display):
        for sprite in self.sprites:
            sprite.render(display)

class Blank(Scene):
    """Just a blank screen."""
    def draw_frame(self, display):
        time.sleep(1.0)

class Image(Scene):
    """Full screen bitmap image."""
    def __init__(self, width, height, path):
        Scene.__init__(self, width, height)
        self.image = PIL.Image.open(path)
        self.image.thumbnail((self.width, self.height), PIL.Image.ANTIALIAS)
        self.image = self.image.convert('RGB')

    def draw_frame(self, display):
        display.set_image(self.image)


class AnimatedGif(Scene):
    """Full screen animated gif."""
    def __init__(self, width, height, path):
        Scene.__init__(self, width, height)
        self.image = PIL.Image.open(path)

        frames = [frame.copy() for frame in PIL.ImageSequence.Iterator(self.image)]
        [frame.thumbnail((self.width, self.height),
                         PIL.Image.ANTIALIAS) for frame in frames]
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
    def __init__(self, width, height):
        Scene.__init__(self, width, height)
        self.sprites = [sprites.Giraffe() for _i in range(3)]
        self.sprites[1].flip_horizontal()
        self.sprites[1].dx = -1
        self.sprites[1].y = 18
        self.sprites[2].ticks_per_movement = 2
        self.sprites[2].y = 10
#         for giraffe in self.sprites:
#             giraffe.phrases.extend(3 * self.sprites)
        self.sprites.extend([sprites.Plant(x, y) for (x, y) in [(30, 10), (10, 20), (40, 5)]])

def scene_factory(width, height, conf, sprites):
    """Build scenes from config."""
    scenes = {}
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
                sprite = copy.copy(sprites[spritename])  # each active_scene gets independent copies of the sprites
                for param, val in spriteparams.items():
                    if not hasattr(sprite, param):
                        raise ValueError('Invalid sprite parameter for {}: {}'.format(sprite, param))
                    setattr(sprite, param, val)
            scene.sprites.append(sprite)

        for sprite in scene.sprites:
            sprite.max_x = width
            sprite.max_y = height

        scenes[name] = scene
    return scenes

