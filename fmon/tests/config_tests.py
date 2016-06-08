from unittest import TestCase
from fmon.mongoconnection import MongoConnection
from fmon.fmonconfig import FMonConfiguration

class TestCreate(TestCase):
    def setUp(self):
        self.fmc = FMonConfiguration(
            MongoConnection('localhost', 27017, '', ''))
        
    def test_serial_port(self):        
        self.assertEqual(self.fmc.port, '/dev/ttyACM0')
        self.assertEqual(self.fmc.baudrate, 115200)

    def test_sensors(self):
        sensors = self.fmc.sensors
        self.assertEqual(sensors[0]['sensor'], 'light')
        self.assertEqual(sensors[0]['type'], 'timeseries')

        self.assertEqual(sensors[1]['sensor'], 'hPa')
        self.assertEqual(sensors[1]['type'], 'timeseries')

        self.assertEqual(sensors[2]['sensor'], 'tempF')
        self.assertEqual(sensors[2]['type'], 'timeseries')
