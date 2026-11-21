import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import flaky_scan  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "suite_inestable"


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = flaky_scan.main(argv)
    return code, out.getvalue()


def report(argv=None):
    code, output = run(["--root", str(FIXTURES), "--json"] + (argv or []))
    assert code in (0, 1)
    return json.loads(output)


class FlakyPatternTests(unittest.TestCase):
    def test_clean_suite_has_no_findings(self):
        code, output = run(["--root", str(FIXTURES), "--json", "--paths", str(FIXTURES / "test_limpio.py")])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["findings"], [])

    def test_every_pattern_is_detected(self):
        rules = {item["rule"] for item in report()["findings"]}
        self.assertEqual(rules, {
            "espera-fija", "reloj-de-pared", "aleatorio-sin-semilla", "red-real",
            "ruta-compartida", "estado-global", "bucle-sin-salida", "skip-permanente",
        })

    def test_sleep_is_medium_with_a_fix(self):
        sleeps = [item for item in report()["findings"] if item["rule"] == "espera-fija"]
        self.assertEqual(len(sleeps), 1)
        self.assertEqual(sleeps[0]["severity"], "medium")
        self.assertIn("fix", sleeps[0])
        self.assertEqual(sleeps[0]["line"], 12)

    def test_unseeded_random_and_real_network_are_high(self):
        severities = {item["rule"]: item["severity"] for item in report()["findings"]}
        self.assertEqual(severities["aleatorio-sin-semilla"], "high")
        self.assertEqual(severities["red-real"], "high")

    def test_seeded_random_is_not_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_semilla.py"
            path.write_text(
                "import random\n\nrandom.seed(7)\n\n\ndef test_uno():\n    assert random.randint(1, 9) >= 1\n",
                encoding="utf-8",
            )
            code, output = run(["--root", tmp, "--json", "--paths", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_allow_network_drops_the_network_rule(self):
        rules = {item["rule"] for item in report(["--allow-network"])["findings"]}
        self.assertNotIn("red-real", rules)
        self.assertIn("espera-fija", rules)

    def test_default_threshold_fails_on_high(self):
        code, _ = run(["--root", str(FIXTURES)])
        self.assertEqual(code, 1)

    def test_none_never_fails(self):
        code, _ = run(["--root", str(FIXTURES), "--fail-on", "none"])
        self.assertEqual(code, 0)

    def test_low_threshold_fails_on_the_skip(self):
        code, output = run(["--root", str(FIXTURES), "--fail-on", "low", "--json"])
        self.assertEqual(code, 1)
        self.assertIn("skip-permanente", {item["rule"] for item in json.loads(output)["findings"]})

    def test_report_counts_files_and_findings(self):
        data = report()
        self.assertEqual(data["source"], "flaky_scan")
        self.assertEqual(data["files"], 2)
        self.assertEqual(data["summary"]["total"], len(data["findings"]))
        self.assertEqual(data["summary"]["by_severity"]["high"], 2)

    def test_missing_root_and_path_exit_two(self):
        self.assertEqual(run(["--root", str(FIXTURES / "no-existe")])[0], 2)
        self.assertEqual(run(["--root", str(FIXTURES), "--paths", str(FIXTURES / "nada.py")])[0], 2)


if __name__ == "__main__":
    unittest.main()
