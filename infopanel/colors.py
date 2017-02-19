"""Colors."""

import matplotlib.colors as mcolor

# make a custom colormap that goes from pure green to pure red.
GREEN_RED = mcolor.LinearSegmentedColormap('green_red', {'red':   ((0.0, 0.0, 0.0),
                                                            (1.0, 1.0, 1.0)),

                                                  'green': ((0.0, 1.0, 1.0),
                                                            (1.0, 0.0, 0.0)),

                                                  'blue':  ((0.0, 0.0, 0.0),
                                                            (1.0, 0.0, 0.0)),
                                                 })

def rgb_from_name(color_name):
    rgb_norm = mcolor.hex2color(mcolor.cnames[color_name])
    rgb = [int(x * 255) for x in rgb_norm]
    return rgb

def interpolate_color(current, minv=0.0, maxv=1.0, cmap=None):
    """Get a color from a colormap based on interpolation."""
    if cmap is None:
        cmap = GREEN_RED
    val = (current - minv) * 255 / (maxv - minv)
    r, g, b, _a = cmap(val / 255.0)
    return [int(x * 255) for x in (r, g, b)]
