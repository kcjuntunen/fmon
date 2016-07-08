from unittest import TestCase
from fmon.mongoconnection import MongoConnection
from fmon.fmonconfig import FMonConfiguration
from testdata import config

class TestCreate(TestCase):
    def setUp(self):
        self.fmc = FMonConfiguration(
            MongoConnection('localhost', 27017, '', ''))

    def test_serial_port(self):
        self.assertEqual(self.fmc.port, config['serial']['port'])
        self.assertEqual(self.fmc.baudrate, config['serial']['baudrate'])

    def test_sensors(self):
        sensors = self.fmc.sensors
        self.assertEqual(sensors[0]['sensor'], config['sensors'][0]['sensor'])
        self.assertEqual(sensors[0]['type'], config['sensors'][0]['type'])

        self.assertEqual(sensors[1]['sensor'], config['sensors'][1]['sensor'])
        self.assertEqual(sensors[1]['type'], config['sensors'][1]['type'])

        self.assertEqual(sensors[2]['sensor'], config['sensors'][2]['sensor'])
        self.assertEqual(sensors[2]['type'], config['sensors'][2]['type'])

    def test_id(self):
        self.assertEqual(self.fmc.id, config['id_info']['uuid'])
        self.assertEqual(self.fmc.location, config['id_info']['store'])
        self.assertEqual(self.fmc.fixture, config['id_info']['fixture'])
