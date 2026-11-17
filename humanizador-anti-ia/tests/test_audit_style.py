# -*- coding: utf-8 -*-
"""Tests de audit_style.py: separación IA/humano, protección y honestidad.

Ejecutar desde la raíz del repo:
    py -m unittest discover -s humanizador-anti-ia/tests -v
"""

import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT = ROOT / "scripts" / "audit_style.py"
CORPUS = HERE / "corpus"

_spec = importlib.util.spec_from_file_location("audit_style", str(SCRIPT))
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

SCORE_KEYS = (
    "total",
    "vocabulario_ia",
    "uniformidad_frases",
    "patrones_estructurales",
    "artefactos_chatbot",
)

IA_FILES = sorted(p for p in CORPUS.glob("*.txt") if p.name.startswith("ia_"))
HUMAN_FILES = sorted(p for p in CORPUS.glob("*.txt") if p.name.startswith("humano_"))


def read(name):
    return (CORPUS / name).read_text(encoding="utf-8")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class TestCorpus(unittest.TestCase):
    def test_corpus_completo(self):
        self.assertEqual(len(IA_FILES), 2, "deben existir 2 textos ia_*.txt")
        self.assertEqual(len(HUMAN_FILES), 2, "deben existir 2 textos humano_*.txt")
        self.assertTrue((CORPUS / "datos_sin_fuente.txt").exists())
        self.assertTrue((CORPUS / "codigo_links.txt").exists())


class TestSeparacionIAHumano(unittest.TestCase):
    def test_ia_puntua_mas_que_humano(self):
        ia = {p.name: audit.score_text(p.read_text(encoding="utf-8"))["total"] for p in IA_FILES}
        humano = {p.name: audit.score_text(p.read_text(encoding="utf-8"))["total"] for p in HUMAN_FILES}
        worst_ia = min(ia.values())
        best_humano = max(humano.values())
        self.assertGreater(
            worst_ia,
            best_humano + 15,
            "el texto IA más flojo debe superar al humano más alto por 15 puntos: %r vs %r" % (ia, humano),
        )
        mean_ia = sum(ia.values()) / len(ia)
        mean_humano = sum(humano.values()) / len(humano)
        self.assertGreater(mean_ia, mean_humano + 25, "separación media insuficiente: %r vs %r" % (ia, humano))

    def test_puntuaciones_en_rango(self):
        for path in IA_FILES + HUMAN_FILES:
            score = audit.score_text(path.read_text(encoding="utf-8"))
            for key in SCORE_KEYS:
                self.assertIn(key, score)
                self.assertGreaterEqual(score[key], 0.0)
                self.assertLessEqual(score[key], 100.0)
            self.assertIn(score["nivel"], ("bajo", "moderado", "medio", "alto", "muy alto"))

    def test_score_es_determinista(self):
        text = read(IA_FILES[0].name)
        self.assertEqual(audit.score_text(text), audit.score_text(text))


class TestProteccionEstructura(unittest.TestCase):
    def test_codigo_no_contamina_metricas(self):
        report = audit.analyze_text(read("codigo_links.txt"))
        self.assertEqual(report["banned_phrases_count"], 0, report["banned_phrases"])
        self.assertEqual(report["em_dashes_count"], 0)
        self.assertEqual(report["score"]["detalle"]["estructura"]["no_solo_sino"], 0)
        self.assertEqual(report["score"]["artefactos_chatbot"], 0.0)
        self.assertGreaterEqual(report["protected_segments"]["code_block"], 1)
        self.assertGreaterEqual(report["protected_segments"]["inline_code"], 1)
        self.assertGreaterEqual(report["protected_segments"]["enlace"], 2)

    def test_mask_y_restore_son_reversibles(self):
        original = read("codigo_links.txt")
        masked, segments = audit.mask_protected(original)
        self.assertNotIn("https://ejemplo.com", masked)
        self.assertNotIn("def cargar", masked)
        self.assertTrue(any(s["tipo"] == "code_block" for s in segments))
        self.assertTrue(any(s["texto"].startswith("https://") for s in segments))
        self.assertEqual(audit.restore_masked(masked, segments), original)

    def test_url_no_cuenta_como_palabras(self):
        con_url = audit.analyze_text("Mira esto https://ejemplo.com/a-b-c-d-e-f-g y dime.")
        sin_url = audit.analyze_text("Mira esto y dime.")
        self.assertEqual(con_url["total_words"], sin_url["total_words"])

    def test_frontmatter_intacto(self):
        text = "---\nname: demo\ndescription: texto crucial y fascinante\n---\n\nLa caja se cerro a las seis."
        masked, segments = audit.mask_protected(text)
        self.assertTrue(any(s["tipo"] == "frontmatter" for s in segments))
        report = audit.analyze_text(text)
        self.assertEqual(report["banned_phrases_count"], 0)
        self.assertEqual(audit.restore_masked(masked, segments), text)


class TestHonestidadFactual(unittest.TestCase):
    def test_detecta_datos_sin_fuente(self):
        findings = audit.detect_data_to_verify(read("datos_sin_fuente.txt"))
        self.assertGreaterEqual(len(findings), 2)
        self.assertTrue(any("68" in f["texto"] for f in findings), findings)
        self.assertTrue(any(f["tipo"] == "dato sin fuente" for f in findings))
        for finding in findings:
            self.assertIn("verificar", finding["accion"].lower())

    def test_no_marca_el_dato_con_fuente(self):
        findings = audit.detect_data_to_verify(read("datos_sin_fuente.txt"))
        self.assertFalse(any("INE" in f["texto"] for f in findings), findings)

    def test_no_inventa_cifras_en_el_analisis(self):
        text = read("datos_sin_fuente.txt")
        report = audit.analyze_text(text)
        for finding in report["datos_a_verificar"]:
            self.assertIn(finding["texto"].split()[0], text)


class TestCLI(unittest.TestCase):
    def test_score_json_tiene_las_cuatro_claves(self):
        proc = run_cli("--score", "--file", str(IA_FILES[0]))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        for key in SCORE_KEYS:
            self.assertIn(key, data)
        self.assertGreaterEqual(data["total"], 0)
        self.assertLessEqual(data["total"], 100)
        self.assertIn("datos_a_verificar", data)

    def test_json_compatible_con_uso_anterior(self):
        proc = run_cli("--json", "--file", str(IA_FILES[0]))
        self.assertEqual(proc.returncode, 2, proc.stderr)
        data = json.loads(proc.stdout)
        for key in ("burstiness_cv", "banned_phrases", "issues", "passed", "score"):
            self.assertIn(key, data)

    def test_markdown_incluye_score_y_datos_a_verificar(self):
        proc = run_cli("--markdown", "--file", str(CORPUS / "datos_sin_fuente.txt"))
        self.assertIn("Puntuación IA", proc.stdout)
        self.assertIn("Datos a Verificar", proc.stdout)
        self.assertIn("verificar", proc.stdout)

    def test_help_funciona_y_explica_la_direccion_del_score(self):
        proc = run_cli("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--score", proc.stdout)
        self.assertIn("MÁS ALTO", proc.stdout.upper())

    def test_texto_vacio_falla_con_codigo_1(self):
        proc = run_cli("--text", "   ")
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
