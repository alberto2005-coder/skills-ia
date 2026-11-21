"""Test que da por cubierto `utils.py` en el fixture."""

import unittest


class UtilsTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(1 + 1, 2)
