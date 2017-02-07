"""Colors."""

from matplotlib.colors import LinearSegmentedColormap

from rgbmatrix import graphics

YELLOW = graphics.Color(200, 200, 0)
GREEN = graphics.Color(0, 200, 0)
RED = graphics.Color(200, 0, 0)
BLUE = graphics.Color(0, 0, 200)

# make a custom colormap that goes from pure green to pure red.
GREEN_RED = LinearSegmentedColormap('green_red', {'red':   ((0.0, 0.0, 0.0),
                                                            (1.0, 1.0, 1.0)),

                                                  'green': ((0.0, 1.0, 1.0),
                                                            (1.0, 0.0, 0.0)),

                                                  'blue':  ((0.0, 0.0, 0.0),
                                                            (1.0, 0.0, 0.0)),
                                                 })

def interpolate_color(current, minv=0.0, maxv=1.0, cmap=None):
    """Get a color from a colormap based on interpolation."""
    if cmap is None:
        cmap = GREEN_RED
    val = (current - minv) * 255 / (maxv - minv)
    r, g, b, _a = cmap(val / 255.0)
    return graphics.Color(int(r * 255), int(g * 255), int(255 * b))