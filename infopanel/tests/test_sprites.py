"""Tests for sprites."""
# pylint: disable=missing-docstring
import unittest

from infopanel import sprites, data
from infopanel.tests import load_test_config, MockDisplay


class TestSprite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conf = load_test_config()

    def setUp(self):
        self.sprites = build_test_sprites()

    def test_factory(self):
        self.assertIsInstance(self.sprites['I90'][0], sprites.Duration)
        self.assertEqual(self.sprites['I90'][0].label, 'I90')

    def test_value_updates(self):
        self.assertEqual(self.sprites['I90'][0].value(), 10.0)
        self.sprites['I90'][0].data_source['travel_time_i90'] = 11.0
        self.assertEqual(self.sprites['I90'][0].value(), 11.0)

class TestTemperature(unittest.TestCase):


    def setUp(self):
        """Build temperature sprites from config."""
        self.conf = load_test_config()
        self.sprites = sprites.sprite_factory(self.conf['sprites'], None, MockDisplay())

    def test_bounds_as_input(self):
        """Make sure configured low_val gets applied correctly."""
        temp = self.sprites['daily_high'][0]
        self.assertEqual(temp.low_val, -15.0)

    def test_scroll_frames(self):
        """Make sure frames are dealt with for non-animated things."""
        temp = self.sprites['scroll'][0]
        self.assertEqual(temp._frame_delta, 0)  # pylint:disable=protected-access
        self.assertEqual(len(temp.frames[0][0]), 0)


def build_test_sprites():
    DURATION_CONFIG = {'I90':{'type':'Duration', 'label':'I90', 'low_val':13.0,  # pylint:disable=invalid-name
                              'high_val':25.0, 'data_label':'travel_time_i90'}}
    datasrc = data.InputData()
    datasrc['travel_time_i90'] = 10.0
    return sprites.sprite_factory(DURATION_CONFIG, datasrc, MockDisplay())

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
