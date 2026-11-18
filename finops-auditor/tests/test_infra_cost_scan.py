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

import infra_cost_scan  # noqa: E402

BUCKET_WITHOUT_LIFECYCLE = '''
resource "aws_s3_bucket" "logs" {
  bucket = "logs-sin-ciclo"
}
'''

BUCKET_WITH_LIFECYCLE = '''
resource "aws_s3_bucket" "logs" {
  bucket = "logs-con-ciclo"

  lifecycle_rule {
    enabled = true
  }
}
'''

DEPLOY_WITHOUT_LIMITS = """
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: api
          image: api:1.0
"""

DEPLOY_WITH_LIMITS = DEPLOY_WITHOUT_LIMITS + """          resources:
            limits:
              cpu: 500m
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = infra_cost_scan.main(argv)
    return code, out.getvalue()


class TestInfraCostScan(unittest.TestCase):

    def test_bucket_without_lifecycle_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "storage.tf"
            target.write_text(BUCKET_WITHOUT_LIFECYCLE, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual([item["rule"] for item in report["findings"]], ["s3-sin-ciclo-de-vida"])
            self.assertEqual(report["findings"][0]["severity"], "high")

    def test_bucket_with_lifecycle_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "storage.tf"
            target.write_text(BUCKET_WITH_LIFECYCLE, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_containers_without_limits_are_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "deploy.yaml"
            target.write_text(DEPLOY_WITHOUT_LIMITS, encoding="utf-8")
            code, output = run(["--path", str(target), "--json", "--fail-on", "medium"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["findings"][0]["rule"], "contenedor-sin-limites")
            self.assertEqual(report["findings"][0]["severity"], "medium")

    def test_containers_with_limits_are_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "deploy.yaml"
            target.write_text(DEPLOY_WITH_LIMITS, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_directory_scan_counts_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "a.tf").write_text(BUCKET_WITHOUT_LIFECYCLE, encoding="utf-8")
            (folder / "b.yaml").write_text(DEPLOY_WITH_LIMITS, encoding="utf-8")
            code, output = run(["--path", str(folder), "--json", "--fail-on", "high"])
            report = json.loads(output)
            self.assertEqual((code, report["files"]), (1, 2))

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe-esta-ruta"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
