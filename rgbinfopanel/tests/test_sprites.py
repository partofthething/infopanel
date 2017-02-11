"""Tests for sprites."""
import unittest

from rgbinfopanel import sprites, driver, data


class TestSprite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        driver.apply_global_config({'global':{'font_dir':'/home/nick/codes/rpi-rgb-led-matrix/fonts'}})

    def setUp(self):
        self.sprites = build_test_sprites()

    def test_factory(self):
        self.assertIsInstance(self.sprites['I90'], sprites.Duration)
        self.assertEqual(self.sprites['I90'].label, 'I90')

    def test_value_updates(self):
        self.assertEqual(self.sprites['I90'].value(), 10.0)
        self.sprites['I90'].data_source['travel_time_i90'] = 11.0
        self.assertEqual(self.sprites['I90'].value(), 11.0)


def build_test_sprites():
    DURATION_CONFIG = {'I90':{'type':'Duration', 'label':'I90', 'low':13.0,
                     'high':25.0, 'data':'travel_time_i90' }}
    datasrc = data.InputData()
    datasrc['travel_time_i90'] = 10.0
    return sprites.sprite_factory(DURATION_CONFIG, datasrc)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
