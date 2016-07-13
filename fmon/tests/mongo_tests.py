from unittest import TestCase
from fmon.mongoconnection import MongoConnection
from pymongo.errors import BulkWriteError
from fmon import fmon

import json

import testdata

class TestCreate(TestCase):
    def setUp(self):
        self.mc = MongoConnection('localhost', 27017, '', '', 'testdb')
        try:
            self.mc.database['config'].insert_one(testdata.config)
        except Exception as e:
            print(e)
            
        bulk = self.mc.database['alerts'].initialize_unordered_bulk_op()
        for alert in testdata.alerts:
            bulk.insert(alert)
        try:
            bulk.execute()
        except BulkWriteError as bwe:
            print(bwe)
        self.fm = fmon.Fmon()

    def tearDown(self):
        self.mc.database['config'].drop()
        self.mc.database['alerts'].drop()
        self.mc.database['timeseriesdata'].drop()
        self.mc.database['eventdata'].drop()
        try:
            self.mc.drop_database('testdb')
        except:
            print("Didn't drop db.")

    def test_connection(self):
        self.assertIsNotNone(self.mc.connection)

    def test_database(self):
        self.assertIsNotNone(self.mc.database)

    def test_config_data(self):
        self.assertIsNotNone(self.mc.config_data)

    def test_timeseries_data(self):
        self.assertIsNotNone(self.mc.timeseries_data)

    def test_timeseries_insert(self):
        #self.fm.logger.error(testdata.json_string)
        j = json.loads(testdata.json_string)
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
        x = json.loads(testdata.json_string)
        y = self.mc.create_insert_payloads(x)
        self.fm.logger.debug(y)

    # This is unnecessary because of upserts.
    # def test_has_hour(self):
    #     import datetime
    #     x = datetime.datetime(1979, 11, 6)
    #     self.assertTrue(self.mc.has_hour(self.mc.current_hour))
    #     self.assertFalse(self.mc.has_hour(x))

    def test_get_alerts(self):
        c = self.mc.alerts.find()
        self.assertEqual(c[0]['sensor'], testdata.alerts[0]['sensor'])
        self.assertEqual(c[1]['recipients'][0], testdata.alerts[0]['recipients'][0])
