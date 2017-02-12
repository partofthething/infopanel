"""Test Scenes."""
import unittest

from infopanel import scenes, sprites
from infopanel.tests import test_sprites, load_test_config

class TestScenes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conf = load_test_config()

    def setUp(self):
        sprites = test_sprites.build_test_sprites()
        self.scenes = build_test_scenes(sprites)

    def test_factory(self):
        scene = self.scenes['traffic']
        self.assertIsInstance(scene, scenes.Scene)
        self.assertEqual(len(scene.sprites), 2)
        self.assertEqual(scene.sprites[0].x, 0)
        self.assertEqual(scene.sprites[0].max_x, 64)

    def test_all(self):
        existing_sprites = sprites.sprite_factory(self.conf['sprites'], None)
        scenes.scene_factory(64, 32, self.conf['scenes'], existing_sprites)


def build_test_scenes(sprites):
    SCENE_CONFIG = {'traffic':{'type':'Scene', 'sprites':[{'I90':{'x':0, 'y':8}},
                                                          {'I90':{'x':0, 'y':16}}]}}
    return scenes.scene_factory(64, 32, SCENE_CONFIG, sprites)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
