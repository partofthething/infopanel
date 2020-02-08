"""Helpers."""

import datetime
import logging
import os

LOG = logging.getLogger(__name__)

FONTS = {}
FONT_DIR = None

def day_of_week():
    """Get day of week, like MONDAY."""
    today = datetime.datetime.today()
    return today.strftime("%A").upper()

def time_now():
    """Get current time like 17:05."""
    now = datetime.datetime.now()
    return now.strftime('%H:%M')

def date():
    """Get date today, like: FEB 02."""
    now = datetime.datetime.now()
    return now.strftime('%b %d').upper()

def load_font(name):
    """Load a font."""
    font = FONTS.get(name)

    if font is None:
        # cache it
        try:
            from rgbmatrix import graphics # pylint: disable=import-outside-toplevel
            font = graphics.Font()
            font.LoadFont(os.path.join(FONT_DIR, name))  # slow.
        except ImportError:
            LOG.error('Could not load font %s because the rgbmatrix '
                      'library is not found.', name)
            font = None
        FONTS[name] = font
    return font
