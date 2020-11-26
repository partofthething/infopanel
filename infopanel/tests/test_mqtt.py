"""Test MQTT connections."""

import unittest

from infopanel import mqtt
from infopanel.tests import load_test_config


class TestMqtt(unittest.TestCase):
    """Test connectivity with MQTT."""

    @classmethod
    def setUpClass(cls):
        cls.conf = load_test_config()

    def setUp(self):
        """Set up each test."""
        data = {}
        self.client = mqtt.MQTTClient(data, self.conf["mqtt"])

    @unittest.skip(
        "Something wrong with the test.mosquitto.org connection from travis ci"
    )
    def test_connect(self):
        """
        Make sure we can connect.

        This relies on the test.mosquitto.org test server.
        """
        self.client.start()
        self.client.stop()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
