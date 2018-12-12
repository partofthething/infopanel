"""Displays to present stuff."""

from matplotlib import cm
try:
    from rgbmatrix import graphics
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except ImportError:
    print('No RGB Matrix library found. Cannot use that display.')
    RGBMatrix = None

from infopanel import colors


class Display(object):
    """
    A display screen.

    This is a common interface to whatever kind of display you have.
    """

    def text(self, font, x, y, red, green, blue, text):
        """Render text in a font to a place on the screen in a certain color."""
        raise NotImplementedError

    @property
    def width(self):
        """Width of the display in pixels."""
        raise NotImplementedError

    @property
    def height(self):
        """Height of the display in pixels."""
        raise NotImplementedError

    @property
    def brightness(self):
        """Brightness of display from 0 to 100."""
        raise NotImplementedError

    @brightness.setter
    def brightness(self, value):
        raise NotImplementedError

    def set_pixel(self, x, y, red, green, blue):
        """Set a pixel to a color."""
        raise NotImplementedError

    def set_image(self, image, x=0, y=0):
        """Apply an image to the screen."""
        raise NotImplementedError

    def rainbow_text(self, font, x, y, text, box=True):
        """Make rainbow text."""
        x_orig = x
        for i, char in enumerate(text):
            r, g, b = colors.interpolate_color(
                float(i) / len(text), cmap=cm.gist_rainbow)  # pylint: disable=no-member
            x += self.text(font, x, y, r, g, b, char)
        if box:
            self.draw_box(x_orig - 2, y - font.height + 2, x, y + 2)

    def draw_box(self, xmin, ymin, xmax, ymax):
        """Don't use PIL because it blanks.  NOTE: Use graphics.DrawLine."""
        for x in range(xmin, xmax):
            self.set_pixel(x, ymin, 0, 200, 0)
            self.set_pixel(x, ymax, 0, 200, 0)

        for y in range(ymin, ymax + 1):
            self.set_pixel(xmin, y, 0, 200, 0)
            self.set_pixel(xmax, y, 0, 200, 0)


class RGBMatrixDisplay(Display):
    """An RGB LED Matrix running off of the rgbmatrix library."""

    def __init__(self, matrix):
        """Construct a matrix."""
        Display.__init__(self)
        self._matrix = matrix
        self.canvas = matrix.CreateFrameCanvas()

    @property
    def width(self):
        """Width of the display in pixels."""
        return self._matrix.width

    @property
    def height(self):
        """Height of the display in pixels."""
        return self._matrix.height

    @property
    def brightness(self):
        """Brightness of display from 0 to 100."""
        return self._matrix.brightness

    @brightness.setter
    def brightness(self, value):
        self._matrix.brightness = value
        self.canvas.brightness = value

    def text(self, font, x, y, red, green, blue, text):
        """Render text in a font to a place on the screen in a certain color."""
        color = graphics.Color(red, green, blue)  # may require caching
        return graphics.DrawText(self.canvas, font, x, y, color, text)

    def set_pixel(self, x, y, red, green, blue):
        """Set a pixel to a color."""
        self.canvas.SetPixel(x, y, red, green, blue)

    def set_image(self, image, x=0, y=0):
        """Apply an image to the screen."""
        self.canvas.SetImage(image, x, y)

    def clear(self):
        """Clear the canvas."""
        self.canvas.Clear()

    def buffer(self):
        """Swap the off-display canvas/buffer with the on-display one."""
        self.canvas = self._matrix.SwapOnVSync(self.canvas)


def rgbmatrix_options_factory(config):
    """Build RGBMatrix options object."""
    options = RGBMatrixOptions()
    if config['led-gpio-mapping'] is not None:
        options.hardware_mapping = config['led-gpio-mapping']
    options.rows = config['led-rows']
    options.cols = config['led-cols']
    options.chain_length = config['led-chain']
    options.parallel = config['led-parallel']
    options.pwm_bits = config['led-pwm-bits']
    options.brightness = config['led-brightness']
    options.pwm_lsb_nanoseconds = config['led-pwm-lsb-nanoseconds']
    if config['led-show-refresh']:
        options.show_refresh_rate = 1
    if config['led-slowdown-gpio'] is not None:
        options.gpio_slowdown = config['led-slowdown-gpio']
    if config['led-no-hardware-pulse']:
        options.disable_hardware_pulsing = True
    return options


def display_factory(config):
    """Build a display based on config settings."""
    if 'RGBMatrix' in config:
        if RGBMatrix is None:
            return Display()
        options = rgbmatrix_options_factory(config['RGBMatrix'])
        matrix = RGBMatrix(options=options)
        display = RGBMatrixDisplay(matrix)
    elif 'DummyMatrix' in config:
        from infopanel.tests import dummy_screen  # pylint: disable=cyclic-import
        display = dummy_screen.DummyScreen()
    else:
        raise ValueError('Unknown Display options. Check config file.')
    return display
