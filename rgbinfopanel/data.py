"""Info data"""

import collections

class InputData(collections.defaultdict):
    """Container for all the live data."""
    def __init__(self):
        collections.defaultdict.__init__(self)
        self.default_factory = lambda: 0
        self['power'] = '1'
        self['mode'] = 'all'
