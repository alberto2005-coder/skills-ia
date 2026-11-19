"""La documentación no puede desviarse del código: `--fail-on` y recuentos de tests."""

import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_DOC = ROOT / "docs" / "index.md"
TABLE_HEADERS = ("| Valores | Herramientas |", "| Values | Tools |")

DOC_TEST_COUNTS = {
    "docs/appsec-audit.md": ("appsec-audit", r"(?:aporta|ships) (\d+) tests"),
    "docs/refactor-surgeon.md": ("refactor-surgeon", r"(?m)^(\d+) tests:"),
    "docs/db-architect.md": ("db-architect", r"(?m)^(\d+) tests:"),
}


def table_rows(text):
    """(celda de valores, celda de herramientas) por fila de las tablas de `--fail-on`."""
    lines = text.splitlines()
    rows = []
    for start, line in enumerate(lines):
        if line.strip() not in TABLE_HEADERS:
            continue
        position = start + 2  # cabecera + separador
        while position < len(lines) and lines[position].startswith("|"):
            cells = re.split(r"(?<!\\)\|", lines[position].strip())[1:-1]
            if len(cells) == 2:
                rows.append((cells[0].strip(), cells[1].strip()))
            position += 1
    return rows


def fail_on_choices():
    """Valores declarados en cada `add_argument("--fail-on", choices=...)`, sin ejecutar nada."""
    choices = {}
    for script in sorted(ROOT.glob("*/scripts/*.py")):
        tree = ast.parse(script.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or getattr(node.func, "attr", "") != "add_argument":
                continue
            names = [arg.value for arg in node.args if isinstance(arg, ast.Constant)]
            if "--fail-on" not in names:
                continue
            values = set()
            for keyword in node.keywords:
                if keyword.arg == "choices" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                    values = {item.value for item in keyword.value.elts if isinstance(item, ast.Constant)}
            choices.setdefault(script.name, set()).update(values)
    return choices


class FailOnTableTests(unittest.TestCase):
    def test_table_matches_argument_choices(self):
        choices = fail_on_choices()
        documented = set()
        for values_cell, tools_cell in table_rows(INDEX_DOC.read_text(encoding="utf-8")):
            found = re.findall(r"`([^`]+)`", values_cell)
            if not found:
                continue
            values = {value.strip() for value in found[0].split("\\|")}
            tools = [
                tool for tool in re.findall(r"`([^`]+)`", tools_cell)
                if tool.split()[0].endswith(".py")
            ]
            for tool in tools:
                name = tool.split()[0]
                documented.add(name)
                with self.subTest(tool=name):
                    self.assertIn(name, choices, "la tabla cita un script sin --fail-on")
                    self.assertLessEqual(values, choices[name], "la tabla ofrece valores que el script no acepta")
                    # Un valor de más solo vale si la fila lo explica (el alias `warning`).
                    for extra in sorted(choices[name] - values):
                        self.assertIn("`%s`" % extra, tools_cell,
                                      "valor no documentado en la fila de %s" % name)
        self.assertEqual(documented, set(choices), "hay scripts con --fail-on fuera de la tabla")


class DocumentedTestCountsTests(unittest.TestCase):
    def test_documented_counts_match_discovery(self):
        for doc, (package, pattern) in DOC_TEST_COUNTS.items():
            text = (ROOT / doc).read_text(encoding="utf-8")
            declared = {int(number) for number in re.findall(pattern, text)}
            with self.subTest(doc=doc):
                self.assertTrue(declared, "el documento ya no declara recuento de tests")
                self.assertEqual(declared, {count_tests(package)},
                                 "el recuento documentado no coincide con los tests reales")


def count_tests(package):
    """Cuenta con el mismo descubrimiento que `run_tests.py`, en un proceso limpio.

    En este proceso los módulos `test_*` de otros paquetes ya están importados con
    el mismo nombre, así que descubrir en caliente choca con ellos.
    """
    start = ROOT / package / "tests"
    code = (
        "import sys, unittest;"
        "start = sys.argv[1];"
        "print(unittest.TestLoader().discover("
        "start, pattern='test_*.py', top_level_dir=start).countTestCases())"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(start)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    if result.returncode != 0:
        raise AssertionError("no se pudieron contar los tests de %s: %s" % (package, result.stderr.strip()))
    return int(result.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
