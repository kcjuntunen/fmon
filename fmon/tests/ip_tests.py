from unittest import TestCase
from fmon import ip

class TestCreate(TestCase):
    def test_get_ip_address(self):
        a = ip.get_ip_address('lo')
        self.assertEqual(a, '127.0.0.1')

    def test_all_interfaces(self):
        a = ip.all_interfaces()
        print(a)
