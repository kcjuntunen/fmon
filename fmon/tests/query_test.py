from unittest import TestCase
# from unittest.mock import patch

from datetime import datetime
from pymongo.errors import BulkWriteError
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

        # self.fmc = FMonConfiguration(self.mc)
        # self.alerts = Alerts(self.mc, self.fmc)
        self.al = query.ArduinoLog(db=self.mc._client, name=self.mc._db)
        self.mc.timeseries_insert(testdata.light_not_transgressing)
        asensor, bsensor, csensor = [x['sensor']
                                     for x in testdata.config['sensors']
                                     if x['type'] == 'event']
        self.mc.event_insert({'name': csensor, 'value': 0})
        self.mc.event_insert({'name': asensor, 'value': 0})
        self.mc.event_insert({ 'Event': { 'name': asensor, 'value': 1 } })
        self.mc.event_insert({ 'Event': { 'name': bsensor, 'value': 1 } })
        self.mc.event_insert({ 'Event': { 'name': bsensor, 'value': 1 } })
        self.mc.event_insert({ 'Event': { 'name': asensor, 'value': 0 } })

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
        asensor = testdata.config['sensors'][2]['sensor']
        lv = testdata.light_not_transgressing[asensor]
        self.assertEqual(self.al.last_value(asensor), lv)

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
        asensor = testdata.config['sensors'][2]['sensor']
        cnt = self.al.sample_count(asensor)
        self.assertEqual(cnt, 1)
        self.mc.timeseries_insert(testdata.light_not_transgressing)
        self.mc.timeseries_insert(testdata.light_transgressing)
        cnt = self.al.sample_count(asensor)
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
        asensor = testdata.config['sensors'][0]['sensor']
        self.mc.timeseries_insert(testdata.light_not_transgressing)
        self.mc.timeseries_insert(testdata.light_transgressing)
        hc = self.al.hour_cursor(asensor)
        vs = hc[0]['values']
        self.assertEqual(vs[len(vs) - 1],
                         testdata.light_transgressing[asensor])

    def test_hour_list(self):
        asensor = testdata.config['sensors'][0]['sensor']
        l = self.al.hour_list(asensor)
        self.assertEqual(l[0], testdata.light_transgressing[asensor])

    def test_hour_events_cursor(self):
        asensor = self.al.ev_sensors[0]
        bsensor = self.al.ev_sensors[1]
        hec1 = self.al.hour_events_cursor(asensor)
        hec2 = self.al.hour_events_cursor(bsensor)
        l1 = [x for x in hec1]
        l2 = [x for x in hec2]
        self.assertEqual(hec1.count(), 2)
        self.assertEqual(len(l1), 2)
        self.assertEqual(len(l2), 3)
        self.assertEqual(hec2.count(), 3)
        print(l1)
        self.assertEqual(l1[0]['name'], asensor)
        self.assertEqual(l1[1]['name'], asensor)
        self.assertEqual(l1[1]['value'], 1)
        self.assertEqual(l2[0]['name'], bsensor)

    def test_hour_event_list(self):
        ev = self.al.ev_sensors
        hel = self.al.hour_event_list(ev[0])
        self.assertEqual(hel[0]['name'], ev[0])

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
        filter = { 'name': { '$in': self.al.ts_sensors } }
        self.assertEqual(self.al.count_matches(filter, 'timeseriesdata'),
                         len(self.al.ts_sensors))
        filter = { 'name': { '$in': self.al.ev_sensors } }
        self.assertEqual(self.al.count_matches(filter, 'eventdata'),
                         6)

    def test_count_values(self):
        asensor = testdata.config['sensors'][0]['sensor']
        bsensor = testdata.config['sensors'][2]['sensor']
        self.assertGreater(self.al.count_values(asensor),
                           0)
        self.assertGreater(self.al.count_values(bsensor),
                           0)

    def test_hour_stats(self):
        asensor = testdata.config['sensors'][2]['sensor']
        hs = self.al.hour_stats(asensor)
        for i in ['min', 'max', 'avg']:
            self.assertGreater(abs(hs[i]), 0)

    def test_list_events(self):
        self.assertEqual(len(self.al.list_events()), 6)

    def test_list_values(self):
        asensor = testdata.config['sensors'][2]['sensor']
        lv = self.al.list_values(asensor)
        self.assertEqual(lv[0]['name'], asensor)
        self.assertEqual(lv[0]['ts'], query.current_hour())
