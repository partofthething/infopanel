"""Scenes. One of these will be active at any given time."""

import time
import inspect
import sys
import copy
import logging
import datetime

from infopanel import sprites, helpers

LOG = logging.getLogger(__name__)
SCENE_BLANK = 'blank'


class Scene:
    """A single screen's worth of sprites."""

    def __init__(self, width, height):
        """Construct a scene."""
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

    def reinit(self):
        """Reinitialize when scene comes back up on the screen."""
        for sprite in self.sprites:
            sprite.reinit()


class Blank(Scene):
    """Just a blank screen."""

    def draw_frame(self, display):
        """Draw a blank frame."""
        time.sleep(1.0)


class Welcome(Scene):
    """Just a welcome message."""

    def __init__(self, width, height):
        """Construct a scene."""
        Scene.__init__(self, width, height)
        self.font = helpers.load_font('9x15B.bdf')

    def draw_frame(self, display):
        """Draw the welcome frame."""
        display.rainbow_text(self.font, 5, 20, 'HELLO!')


class Time(Scene):
    """Basic clock."""

    def __init__(self, width, height):
        """Construct a scene."""
        Scene.__init__(self, width, height)
        self.font = helpers.load_font('9x15B.bdf')

    def draw_frame(self, display):
        """Draw the current time."""
        now = datetime.datetime.now()
        display.rainbow_text(self.font, 5, 20, now.strftime('%I:%M %p'))


class Giraffes(Scene):
    """A field of giraffes saying things."""

    def __init__(self, width, height, extra_phrases=None, extra_phrase_frequency=None):
        """Construct a scene."""
        Scene.__init__(self, width, height)
        self._extra_phrases = extra_phrases or []
        self._extra_phrase_frequency = extra_phrase_frequency or 1
        self.sprites = [sprites.Giraffe(width, height) for _i in range(3)]
        self.sprites[1].flip_horizontal()
        self.sprites[1].dx = -1
        self.sprites[1].y = 18
        self.sprites[2].ticks_per_movement = 2
        self.sprites[2].y = 10
        for (x, y) in [(30, 10), (10, 20), (40, 5)]:
            plant = sprites.Plant(width, height)
            plant.x, plant.y = x, y
            self.sprites.append(plant)
        for sprite in self.sprites:
            sprite.apply_config({})  # set defaults on everything else.

    def apply_config(self, conf, existing_sprites):
        """Apply Giraffe-specific configuration entries."""
        for sprite in self.sprites:
            if isinstance(sprite, sprites.Giraffe):
                for extra_phrase in self._extra_phrases:
                    phrase_sprite = existing_sprites[extra_phrase][0]
                    sprite.phrases.extend(
                        [phrase_sprite] * self._extra_phrase_frequency)


def scene_factory(width, height, conf, existing_sprites):  # pylint: disable=too-many-locals
    """Build scenes from config."""
    scenes = {SCENE_BLANK: Blank(width, height)}  # alway add blank scene for suspend
    cls = None
    for name, scene_data in conf.items():  # pylint: disable=too-many-nested-blocks
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
        LOG.debug('Initializing %s', cls)
        scene = cls(width, height, **scene_data)
        for sprite_data in sprites_to_add:
            for spritename, spriteparams in sprite_data.items():  # should be only one
                # each active_scene gets independent copies of the sprites because scenes
                # can set different custom config for each sprite (location,
                # direction, color...)
                sprite = copy.copy(existing_sprites[spritename][0])
                existing_sprites[spritename].append(
                    sprite)  # track the copies by name
                if spriteparams is not None:
                    for param, val in spriteparams.items():
                        if not hasattr(sprite, param):
                            raise ValueError('Invalid sprite parameter for {}: {}'
                                             ''.format(sprite, param))
                        setattr(sprite, param, val)
            scene.sprites.append(sprite)

        scene.apply_config(conf, existing_sprites)

        scenes[name] = scene
    return scenes
