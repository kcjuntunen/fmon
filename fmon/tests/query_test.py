from unittest import TestCase
# from unittest.mock import patch

# from datetime import datetime
# from pymongo.errors import BulkWriteError
# import json

from fmon import query
from fmon.mongoconnection import MongoConnection
# from fmon.fmonconfig import FMonConfiguration
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

        self.mc.timeseries_insert(testdata.light_not_transgressing)
        self.mc.event_insert({'name': 'PIR', 'value': 0})
        self.mc.event_insert({'name': 'Arduino reset', 'value': 0})
        # self.fmc = FMonConfiguration(self.mc)
        # self.alerts = Alerts(self.mc, self.fmc)
        self.al = query.ArduinoLog(name='testdb')

    def tearDown(self):
        # from time import sleep
        # sleep(15)
        self.mc.database['config'].drop()
        self.mc.database['alerts'].drop()
        self.mc.database['timeseriesdata'].drop()
        self.mc.database['eventdata'].drop()
        try:
            self.mc.drop_database('testdb')
        except:
            print("Didn't drop db.")

    def test_get_ts_sensors(self):
        from_config = [s['sensor'] for s in testdata.config['sensors']
                       if s['type'] == 'timeseries']
        from_config.sort()
        from_al = [s for s in self.al.ts_sensors]
        from_al.sort()
        self.assertEqual(from_config, from_al,
                         msg='{}: {}'.format(from_config, from_al))
        
    def test_get_ev_sensors(self):
        from_config = [s['sensor'] for s in testdata.config['sensors']
                       if s['type'] == 'event']
        from_config.sort()
        from_al = [s for s in self.al.ev_sensors if s is not None]
        
        from_al.sort()
        self.assertEqual(from_config, from_al,
                         msg='{}: {}'.format(from_config, from_al))
        
    def test_get_all_sensors(self):
        aas = [s for s in self.al.all_sensors]
        aas.sort()

        cas = [s['sensor'] for s in testdata.config['sensors']]
        cas.sort()
        self.assertEqual(aas, cas)

    def test_last_value(self):
        lv = testdata.light_not_transgressing['tempF']
        self.assertEqual(self.al.last_value('tempF'), lv)
