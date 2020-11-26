"""Input data that might come over MQTT or whatever."""

import collections


class InputData(collections.defaultdict):
    """Container for all the live data."""

    def __init__(self):
        """Construct default data."""
        collections.defaultdict.__init__(self)
        self.default_factory = lambda: 0
        self["power"] = "1"
        self["mode"] = "all"
        self["brightness"] = 100
        self["image_path"] = ""
        self["random"] = "0"
