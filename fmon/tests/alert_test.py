from unittest import TestCase
from unittest.mock import patch

from datetime import datetime
import json

from fmon.mongoconnection import MongoConnection
from fmon.fmonconfig import FMonConfiguration
from fmon.alerts import Alerts

import testdata

class TestCreate(TestCase):
    def setUp(self):
        self.mc = MongoConnection('localhost', 27017, '', '')
        self.fmc = FMonConfiguration(self.mc)
        self.alerts = Alerts(self.mc, self.fmc)

    def test_found_something(self):
        self.assertIsNotNone(self.alerts)

    def test_get_alerts(self):
        al = self.alerts.alert_list
        self.assertIsInstance(al, set,
                              msg='This is a {}.'.format(type(al)))

    def test_get_alert_item(self):
        alight, atemp = self.alerts.alert_list
        self.assertIsNotNone(alight.sensor)
        self.assertEqual(atemp.recipients[0],
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
            if alert.sensor == testdata.alerts[0]['sensor']:
                self.assertEqual(alert.limits['days'], 0b1111100)
            if alert.sensor == testdata.alerts[1]['sensor']:
                self.assertEqual(alert.limits['days'], 0b0000111)

    @patch('fmon.alerts.datetime')
    def test_check_ok_to_send(self, mock_date):
        mock_date.today.return_value = datetime(2016, 6, 20, 10, 0)
        mock_date.now.return_value = datetime(2016, 6, 20, 10, 0)
        for alert in self.alerts:
            if alert.sensor == 'light':
                self.assertTrue(alert.ok_to_send, msg="light should be true")
                alert.sent = True
                self.assertFalse(alert.ok_to_send)
            if alert.sensor == 'tempF':
                self.assertFalse(alert.ok_to_send, msg= "tempF should be f")
            
    def test_send_alerts(self):
        a = {alert.sensor: alert for alert in self.alerts}
        self.alerts.send_alerts(testdata.light_trangressing)
        self.assertTrue(a[testdata.alerts[0]['sensor']].sent)
        self.assertFalse(a[testdata.alerts[1]['sensor']].sent)

        self.alerts.send_alerts(light_not_transgressing)
        self.assertFalse(a[testdata.alerts[0]['sensor']].sent)

    def test_agreeable_day(self):        
        a = {alert.sensor: alert for alert in self.alerts}
        print(a)
        self.assertTrue(
            a[testdata.alerts[1]['sensor']].agreeable_day(5))

        self.assertTrue(
            a[testdata.alerts[1]['sensor']].agreeable_day(6))

        self.assertFalse(
            a[testdata.alerts[1]['sensor']].agreeable_day(3))

        self.assertTrue(
            a[testdata.alerts[0]['sensor']].agreeable_day(2))

        self.assertTrue(
            a[testdata.alerts[0]['sensor']].agreeable_day(3))

        self.assertFalse(
            a[testdata.alerts[0]['sensor']].agreeable_day(6))

    def test_within_workday(self):
        a = [alert for alert in self.alerts]
        self.assertTrue(a[0].within_workday(800))
        self.assertFalse(a[0].within_workday(1200))
        self.assertFalse(a[0].within_workday(200))
        self.assertTrue(a[1].within_workday(800))
        self.assertFalse(a[1].within_workday(1200))
        self.assertFalse(a[1].within_workday(200))

    def test_equality(self):
        a = {alert.sensor: alert for alert in self.alerts}
        x = a[testdata.alerts[0]['sensor']]
        y = a[testdata.alerts[0]['sensor']]
        y.sent = True
        self.assertEqual(x, y)

    def test_transgressing_range(self):
        a = {alert.sensor: alert for alert in self.alerts}
        self.assertFalse(a[testdata.alerts[0]['sensor']].
                         transgressing_range(testdata.light_not_transgressing))
        self.assertTrue(a[testdata.alerts[0]['sensor']].transgressing_range(testdata.light_trangressing))
        self.assertFalse(a[testdata.alerts[1]['sensor']].
                         transgressing_range(testdata.light_not_transgressing))
