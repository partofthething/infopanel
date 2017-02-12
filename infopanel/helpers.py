"""Helpers."""

import datetime
import os


FONTS = {}
FONT_DIR = None

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

def load_font(name):
    from rgbmatrix import graphics
    global FONTS
    font = FONTS.get(name)
    if font is None:
        # cache it
        font = graphics.Font()
        font.LoadFont(os.path.join(FONT_DIR, name))  # slow.
        FONTS[name] = font
    return font
