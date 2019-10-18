"""Tests for driver."""
# pylint: disable=missing-docstring
import unittest

from infopanel import mqtt
from infopanel import data


# pylint: disable=too-few-public-methods
class MockMQTTMsg(object):
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload


class TestDriver(unittest.TestCase):
    def test_bytes_mode_input(self):
        """
        Make sure a bytes mode name gets handled properly.

        Sometimes MQTT returns byte strings instead of bytes.
        """
        datasrc = data.InputData()
        client = mqtt.MQTTClient(datasrc, conf=None)
        msg = MockMQTTMsg("infopanel/mode", "random")
        client.on_message(None, None, msg)
        self.assertEqual(datasrc["mode"], "random")
        msg = MockMQTTMsg("infopanel/mode", b"random")
        client.on_message(None, None, msg)
        self.assertEqual(datasrc["mode"], "random")


if __name__ == "__main__":
    unittest.main()
