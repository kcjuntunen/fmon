from unittest import TestCase
from fmon import fmon

class TestCreate(TestCase):
    def setUp(self):
        self.f = fmon.Fmon()

    def test_poll(self):
        self.f.poll()
        line = self.f.get_line()
        self.assertGreater(len(line), 0)

    def test_start(self):
        # fmon.start()
        pass
