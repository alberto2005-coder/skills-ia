"""Suite deliberadamente inestable: una causa por test, para el escáner."""

import random
import time
import unittest

CONTADOR = 0


class InestableTest(unittest.TestCase):
    def test_espera_fija(self):
        time.sleep(0.5)
        self.assertTrue(True)

    def test_reloj_de_pared(self):
        self.assertGreater(time.time(), 0)

    def test_azar_sin_semilla(self):
        self.assertIn(random.choice([1, 2]), [1, 2])

    def test_red_real(self):
        import urllib.request

        self.assertTrue(True)

    def test_ruta_compartida(self):
        ruta = "/tmp/informe-compartido.csv"
        self.assertTrue(ruta)

    def test_estado_global(self):
        global CONTADOR
        CONTADOR += 1
        self.assertGreaterEqual(CONTADOR, 1)

    def test_bucle_sin_salida(self):
        intentos = 0
        while True:
            intentos += 1
            if intentos > 1:
                break

    @unittest.skip("flaky hasta que se arregle el servicio")
    def test_skip_permanente(self):
        self.assertTrue(True)
