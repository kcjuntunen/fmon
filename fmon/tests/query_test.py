from unittest import TestCase
# from unittest.mock import patch

# from datetime import datetime
# from pymongo.errors import BulkWriteError
# import json

from fmon import query
from fmon.mongoconnection import MongoConnection
from sys import stdout, stderr
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

        self.mc.event_insert({ 'Event': { 'name': 'PIR', 'value': 1 } })
        self.mc.event_insert({ 'Event': { 'name': 'Shock', 'value': 1 } })
        self.mc.event_insert({ 'Event': { 'name': 'Shock', 'value': 1 } })
        self.mc.event_insert({ 'Event': { 'name': 'PIR', 'value': 0 } })
        # self.fmc = FMonConfiguration(self.mc)
        # self.alerts = Alerts(self.mc, self.fmc)
        self.al = query.ArduinoLog(db=self.mc._client, name=self.mc._db)

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

    def test_last_values(self):
        lvs = testdata.light_not_transgressing
        olvs = self.al.last_values()
        dd = {}
        for d in olvs:
            k, v = d['name'], d['values']
            dd[k] = v[len(v) - 1]
        self.assertEqual(dd, lvs)

    def test_ts_ev(self):
        ev = self.al.ev
        ts = self.al.ts
        from pymongo.collection import Collection
        self.assertIsInstance(ev, Collection)
        self.assertIsInstance(ev, Collection)

    def test_sample_count(self):
        cnt = self.al.sample_count('tempF')
        self.assertEqual(cnt, 1)
        self.mc.timeseries_insert(testdata.light_not_transgressing)
        self.mc.timeseries_insert(testdata.light_transgressing)
        cnt = self.al.sample_count('tempF')
        self.assertEqual(cnt, 3)

    def test_latest_documents(self):
        ld = self.al.latest_documents()
        self.assertEqual(len(ld), len(self.al.ts_sensors))

        dd = {}
        for d in ld:
            k, v = d['name'], d['values']
            dd[k] = v[len(v) - 1]
        self.assertEqual(dd, testdata.light_not_transgressing)

    def test_hour_cursor(self):
        self.mc.timeseries_insert(testdata.light_not_transgressing)
        self.mc.timeseries_insert(testdata.light_transgressing)
        hc = self.al.hour_cursor('tempF')
        vs = hc[0]['values']
        self.assertEqual(vs[len(vs) - 1],
                         testdata.light_transgressing['tempF'])

    def test_hour_list(self):
        l = self.al.hour_list('hPa')
        self.assertEqual(l[0], testdata.light_transgressing['hPa'])

    def test_hour_events_cursor(self):
        hec1 = self.al.hour_events_cursor('PIR')
        hec2 = self.al.hour_events_cursor('Shock')
        l1 = [x for x in hec1]
        l2 = [x for x in hec2]
        self.assertEqual(hec1.count(), 3)
        self.assertEqual(len(l1), 3)
        self.assertEqual(len(l2), 2)
        self.assertEqual(hec2.count(), 2)
        print(l1)
        self.assertEqual(l1[0]['name'], 'PIR')
        self.assertEqual(l1[1]['name'], 'PIR')
        self.assertEqual(l1[1]['value'], 1)
        self.assertEqual(l2[0]['name'], 'Shock')

    def test_hour_event_list(self):
        hel = self.al.hour_event_list('PIR')
        self.assertEqual(hel[0]['name'], 'PIR')

    def test_avg_hour(self):
        pass

    def test_min_hour(self):
        pass

    def test_max_hour(self):
        pass

    def test_std_hour(self):
        pass

    def test_cv_hour(self):
        pass

    def test_count_matches(self):
        filter = { 'name': { '$in': ['tempF', 'hPa', 'light'] } }
        self.assertEqual(self.al.count_matches(filter, 'timeseriesdata'), 3)
        filter = { 'name': { '$in': ['Shock', 'PIR'] } }
        self.assertEqual(self.al.count_matches(filter, 'eventdata'), 5)

    def test_count_values(self):
        self.assertGreater(self.al.count_values('tempF'),
                           0)
        self.assertGreater(self.al.count_values('hPa'),
                           0)

    def test_hour_stats(self):
        hs = self.al.hour_stats('light')
        for i in ['min', 'max', 'avg']:
            self.assertGreater(abs(hs[i]), 0)

    def test_list_events(self):
        self.assertEqual(len(self.al.list_events()), 6)

    def test_list_values(self):
        lv = self.al.list_values('light')
        self.assertEqual(lv[0]['name'], 'light')
        self.assertEqual(lv[0]['ts'], query.current_hour())

