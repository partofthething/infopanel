"""Configuration file stuff."""

import inspect

import yaml
import voluptuous as vol

from infopanel import sprites, scenes

SPRITE_NAMES = [name for name,
                value in inspect.getmembers(sprites, inspect.isclass)]

MQTT = vol.Schema({'broker': str,
                   vol.Optional('port', default=1883): int,
                   'client_id': str,
                   vol.Optional('keepalive', default=60): int,
                   vol.Optional('username'): str,
                   vol.Optional('password'): str,
                   vol.Optional('certificate'): str,
                   vol.Optional('protocol', default='3.1'): vol.Coerce(str),
                   'topic': str})

SPRITE = vol.Schema({'type': vol.Any(*SPRITE_NAMES)},
                    extra=vol.ALLOW_EXTRA)
SPRITES = vol.Schema({str: SPRITE})

SCENE_NAMES = [name for name,
               value in inspect.getmembers(scenes, inspect.isclass)]
# sprite list in scenes is a list because you may want multiple of one
# sprite in a scene.
SCENES = vol.Schema({str: {vol.Optional('type', default='Scene'): vol.Any(*SCENE_NAMES),
                           vol.Optional('path'): str,
                           vol.Optional('sprites'): list}}, extra=vol.ALLOW_EXTRA)

MODES = vol.Schema({str: list})

RGBMATRIX = vol.Schema({'led-rows': int,
                        'led-chain': int,
                        'led-parallel': int,
                        'led-pwm-bits': vol.All(int, vol.Range(min=1, max=11)),
                        'led-brightness': vol.All(int, vol.Range(min=1, max=100)),
                        'led-gpio-mapping': vol.Any('adafruit-hat-pwm', 'adafruit-hat', 'regular'),
                        'led-scan-mode': vol.All(int, vol.Range(min=0, max=1)),
                        'led-pwm-lsb-nanoseconds': int,
                        'led-show-refresh': bool,
                        'led-slowdown-gpio': vol.All(int, vol.Range(min=0, max=2)),
                        'led-no-hardware-pulse': bool})

GLOBAL = vol.Schema({'font_dir': str,
                     'default_mode': str,
                     'random': bool})

SCHEMA = vol.Schema({'mqtt': MQTT,
                     'sprites': SPRITES,
                     'scenes': SCENES,
                     'modes': MODES,
                     vol.Optional('RGBMatrix'): RGBMATRIX,
                     vol.Optional('DummyMatrix'): None,
                     'global': GLOBAL})


def load_config_yaml(path):
    """Load and validate config file as an alternative to command line options."""
    with open(path) as configfile:
        config = yaml.load(configfile)
    config = SCHEMA(config)

    return config
