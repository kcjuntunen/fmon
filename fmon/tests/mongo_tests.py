from unittest import TestCase
from fmon.mongoconnection import MongoConnection
from fmon import fmon

import json

class TestCreate(TestCase):
    def setUp(self):
        self.mc = MongoConnection('localhost', 27017, '', '')
        self.fm = fmon.Fmon()

    def test_connection(self):
        self.assertIsNotNone(self.mc.connection)

    def test_database(self):
        self.assertIsNotNone(self.mc.database)

    def test_config_data(self):
        self.assertIsNotNone(self.mc.config_data)

    def test_timeseries_data(self):
        self.assertIsNotNone(self.mc.timeseries_data)

    def test_timeseries_insert(self):
        j = json.loads(""" { "hPa": 111, "tempF": 11, "light": 111 } """)
        self.mc.timeseries_insert(j)

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

    def test_create_sensor_payloads(self):
        import json
        x = json.loads( """{"hPa": 1000, "tempF": 72, "light": 200}""" )
        y = self.mc.create_insert_payloads(x)
        self.fm.logger.debug(y)

    def test_has_hour(self):
        import datetime
        x = datetime.datetime(1979, 11, 6)
        self.assertTrue(self.mc.has_hour(self.mc.current_hour))
        self.assertFalse(self.mc.has_hour(x))

    def test_get_alerts(self):
        c = self.mc.alerts.find()
        self.assertEqual(c[0]['sensor'], 'light')
        self.assertEqual(c[1]['recipients'][0], 'kcjuntunen@amstore.com')
