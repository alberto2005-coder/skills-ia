# -*- coding: utf-8 -*-
"""Contrato de severidad: `checks` solo lleva la puerta y `findings` las dos escalas."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import analyze, checks, report  # noqa: E402

RISK_SCALE = {"critical", "high", "medium", "low"}
GATE_SCALE = {"must", "should", "nice"}


def known_ids():
    """Ids reales del catálogo, sin las claves de prefijo (las que acaban en `-`)."""
    return sorted(key for key in checks.CHECKS if not key.endswith("-"))


class CheckRecordTests(unittest.TestCase):
    def test_every_check_record_carries_only_the_gate_level(self):
        for check_id in known_ids():
            with self.subTest(check=check_id):
                record = checks.check(check_id, "fail", evidence="evidencia")
                self.assertNotIn("severity", record)
                self.assertIn(record["severity_level"], GATE_SCALE)

    def test_catalog_and_unknown_ids_use_the_same_shape(self):
        meta = checks.catalog("NO-EXISTE-999")
        self.assertNotIn("severity", meta)
        self.assertIn(meta["severity_level"], GATE_SCALE)
        record = checks.check("NO-EXISTE-999", "fail")
        self.assertNotIn("severity", record)
        self.assertIn(record["severity_level"], GATE_SCALE)

    def test_audit_payload_checks_do_not_carry_the_risk_key(self):
        payload = report.build_payload({
            "checks": [checks.check(check_id, "fail") for check_id in known_ids()],
            "findings": [],
        })
        self.assertTrue(payload["checks"])
        for record in payload["checks"]:
            self.assertNotIn("severity", record)
            self.assertIn(record.get("severity_level"), GATE_SCALE)


class FindingRecordTests(unittest.TestCase):
    def test_findings_declare_both_axes_on_their_own_scale(self):
        ids = known_ids()
        findings = analyze.to_findings([checks.check(check_id, "fail") for check_id in ids])
        self.assertEqual(len(findings), len(ids))
        for finding in findings:
            with self.subTest(finding=finding["id"]):
                self.assertIn("severity_level", finding)
                self.assertIn(finding["severity_level"], GATE_SCALE)
                self.assertIn(finding["severity"], RISK_SCALE)

    def test_finding_without_a_check_record_still_declares_the_gate(self):
        finding = analyze.to_findings([{"id": known_ids()[0], "status": "fail"}])[0]
        self.assertIn(finding["severity_level"], GATE_SCALE)
        self.assertIn(finding["severity"], RISK_SCALE)


if __name__ == "__main__":
    unittest.main()
