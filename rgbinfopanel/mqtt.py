"""MQTT client to get data into the display from some data source."""

import paho.mqtt.client as mqtt
import yaml

class MQTT_Client(object):

    def __init__(self, data_container):
        self._client = None
        self._data_container = data_container
        with open('/etc/ledmatrix/ledmatrix.yaml') as f:
            self.conf = yaml.load(f)['mqtt']

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe(self.conf['topic'])  # subscribe in case we get disconnected

    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        key = msg.topic.split('/')[-1]
        self._data_container[key] = msg.payload

    def start(self):
        conf = self.conf
        print('Connecting to MQTT server at {}'.format(conf['broker']))
        self._client = mqtt.Client(conf['client_id'], protocol=conf['protocol'])
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        self._client.username_pw_set(conf['username'], conf['password'])
        self._client.tls_set(conf['certificate'])
        self._client.connect(conf['broker'], conf['port'], conf['keepalive'])
        self._client.loop_start()

    def stop(self):
        self._client.loop_stop()
