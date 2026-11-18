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

import ci_cost_scan  # noqa: E402

EXPENSIVE = """
name: Tests
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pip install -r requirements.txt
"""

CHEAP = """
name: Tests
on:
  push:
  pull_request:
concurrency:
  group: tests-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/cache@v4
        with:
          path: ~/.cache/uv
      - run: uv sync
"""

PUSH_ONLY = """
name: Release
on:
  push:
concurrency:
  group: release
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/cache@v4
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = ci_cost_scan.main(argv)
    return code, out.getvalue()


class TestCiCostScan(unittest.TestCase):

    def test_duplicate_suite_without_concurrency_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "tests.yml"
            target.write_text(EXPENSIVE, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            rules = [item["rule"] for item in report["findings"]]
            self.assertEqual(code, 1)
            self.assertIn("ci-doble-ejecucion", rules)
            self.assertIn("ci-sin-cache", rules)

    def test_cache_and_concurrency_are_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "tests.yml"
            target.write_text(CHEAP, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_single_trigger_does_not_flag_double_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "release.yml"
            target.write_text(PUSH_ONLY, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_fail_on_controls_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "ci.yml"
            target.write_text("name: Lint\non:\n  push:\njobs:\n  lint:\n    runs-on: ubuntu-latest\n",
                              encoding="utf-8")
            medium, _ = run(["--path", str(target), "--fail-on", "medium"])
            high, _ = run(["--path", str(target), "--fail-on", "high"])
            self.assertEqual((medium, high), (1, 0))

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe-esta-ruta"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
