import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ab"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ab_compare  # noqa: E402


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = ab_compare.main(list(args))
    return code, out.getvalue()


def compare(*args):
    code, output = run("--a", str(FIXTURES / "control.json"), "--b", str(FIXTURES / "variante.json"), "--json", *args)
    return code, json.loads(output)


def report(**data):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    handle.write(json.dumps(data))
    handle.close()
    return handle.name


class AbTests(unittest.TestCase):
    def test_effectiveness_counts_every_sample(self):
        _, payload = compare()
        self.assertEqual(payload["a"]["effectiveness"], 0.75)
        self.assertEqual(payload["b"]["effectiveness"], 1.0)

    def test_compliance_only_uses_mandatory_cases(self):
        _, payload = compare()
        self.assertEqual(payload["a"]["compliance"], 0.5)
        self.assertEqual(payload["b"]["compliance"], 1.0)

    def test_cost_and_latency_are_means_per_sample(self):
        _, payload = compare()
        self.assertAlmostEqual(payload["a"]["cost"], 0.00185, places=6)
        self.assertAlmostEqual(payload["a"]["latency"], 115.0, places=6)
        self.assertAlmostEqual(payload["b"]["cost"], 0.003575, places=6)

    def test_variability_is_the_mean_case_deviation(self):
        _, payload = compare()
        self.assertAlmostEqual(payload["a"]["variability"], 0.015, places=6)
        self.assertAlmostEqual(payload["b"]["variability"], 0.0075, places=6)

    def test_variability_is_null_without_repeats(self):
        path = report(label="unica", cases=[{"id": "c1", "samples": [{"passed": True, "score": 0.9}]}])
        document, error = ab_compare.read(path)
        self.assertIsNone(error)
        normalized, error = ab_compare.normalize(document, path)
        self.assertIsNone(error)
        self.assertIsNone(ab_compare.metrics(normalized)["variability"])

    def test_flat_samples_group_by_case_id(self):
        path = report(label="plana", cases=[
            {"id": "c1", "passed": True, "score": 0.9},
            {"id": "c1", "passed": False, "score": 0.7},
        ])
        document, _ = ab_compare.read(path)
        normalized, error = ab_compare.normalize(document, path)
        self.assertIsNone(error)
        self.assertEqual(len(normalized["cases"]["c1"]["samples"]), 2)
        self.assertEqual(ab_compare.metrics(normalized)["effectiveness"], 0.5)

    def test_deltas_point_from_a_to_b(self):
        _, payload = compare()
        self.assertEqual(payload["delta"]["effectiveness"], 0.25)
        self.assertEqual(payload["delta"]["compliance"], 0.5)
        self.assertGreater(payload["delta"]["cost_pct"], 0)

    def test_identical_runs_have_zero_delta(self):
        code, output = run("--a", str(FIXTURES / "control.json"), "--b", str(FIXTURES / "control.json"), "--json")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(payload["delta"]["effectiveness"], 0)
        self.assertEqual(payload["delta"]["cost_pct"], 0)

    def test_cost_gate_fails_the_comparison(self):
        code, payload = compare("--max-cost-increase", "20")
        self.assertEqual(code, 1)
        self.assertEqual(payload["verdict"], "fail")
        self.assertEqual(payload["gates"][0]["gate"], "max-cost-increase")

    def test_generous_gates_pass(self):
        code, payload = compare("--max-cost-increase", "200", "--max-latency-increase", "100")
        self.assertEqual(code, 0)
        self.assertEqual(payload["verdict"], "pass")

    def test_min_effectiveness_gate_uses_points(self):
        code, _ = compare("--min-effectiveness-delta", "30")
        self.assertEqual(code, 1)

    def test_cases_only_in_one_run_are_listed(self):
        path = report(label="otra", cases=[{"id": "solo-b", "samples": [{"passed": True, "score": 1.0}]}])
        _, output = run("--a", str(FIXTURES / "control.json"), "--b", path, "--json")
        self.assertEqual(json.loads(output)["only_in_b"], ["solo-b"])

    def test_invalid_json_exits_two(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        handle.write("{no es json")
        handle.close()
        code, _ = run("--a", handle.name, "--b", str(FIXTURES / "variante.json"))
        self.assertEqual(code, 2)

    def test_missing_cases_exits_two(self):
        path = report(label="vacia", metrics={})
        code, _ = run("--a", path, "--b", str(FIXTURES / "variante.json"))
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
