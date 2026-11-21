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

import contract_fixtures  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "contrato"
PROVIDER = str(FIXTURES / "provider.json")


def run(consumer, argv=None):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = contract_fixtures.main(
            ["--provider", PROVIDER, "--consumer", str(FIXTURES / consumer), "--json"] + (argv or [])
        )
    return code, out.getvalue()


def findings(consumer):
    code, output = run(consumer)
    assert code in (0, 1)
    return json.loads(output)


class ContractTests(unittest.TestCase):
    def test_matching_payload_is_clean(self):
        code, output = run("consumer_ok.json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["findings"], [])

    def test_missing_required_field_is_high(self):
        data = findings("consumer_roto.json")
        missing = [item for item in data["findings"] if item["rule"] == "campo-faltante"]
        self.assertEqual([item["message"].split("«")[1].split("»")[0] for item in missing], ["email"])
        self.assertEqual(missing[0]["severity"], "high")

    def test_scalar_type_drift_is_detected(self):
        data = findings("consumer_roto.json")
        drift = [item for item in data["findings"] if item["rule"] == "tipo-divergente"]
        self.assertTrue(any("«id»" in item["message"] for item in drift))

    def test_array_item_type_drift_is_detected(self):
        data = findings("consumer_roto.json")
        drift = [item for item in data["findings"] if item["rule"] == "tipo-divergente"]
        self.assertTrue(any("array<string>" in item["message"] for item in drift))

    def test_optional_field_may_be_absent_or_null(self):
        rules = {item["rule"] for item in findings("consumer_roto.json")["findings"]}
        self.assertNotIn("nulo-no-permitido", rules)
        self.assertNotIn("campo-faltante", {item["rule"] for item in findings("consumer_ok.json")["findings"]})

    def test_extra_field_is_low_and_does_not_break_the_default_gate(self):
        code, output = run("consumer_extra.json")
        data = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual([item["rule"] for item in data["findings"]], ["campo-extra"])
        self.assertEqual(data["findings"][0]["severity"], "low")

    def test_low_threshold_fails_on_the_extra(self):
        code, _ = run("consumer_extra.json", ["--fail-on", "low"])
        self.assertEqual(code, 1)

    def test_none_never_fails(self):
        code, _ = run("consumer_roto.json", ["--fail-on", "none"])
        self.assertEqual(code, 0)

    def test_report_shape_is_stable(self):
        data = findings("consumer_roto.json")
        self.assertEqual(data["source"], "contract_fixtures")
        self.assertEqual(data["files"], 2)
        self.assertEqual(data["summary"]["total"], len(data["findings"]))

    def test_missing_or_broken_input_exits_two(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = contract_fixtures.main(
                ["--provider", str(FIXTURES / "no-existe.json"), "--consumer", str(FIXTURES / "consumer_ok.json")]
            )
        self.assertEqual(code, 2)
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "roto.json"
            broken.write_text("{", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = contract_fixtures.main(["--provider", PROVIDER, "--consumer", str(broken)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
