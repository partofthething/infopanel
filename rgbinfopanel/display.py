"""Home automation status/info panel for RGB LED matrix."""

import threading
import argparse
import time
import os
import random
import collections

from matplotlib import cm
from rgbmatrix import graphics
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import yaml

from rgbinfopanel import mqtt, scenes, helpers

FRAME_DELAY_S = 0.005

class Display(threading.Thread):
    """The display matrix."""

    def __init__(self, matrix, live_data, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        print('Starting Matrix')
        self.matrix = matrix
        self.font = helpers.load_font('5x8.bdf')
        self.line_height = self.font.height
        self.live_data = live_data
        self.canvas = self.matrix.CreateFrameCanvas()
        self._stop = threading.Event()
        self.scenes = [scenes.Giraffes(self), scenes.Welcome(self), scenes.Traffic(self)]
        self.durations_in_s = [15, 5, 10]  # favor some scenes over others time-wise
        self.scene = None
        self._change_scene()
        self.x, self.y = 0, 0
        self._scroll_x = None

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
        """Switch to another scene, maybe."""
        choice = random.randint(0, len(self.scenes) - 1)
        self.scene = self.scenes[choice]
        self.interval = self.durations_in_s[choice]

    def draw_frame(self):
        """Perform a double-buffered draw frame and frame switch."""
        self.canvas.Clear()
        self.scene.draw_frame()
        self.reset_cursor()
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def reset_cursor(self):
        """Put cursor at 0,0."""
        self.x, self.y = 0, 0

    def _draw_text_lines(self, lines):
        self.y += self.line_height
        x0 = self.x
        for info in lines:
            self.x = x0
            for text, color in info:
                self.x += graphics.DrawText(self.canvas, self.font, self.x, self.y, color, text)
            self.y += self.line_height

    def rainbow_text(self, canvas, font, x, y, text, box=True):
        """Make rainbow text."""
        x0 = x
        for i, char in enumerate(text):
            color = helpers.interpolate_color(float(i) / len(text), cmap=cm.gist_rainbow)  # pylint: disable=no-member
            x += graphics.DrawText(canvas, font, x, y, color, char)
        if box:
            self.draw_box(canvas, x0 - 2, y - font.height + 2, x, y + 2)

    def draw_box(self, canvas, xmin, ymin, xmax, ymax):
        """Don't use PIL because it blanks.  NOTE: Use graphics.DrawLine"""
        for x in range(xmin, xmax):
            canvas.SetPixel(x, ymin, 0, 200, 0)
            canvas.SetPixel(x, ymax, 0, 200, 0)

        for y in range(ymin, ymax + 1):
            canvas.SetPixel(xmin, y, 0, 200, 0)
            canvas.SetPixel(xmax, y, 0, 200, 0)

class InputData(collections.defaultdict):
    """Container for all the live data."""
    def __init__(self):
        collections.defaultdict.__init__(self)
        self.default_factory = lambda: 0
        self.temp_low = None
        self.temp_high = None
        self.temp_current = None
        self.precip_intensity_today = None
        self.travel_mode = None




def process_args():
    """Turn args into options object and build matrix."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--led-rows", action="store",
                        help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32",
                        default=32, type=int)
    parser.add_argument("-c", "--led-chain", action="store",
                        help="Daisy-chained boards. Default: 1.", default=1, type=int)
    parser.add_argument("-P", "--led-parallel", action="store",
                        help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1",
                        default=1, type=int)
    parser.add_argument("-p", "--led-pwm-bits", action="store",
                        help="Bits used for PWM. Something between 1..11. Default: 11",
                        default=11, type=int)
    parser.add_argument("-b", "--led-brightness", action="store",
                        help="Sets brightness level. Default: 100. Range: 1..100",
                        default=100, type=int)
    parser.add_argument("-m", "--led-gpio-mapping",
                        help="Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm" ,
                        choices=['regular', 'adafruit-hat', 'adafruit-hat-pwm'], type=str)
    parser.add_argument("--led-scan-mode", action="store",
        help="Progressive or interlaced scan. 0 Progressive, 1 Interlaced (default)",
        default=1, choices=range(2), type=int)
    parser.add_argument("--led-pwm-lsb-nanoseconds", action="store",
                        help=("Base time-unit for the on-time in the lowest significant bit in "
                              "nanoseconds. Default: 130"),
                        default=130, type=int)
    parser.add_argument("--led-show-refresh", action="store_true",
                        help="Shows the current refresh rate of the LED panel")
    parser.add_argument("--led-slowdown-gpio", action="store",
                        help="Slow down writing to GPIO. Range: 1..100. Default: 1",
                        choices=range(3), type=int)
    parser.add_argument("--led-no-hardware-pulse", action="store",
                        help="Don't use hardware pin-pulse generation")
    parser.add_argument("--config", action="store", help="Point to a YAML configuration file.",
                        default='/etc/ledmatrix/ledmatrix.yaml')

    args = parser.parse_args()

    options = RGBMatrixOptions()

    if args.led_gpio_mapping != None:
        options.hardware_mapping = args.led_gpio_mapping
    options.rows = args.led_rows
    options.chain_length = args.led_chain
    options.parallel = args.led_parallel
    options.pwm_bits = args.led_pwm_bits
    options.brightness = args.led_brightness
    options.pwm_lsb_nanoseconds = args.led_pwm_lsb_nanoseconds
    if args.led_show_refresh:
        options.show_refresh_rate = 1
    if args.led_slowdown_gpio != None:
        options.gpio_slowdown = args.led_slowdown_gpio
    if args.led_no_hardware_pulse:
        options.disable_hardware_pulsing = True

    if os.path.exists(args.config):
        # config file values override any command line args or their defaults.
        load_config_yaml(args.config, options)

    matrix = RGBMatrix(options=options)
    return matrix

def load_config_yaml(path, options):
    """Load optional config file as an alternative to command line options."""
    with open(path) as configfile:
        config = yaml.load(configfile)
    # apply settings

def run():
    """Run the screen."""
    matrix = process_args()
    data = InputData()

    client = mqtt.MQTT_Client(data)
    client.start()

    try:
        display = Display(matrix, data)
        # display.start()  # multiple threads
        display.run()  # main thread
    finally:
        client.stop()
        print('Quitting.')

if __name__ == "__main__":
    run()
