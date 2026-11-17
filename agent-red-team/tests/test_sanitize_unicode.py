"""Tests del saneador de Unicode invisible y comentarios ocultos."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import sanitize_unicode  # noqa: E402

MALICIOSA = RAIZ / "tests" / "fixtures" / "skill_maliciosa"


class TestSanitizeUnicode(unittest.TestCase):
    """(c) sanitize_unicode detecta y elimina caracteres invisibles."""

    @classmethod
    def setUpClass(cls):
        base = Path(tempfile.mkdtemp(prefix="art-sanitize-"))
        cls.addClassCleanup(shutil.rmtree, str(base), ignore_errors=True)
        copia = base / "skill_maliciosa"
        shutil.copytree(str(MALICIOSA), str(copia),
                        ignore=shutil.ignore_patterns("__pycache__", "*.py[co]"))
        cls.original = (copia / "SKILL.md").read_text(encoding="utf-8")
        cls.limpio, cls.u_count, cls.c_count = sanitize_unicode.sanitize_content(cls.original)

    def test_cuenta_invisibles(self):
        self.assertGreaterEqual(self.u_count, 2)

    def test_elimina_comentarios_html(self):
        self.assertGreaterEqual(self.c_count, 1)
        self.assertNotIn("<!--", self.limpio)
        self.assertNotIn("Nota interna", self.limpio)

    def test_no_queda_unicode_invisible(self):
        for idx, ch in enumerate(self.limpio):
            if idx == 0 and ord(ch) == 0xFEFF:
                continue
            self.assertNotIn(ord(ch), sanitize_unicode.INVISIBLE_CODEPOINTS)

    def test_conserva_el_texto_visible(self):
        self.assertIn("Formateador Pro", self.limpio)
        self.assertIn("scripts/sync_env.py", self.limpio)

    def test_fichero_saneado_se_escribe_aparte(self):
        tmp = tempfile.mkdtemp(prefix="art-sanitize-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        destino = Path(tmp) / "SKILL.md"
        destino.write_text(self.original, encoding="utf-8")

        salida, u_count, c_count = sanitize_unicode.sanitize_content(
            destino.read_text(encoding="utf-8")
        )
        ruta_salida = destino.with_suffix(destino.suffix + ".sanitized")
        ruta_salida.write_text(salida, encoding="utf-8")

        self.assertTrue(ruta_salida.exists())
        self.assertGreaterEqual(u_count, 2)
        self.assertGreaterEqual(c_count, 1)
        # El original no se modifica.
        self.assertIn("\u200b", destino.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
