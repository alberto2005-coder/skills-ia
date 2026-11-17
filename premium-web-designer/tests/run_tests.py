import sys
import json
import unittest

from datetime import datetime, timezone
from pathlib import Path

from config import REPORT_DIR, TEST_DIR, ensure_report_directory


class TestResult(unittest.TextTestResult):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.details = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.details.append({
            "test": str(test),
            "status": "PASS",
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.details.append({
            "test": str(test),
            "status": "FAIL",
            "error": self._exc_info_to_string(err, test),
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.details.append({
            "test": str(test),
            "status": "ERROR",
            "error": self._exc_info_to_string(err, test),
        })

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.details.append({
            "test": str(test),
            "status": "SKIP",
            "reason": reason,
        })


def main():

    ensure_report_directory()

    print("\n" + "=" * 60)
    print(" PREMIUM WEB DESIGNER - AUTOMATED TEST SUITE")
    print("=" * 60)

    loader = unittest.TestLoader()

    suite = loader.discover(
        start_dir=str(TEST_DIR),
        pattern="test_*.py",
        top_level_dir=str(TEST_DIR),
    )

    runner = unittest.TextTestRunner(
        verbosity=2,
        resultclass=TestResult,
    )

    result = runner.run(suite)

    total = result.testsRun
    passed = len(result.successes) if hasattr(
        result, "successes"
    ) else sum(
        item["status"] == "PASS"
        for item in result.details
    )

    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)

    score = round(
        (passed / total) * 100, 2
    ) if total else 0

    if errors or failed:
        verdict = "FAIL"
    elif skipped:
        verdict = "PASS WITH SKIPPED TESTS"
    else:
        verdict = "PASS"

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    report = {
        "project": "Premium Web Designer",
        "version": "2.0.0",
        "timestamp": timestamp,
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "score": score,
        "verdict": verdict,
        "tests": result.details,
    }

    json_path = REPORT_DIR / "test-report.json"
    txt_path = REPORT_DIR / "test-report.txt"

    json_path.write_text(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )

    lines = [
        "PREMIUM WEB DESIGNER - TEST REPORT",
        "=" * 45,
        f"Date: {timestamp}",
        f"Total tests: {total}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Errors: {errors}",
        f"Skipped: {skipped}",
        f"Score: {score}%",
        f"Verdict: {verdict}",
        "",
        "INDIVIDUAL RESULTS",
        "-" * 45,
    ]

    for item in result.details:
        lines.append(
            f"[{item['status']}] {item['test']}"
        )

        if "error" in item:
            lines.append(item["error"])

    txt_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print(" FINAL RESULTS")
    print("=" * 60)

    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Errors:  {errors}")
    print(f"Skipped: {skipped}")
    print(f"Score:   {score}%")
    print(f"Verdict: {verdict}")

    print("\nReports generated:")
    print(json_path)
    print(txt_path)

    print("=" * 60)

    return 0 if not failed and not errors else 1


if __name__ == "__main__":
    sys.exit(main())