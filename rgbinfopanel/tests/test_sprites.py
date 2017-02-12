"""Tests for sprites."""
import unittest

from rgbinfopanel import sprites, data
from rgbinfopanel.tests import load_test_config

class TestSprite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conf = load_test_config()

    def setUp(self):
        self.sprites = build_test_sprites()

    def test_factory(self):
        self.assertIsInstance(self.sprites['I90'], sprites.Duration)
        self.assertEqual(self.sprites['I90'].label, 'I90')

    def test_value_updates(self):
        self.assertEqual(self.sprites['I90'].value(), 10.0)
        self.sprites['I90'].data_source['travel_time_i90'] = 11.0
        self.assertEqual(self.sprites['I90'].value(), 11.0)

class TestTemperature(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conf = load_test_config()

    def setUp(self):
        """Build temperature sprites from config."""
        self.sprites = sprites.sprite_factory(self.conf['sprites'], None)

    def test_bounds_as_input(self):
        """Make sure configured low_val gets applied correctly."""
        temp = self.sprites['daily_high']
        self.assertEqual(temp.low_val, -15.0)


def build_test_sprites():
    DURATION_CONFIG = {'I90':{'type':'Duration', 'label':'I90', 'low_val':13.0,
                     'high_val':25.0, 'data_label':'travel_time_i90' }}
    datasrc = data.InputData()
    datasrc['travel_time_i90'] = 10.0
    return sprites.sprite_factory(DURATION_CONFIG, datasrc)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
