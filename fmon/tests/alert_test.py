from unittest import TestCase

from datetime import datetime
import json

from fmon.mongoconnection import MongoConnection
from fmon.fmonconfig import FMonConfiguration
from fmon.alerts import Alerts

class TestCreate(TestCase):
    def setUp(self):
        self.mc = MongoConnection('localhost', 27017, '', '')
        self.fmc = FMonConfiguration(self.mc)
        self.alerts = Alerts(self.mc, self.fmc)

    def test_found_something(self):
        self.assertIsNotNone(self.alerts)

    def test_get_alerts(self):
        al = self.alerts.alert_list
        self.assertIsInstance(al, list,
                              msg='This is a {}.'.format(type(al)))

    def test_get_alert_item(self):
        al = self.alerts.alert_list
        self.assertEqual(al[0].sensor, 'light')
        self.assertEqual(al[1].recipients[0],
                         'kcjuntunen@amstore.com')

    def test_query_alert_count(self):
        self.assertGreater(len(self.alerts), 1)

    def test_query_alert_generator(self):
        res = False
        for alert in self.alerts:
            if "kcjuntunen@amstore.com" in alert.recipients:
                res = True
        self.assertTrue(res)

    def test_return_repr(self):
        self.assertEqual(str(self.alerts), 'Alerts: 2 items')

    def test_get_alert_limits(self):
        for alert in self.alerts:
            self.assertEqual(alert.limits['days'], 124)

    def test_check_ok_to_send(self):
        early = datetime(2016, 6, 20, 5)
        oktime = datetime(2016, 6, 20, 10)
        for alert in self.alerts:
            self.assertTrue(alert.ok_to_send)

    def test_send_alerts(self):
        jo = json.loads('{"light": 800, "tempF": 90}')
        self.alerts.send_alerts(jo)
