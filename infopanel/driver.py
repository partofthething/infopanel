"""The infopanel driver. This is the main controller for the system."""

import threading
import argparse
import time
import random
import logging
import os

from infopanel import mqtt, scenes, config, display, sprites, data

FRAME_DELAY_S = 0.005
BLANK = 'blank'

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Driver(object):  # pylint: disable=too-many-instance-attributes
    """Main controller for the infopanel."""
    def __init__(self, disp, data_source):
        LOG.info('Starting InfoPanel.')
        self.display = disp
        self.data_source = data_source
        self.sprites = {}  # name: sprite
        self.scenes = {}  # name: scene
        # separate blank so not in randomizer
        self._blank = scenes.Blank(self.display.width, self.display.height)
        self.durations_in_s = {self._blank: 2.0}  # scene: seconds
        self.scene_sequence = []

        self._mode = 'all'
        self.modes = {}
        self.active_scene = None
        self._stop = threading.Event()
        self.interval = 2
        self._brightness = 100  # just used to detect changes in data. Should be handeled on data.

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

    @property
    def suspended(self):
        """True if the system is in suspend mode."""
        return self.scene_sequence[0] is self._blank

    def _change_scene(self):
        """Switch to another active_scene, maybe."""
        self._check_for_command()
        new_scene = random.choice(self.scene_sequence)
        if new_scene is not self.active_scene:
            self.display.clear()
            LOG.debug('Switching to new scene: %s', new_scene)
        self.active_scene = new_scene
        self.interval = self.durations_in_s[self.active_scene]

    def _check_for_command(self):
        """Process any incoming commands."""
        if self.data_source['power'] == '1' and self.suspended:
            self.resume()
        elif self.data_source['power'] == '0' and not self.suspended:
            self.suspend()

        if self.data_source['mode'] != self._mode:
            self.apply_mode(self.data_source['mode'])

        if self.data_source['brightness'] != self._brightness:
            try:
                self._brightness = int(self.data_source['brightness'])
            except:
                self._brightness = 100
            self.display.brightness = self._brightness

    def suspend(self):
        """Turn off until the suspend command goes away (externally controlled)."""
        LOG.info('Suspending.')
        self.scene_sequence = [self._blank]

    def resume(self):
        """Resume from suspend."""
        LOG.info('Resuming')
        self.apply_mode(self._mode)

    def apply_mode(self, mode):
        """
        Apply a different sequence of scenes with different durations.

        If the mode is the name of a scene, set that scene instead.
        """
        self._mode = mode
        LOG.info('Applying mode: %s', mode)
        if mode == 'all':  # hard-coded default mode
            self.run_all_scenes()
            return
        if mode not in self.modes:
            if mode in self.scenes:
                # allow mode names to be any scene name to get just that mode.
                self.scene_sequence = [self.scenes[mode]]
            else:
                LOG.error('Invalid mode: %s', mode)
                return
        else:
            self.scene_sequence = []
            for scene_name, duration in self.modes[mode]:
                scene = self.scenes[scene_name]
                self.scene_sequence.append(scene)
                self.durations_in_s[scene] = duration

    def draw_frame(self):
        """Perform a double-buffered draw frame and frame switch."""
        self.display.clear()
        self.active_scene.draw_frame(self.display)
        self.display.buffer()

    def run_all_scenes(self, duration=5):
        """Make mode with all defined scenes running uniformly."""
        self.scene_sequence = []
        for scene in self.scenes.values():
            self.scene_sequence.append(scene)
            self.durations_in_s[scene] = duration
        self.active_scene = self.scene_sequence[0]
        LOG.debug('Running all scenes, starting with %s.', self.active_scene)


def driver_factory(disp, data_src, conf):
    """Build factory and add scenes and sprites."""
    driver = Driver(disp, data_src)
    driver.sprites = sprites.sprite_factory(conf['sprites'], data_src)
    driver.scenes = scenes.scene_factory(disp.width, disp.height,
                                         conf['scenes'], driver.sprites)

    for mode_name, scenelist in conf['modes'].items():
        driver.modes[mode_name] = []
        for sceneinfo in scenelist:
            for scene_name, durationinfo in sceneinfo.items():
                driver.modes[mode_name].append((scene_name, durationinfo['duration']))

    driver.run_all_scenes()

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

    client = mqtt.MQTTClient(datasrc, conf['mqtt'])
    client.start()
    try:
        # infopanel.start()  # multiple threads
        infopanel.run()  # main thread
    finally:
        client.stop()
        LOG.info('Quitting.')

if __name__ == "__main__":
    run()
