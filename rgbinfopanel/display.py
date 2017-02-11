"""Displays to present stuff."""

from matplotlib import cm
from rgbmatrix import graphics
from rgbmatrix import RGBMatrix, RGBMatrixOptions

from rgbinfopanel import colors


class Display(object):
    """
    A display screen.

    This is a common interface to whatever kind of display you have.
    """
    def __init__(self):
        pass

    def text(self, font, x, y, color, text):
        """Render text in a font to a place on the screen in a certain color."""
        raise NotImplementedError

    @property
    def width(self):
        raise NotImplementedError

    @property
    def height(self):
        raise NotImplementedError

    def set_pixel(self, x, y, r, g, b):
        raise NotImplementedError

    def set_image(self, image):
        raise NotImplementedError

    def rainbow_text(self, font, x, y, text, box=True):
        """Make rainbow text."""
        x0 = x
        for i, char in enumerate(text):
            color = colors.interpolate_color(float(i) / len(text), cmap=cm.gist_rainbow)  # pylint: disable=no-member
            x += self.text(font, x, y, color, char)
        if box:
            self.draw_box(x0 - 2, y - font.height + 2, x, y + 2)

    def draw_box(self, xmin, ymin, xmax, ymax):
        """Don't use PIL because it blanks.  NOTE: Use graphics.DrawLine"""
        for x in range(xmin, xmax):
            self.set_pixel(x, ymin, 0, 200, 0)
            self.set_pixel(x, ymax, 0, 200, 0)

        for y in range(ymin, ymax + 1):
            self.set_pixel(xmin, y, 0, 200, 0)
            self.set_pixel(xmax, y, 0, 200, 0)

class RGBMatrix_Display(Display):
    """An RGB LED Matrix running off of the rgbmatrix library."""
    def __init__(self, matrix):
        self._matrix = matrix
        self.canvas = matrix.CreateFrameCanvas()

    @property
    def width(self):
        return self._matrix.width

    @property
    def height(self):
        return self._matrix.height

    def text(self, font, x, y, color, text):
        return graphics.DrawText(self.canvas, font, x, y, color, text)

    def set_pixel(self, x, y, red, green, blue):
        self.canvas.SetPixel(x, y, red, green, blue)

    def set_image(self, image):
        self.canvas.SetImage(image)

    def clear(self):
        self.canvas.Clear()

    def buffer(self):
        self.canvas = self._matrix.SwapOnVSync(self.canvas)



def rgbmatrix_options_factory(config):
    """Build RGBMatrix options object."""
    options = RGBMatrixOptions()
    if config['led-gpio-mapping'] != None:
        options.hardware_mapping = config['led-gpio-mapping']
    options.rows = config['led-rows']
    options.chain_length = config['led-chain']
    options.parallel = config['led-parallel']
    options.pwm_bits = config['led-pwm-bits']
    options.brightness = config['led-brightness']
    options.pwm_lsb_nanoseconds = config['led-pwm-lsb-nanoseconds']
    if config['led-show-refresh']:
        options.show_refresh_rate = 1
    if config['led-slowdown-gpio'] != None:
        options.gpio_slowdown = config['led-slowdown-gpio']
    if config['led-no-hardware-pulse']:
        options.disable_hardware_pulsing = True
    return options

def display_factory(config):
    """Build a display based on config settings."""
    if 'RGBMatrix' in config:
        options = rgbmatrix_options_factory(config['RGBMatrix'])
        matrix = RGBMatrix(options=options)
        display = RGBMatrix_Display(matrix)
    else:
        raise ValueError('Unknown Display options. Check config file.')
    return display
