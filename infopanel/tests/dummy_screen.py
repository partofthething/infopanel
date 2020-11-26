"""
Dummy screen for testing in development using pygame.

This shows a graphical window on your computer instead
of using a RGB matrix.

Activate with ``DummyMatrix:`` your config file.
"""
import pygame

from infopanel import display

SCALING = 10


class DummyScreen(display.Display):
    """A dummy screen for testing purposes."""

    def __init__(self, width=64, height=32):
        """Construct a dummy screen."""
        pygame.init()  # pylint: disable=no-member

        self.canvas = pygame.Surface(
            (width, height)
        )  # pylint: disable=too-many-function-args
        self._display = pygame.display.set_mode(
            (self.width * SCALING, self.height * SCALING)
        )
        pygame.display.set_caption("infopanel test screen")
        self.clock = pygame.time.Clock()
        self._brightness = 50
        self.font = pygame.font.SysFont("courier", 9)

    @property
    def width(self):
        """Width of the display in pixels."""
        return self.canvas.get_width()

    @property
    def height(self):
        """Height of the display in pixels."""
        return self.canvas.get_height()

    @property
    def brightness(self):
        """Brightness of display from 0 to 100."""
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        """Set the brightness."""
        self._brightness = value

    def text(self, font, x, y, red, green, blue, text):
        """Render text in a font to a place on the screen in a certain color."""
        val = self.font.render(text, 0, (red, green, blue))
        width, _height = self.font.size(text)
        self.canvas.blit(val, (x + 1, y + 1 - self.font.get_height()))
        return width

    def set_pixel(self, x, y, red, green, blue):
        """Set a pixel to a color."""
        self.canvas.fill((red, green, blue), (x + 1, y + 1, 1, 1))

    def set_image(self, image, x=0, y=0):
        """Apply an image to the screen."""
        raise NotImplementedError
        myimage = pygame.image.load("myimage.bmp")  # pylint: disable=unreachable
        imagerect = myimage.get_rect()
        self.canvas.blit(myimage, imagerect)

    def clear(self):
        """Clear the canvas."""
        self.canvas.fill((0, 0, 0))  # black

    def buffer(self):
        """Swap the off-display canvas/buffer with the on-display one and scale it."""
        pygame.transform.scale(
            self.canvas, (self.width * SCALING, self.height * SCALING), self._display
        )
        pygame.display.flip()
