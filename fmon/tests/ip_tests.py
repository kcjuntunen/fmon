from unittest import TestCase
from fmon.ip import *

class TestCreate(TestCase):
    def test_get_ip_address(self):
        a = get_ip_address('lo')
        self.assertEqual(a, '127.0.0.1')

    def test_all_interfaces(self):
        a = all_interfaces()
        self.assertTrue('lo' in a)        
