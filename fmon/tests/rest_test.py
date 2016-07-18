from unittest import TestCase

from fmon.mongoconnection import MongoConnection
from fmon import eveserve

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from xml.etree import ElementTree as etree
import testdata

ff_bin = FirefoxBinary(testdata.FF_BIN_PATH)

class TestCreate(TestCase):
    def setUp(self):
        eveserve.start_eve()
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
        #self.al = query.ArduinoLog(name='testdb')
        self.b = webdriver.Firefox(firefox_binary=ff_bin)
        self.b.implicitly_wait(3)

    def tearDown(self):
        # from time import sleep
        # sleep(30)
        self.b.quit()
        eveserve.stop_eve()
        self.mc.database['config'].drop()
        self.mc.database['alerts'].drop()
        self.mc.database['timeseriesdata'].drop()
        self.mc.database['eventdata'].drop()
        try:
            self.mc.drop_database('testdb')
        except:
            print("Didn't drop db.")
        exit(0)

    def test_get_temp(self):
        self.b.get('http://localhost:5000/lastreading/tempF')
        t = self.b.find_element_by_tag_name('body')
        self.assertEqual(testdata.light_not_transgressing['tempF'], float(t.text))

    def test_get_values(self):
        self.b.get('http://localhost:5000/timeseriesdata?maxresults=1')

        t = etree.fromstring(self.b.page_source)
        a = t.findall('resource')
        vs = a[0].findall('values')
        self.assertGreater(len(vs), 3)
