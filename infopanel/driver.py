"""The infopanel driver. This is the main controller for the system."""

import threading
import argparse
import time
import random
import logging
import os
import itertools

from infopanel import mqtt, scenes, config, display, sprites, data

FRAME_DELAY_S = 0.005
MODE_BLANK = 'blank'
MODE_ALL = 'all'
MODE_ALL_DURATION = 5  # 5 second default scene duration.
ON = '1'  # for MQTT processing
OFF = '0'

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Driver(object):  # pylint: disable=too-many-instance-attributes
    """Main controller for the infopanel."""

    def __init__(self, disp, data_source):
        """Construct infopanel driver."""
        LOG.info('Starting InfoPanel.')
        self.display = disp
        self.data_source = data_source
        self.sprites = {}  # name: list of sprites
        self.scenes = {}  # name: scene
        self.durations_in_s = {}  # scene: seconds
        self.brightnesses = {}  # scene: brightness percent
        self.scene_sequence = []
        self._scene_iterator = itertools.cycle(self.scene_sequence)
        self._randomize_scenes = ON
        self._previous_mode = None
        self._mode = MODE_ALL
        self.modes = {}
        self.active_scene = None
        self._stop = threading.Event()
        self.interval = 2
        # just used to detect changes in data. Should be handled on data.
        self._brightness = 100

    def run(self):
        """
        Draw frames forever or until the main thread stops us.

        Notes
        -----
        Uses the clock to figure out when to switch scenes instead of the number of frames
        because some scenes are way slower than others.

        """
        interval_start = time.time()
        while True:
            if self._stop.isSet():
                break
            self.draw_frame()
            time.sleep(FRAME_DELAY_S)
            now = time.time()
            if now - interval_start > self.interval:
                interval_start = now
                self._change_scene()

    def stop(self):
        """Shut down the thread."""
        self._stop.set()

    def _change_scene(self):
        """Switch to another active_scene, maybe."""
        self._check_for_command()
        if self._randomize_scenes == ON:
            new_scene = random.choice(self.scene_sequence)
        else:
            new_scene = next(self._scene_iterator)

        if new_scene != self.active_scene:
            LOG.debug('Switching to new scene: %s', new_scene)
            self.display.clear()
            new_scene.reinit()
            brightness = self.brightnesses.get(new_scene)
            if brightness is not None:
                # allow brightness changes on scene change
                # None value indicates no change.
                self.display.brightness = brightness
            self.active_scene = new_scene
            self.interval = self.durations_in_s[new_scene]

    def _check_for_command(self):
        """Process any incoming commands."""
        if self.data_source['mode'] != self._mode:
            success = self.apply_mode(self.data_source['mode'])
            if not success:
                # Invalid mode. Reset data source to avoid dead-locking.
                self.data_source['mode'] = self._mode

        if self.data_source['brightness'] != self._brightness:
            try:
                self._brightness = int(self.data_source['brightness'])
            except TypeError:
                self._brightness = 100
            self.display.brightness = self._brightness

        if self.data_source['random'] != self._randomize_scenes:
            self._randomize_scenes = self.data_source['random']

        if self.data_source['image_path']:
            self.change_image_path(self.data_source['image_path'])
            # clear it out in anticipation of next command.
            self.data_source['image_path'] = ''

    def apply_mode(self, mode):
        """
        Apply a different sequence of scenes with different durations.

        If the mode is the name of a scene, set that scene instead.
        """
        LOG.info('Applying mode: %s', mode)
        if mode not in self.modes:
            if mode in self.scenes:
                # allow mode names to be any scene name to get just that mode.
                scene = self.scenes[mode]
                self.scene_sequence = [scene]
                self.durations_in_s[scene] = MODE_ALL_DURATION
            else:
                LOG.error('Invalid mode: %s', mode)
                return False
        else:
            self.scene_sequence = []
            for scene_name, duration, brightness in self.modes[mode]:
                scene = self.scenes[scene_name]
                self.scene_sequence.append(scene)
                self.durations_in_s[scene] = duration
                self.brightnesses[scene] = brightness
        self._scene_iterator = itertools.cycle(self.scene_sequence)
        self._previous_mode = self._mode  # for suspend/resume
        self._mode = mode
        return True

    def change_image_path(self, pathsetting):
        """
        Change the image path.

        The pathsetting is a special string in the form: spritename=newpath.
        """
        try:
            sprite_name, new_path = pathsetting.split('=')
        except ValueError:
            LOG.error(
                'Path change string %s invalid. Format: spritename=newpath', pathsetting)
            return
        sprites_of_name = self.sprites.get(sprite_name)
        LOG.debug('Setting %s path to %s', sprite_name, new_path)
        if not sprites_of_name:
            LOG.warning('No sprite named %s to modify.', sprite_name)
            return
        try:
            for sprite in sprites_of_name:
                sprite.set_source_path(new_path)
        except AttributeError:
            LOG.warning(
                'The %s sprite cannot have its path modified.', sprite_name)

    def draw_frame(self):
        """Perform a double-buffered draw frame and frame switch."""
        self.display.clear()
        self.active_scene.draw_frame(self.display)
        self.display.buffer()

    def init_modes(self, conf):
        """Process modes from configuration."""
        modeconf = conf['modes']
        # blank mode for suspend. Use None brightness to keep constant
        self.modes[MODE_BLANK] = [(scenes.SCENE_BLANK, 2.0, None)]

        for mode_name, scenelist in modeconf.items():
            self.modes[mode_name] = []
            for sceneinfo in scenelist:
                for scene_name, scene_settings in sceneinfo.items():
                    self.modes[mode_name].append(
                        (scene_name,
                         scene_settings['duration'],
                         scene_settings.get('brightness')
                        )
                    )

        self.modes[MODE_ALL] = []  # make a default catch-all mode.
        for scene_name in self.scenes:
            if scene_name in [scenes.SCENE_BLANK]:
                # do not randomly cycle through the special blank scene.
                continue
            self.modes[MODE_ALL].append((scene_name, MODE_ALL_DURATION, self._brightness))

        default_mode = conf['global'].get('default_mode', MODE_ALL)
        self.apply_mode(default_mode)
        self.data_source['mode'] = default_mode
        self._change_scene()


def driver_factory(disp, data_src, conf):
    """Build factory and add scenes and sprites."""
    driver = Driver(disp, data_src)
    driver.sprites = sprites.sprite_factory(conf['sprites'], data_src, disp)
    driver.scenes = scenes.scene_factory(disp.width, disp.height,
                                         conf['scenes'], driver.sprites)
    driver.init_modes(conf)
    return driver


def apply_global_config(conf):
    """Apply config items that are global in nature."""
    from infopanel import helpers
    helpers.FONT_DIR = os.path.expandvars(conf['global']['font_dir'])


def run(conf_file=None):
    """Run the screen."""
    if not conf_file:
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", action="store", help="Point to a YAML configuration file.",
                            default='/etc/infopanel/infopanel.yaml')

        args = parser.parse_args()
        conf_file = args.config
    conf = config.load_config_yaml(conf_file)
    apply_global_config(conf)
    disp = display.display_factory(conf)
    datasrc = data.InputData()
    infopanel = driver_factory(disp, datasrc, conf)

    if conf.get('mqtt'):
        client = mqtt.MQTTClient(datasrc, conf['mqtt'])
        client.start()
    else:
        client = None
    try:
        # infopanel.start()  # multiple threads
        infopanel.run()  # main thread
    finally:
        if client:
            client.stop()
        LOG.info('Quitting.')


if __name__ == "__main__":
    run()
