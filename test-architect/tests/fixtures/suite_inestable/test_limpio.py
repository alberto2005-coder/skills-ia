"""Suite determinista: no debe producir ningún hallazgo."""

import tempfile
import unittest
from pathlib import Path


class LimpioTest(unittest.TestCase):
    def test_suma(self):
        self.assertEqual(2 + 2, 4)

    def test_temporal_aislado(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "datos.txt"
            ruta.write_text("hola", encoding="utf-8")
            self.assertEqual(ruta.read_text(encoding="utf-8"), "hola")
