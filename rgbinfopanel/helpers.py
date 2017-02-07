"""Helpers."""

import datetime
import os

from matplotlib.colors import LinearSegmentedColormap
from rgbmatrix import graphics

FONTS = {}

# make a custom colormap that goes from pure green to pure red.
GREEN_RED = LinearSegmentedColormap('green_red', {'red':   ((0.0, 0.0, 0.0),
                                                            (1.0, 1.0, 1.0)),

                                                  'green': ((0.0, 1.0, 1.0),
                                                            (1.0, 0.0, 0.0)),

                                                  'blue':  ((0.0, 0.0, 0.0),
                                                            (1.0, 0.0, 0.0)),
                                                 })

def day_of_week():
    """Get day of week, like MONDAY."""
    today = datetime.datetime.today()
    return today.strftime("%A").upper()

def time_now():
    """Current time like 17:05."""
    now = datetime.datetime.now()
    return now.strftime('%H:%M')

def date():
    """Date today, like: FEB 02"""
    now = datetime.datetime.now()
    return now.strftime('%b %d').upper()

def interpolate_color(current, minv=0.0, maxv=1.0, cmap=None):
    """Get a color from a colormap based on interpolation."""
    if cmap is None:
        cmap = GREEN_RED
    val = (current - minv) * 255 / (maxv - minv)
    r, g, b, _a = cmap(val / 255.0)
    return graphics.Color(int(r * 255), int(g * 255), int(255 * b))

def load_font(name):
    # s.path.join(os.path.dirname(graphics.__file__), '..', '..', 'fonts')
    FONT_DIR = '/home/pi/gpio/rpi-rgb-led-matrix/fonts'
    global FONTS
    font = FONTS.get(name)
    if font is None:
        # cache it
        font = graphics.Font()
        font.LoadFont(os.path.join(FONT_DIR, name))  # slow.
        FONTS[name] = font
    return font
