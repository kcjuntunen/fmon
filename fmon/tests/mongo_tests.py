from unittest import TestCase
from fmon.mongoconnection import MongoConnection

class TestCreate(TestCase):
    def setUp(self):
        self.mc = MongoConnection('localhost', 27017, '', '')

    def test_connection(self):
        self.assertIsNotNone(self.mc.connection)

    def test_database(self):
        self.assertIsNotNone(self.mc.database)

    def test_config_data(self):
        self.assertIsNotNone(self.mc.config_data)

    def test_timeseries_data(self):
        self.assertIsNotNone(self.mc.timeseries_data)

    def test_timeseries_insert(self):
        self.mc.timeseries_insert(
            { "Poll":
              { "hPa": 111,
                "tempF": 11,
                "light": 111
              }
            })

        self.mc.timeseries_insert(
              { "hPa": 111,
                "tempF": 11,
                "light": 111
              })

    def test_event_insert(self):
        self.mc.event_insert({ "Event":
              { "type": "PIR detect",
                "value": 0
              }
            })

        self.mc.event_insert(
              { "type": "PIR reset",
                "value": 0
              })
