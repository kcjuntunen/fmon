from unittest import TestCase
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from xml.etree import ElementTree as etree
import testdata

ff_bin = FirefoxBinary(testdata.FF_BIN_PATH)

class TestCreate(TestCase):
    def setUp(self):
        self.b = webdriver.Firefox(firefox_binary=ff_bin)

    def tearDown(self):
        self.b.close()

    def test_get_temp(self):
        self.b.get('http://localhost:5000/lastreading/tempF')
        t = self.b.find_element_by_tag_name('body')
        self.assertEqual(testdata.light_not_transgressing['tempF'], float(t.text))

    def test_get_values(self):
        self.b.get('http://localhost:5000/timeseriesdata?maxresults=1')

        t = etree.fromstring(self.b.page_source)
        a = t.findall('resource')
        vs = a[0].findall('values')
        self.assertGreater(len(vs), 10)
