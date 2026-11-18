import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import hotspots  # noqa: E402

GIT = shutil.which("git")


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = hotspots.main(argv)
    return code, out.getvalue()


def commit(repo, message, date):
    env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
           "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@example.com"}
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True, env=env)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", message], check=True,
                   capture_output=True, env=env)


def make_repo(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)


@unittest.skipUnless(GIT, "git no está disponible")
class TestHotspots(unittest.TestCase):

    def _repo(self, tmp):
        repo = Path(tmp) / "repo"
        repo.mkdir()
        make_repo(repo)
        (repo / "app.py").write_text("def uno():\n    return 1\n", encoding="utf-8")
        commit(repo, "uno", "2026-01-01T10:00:00+00:00")
        (repo / "app.py").write_text(
            "def uno(x):\n    if x:\n        return 1\n    return 2\n", encoding="utf-8")
        commit(repo, "dos", "2026-01-02T10:00:00+00:00")
        return repo

    def test_missing_since_is_not_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 2)
            self.assertFalse(report["measured"])
            self.assertIn("--since", report["reason"])

    def test_not_a_repository_is_not_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, output = run(["--path", tmp, "--since", "2026-01-01T00:00:00", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 2)
            self.assertFalse(report["measured"])

    def test_churn_and_complexity_are_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            code, output = run(["--path", str(repo), "--since", "2026-01-01T00:00:00", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertTrue(report["measured"])
            self.assertEqual(report["commits"], 2)
            top = report["files"][0]
            self.assertEqual(top["path"], "app.py")
            self.assertGreaterEqual(top["churn"], 4)
            self.assertGreaterEqual(top["complexity"], 2)
            self.assertEqual(top["score"], top["churn"] * top["complexity"])

    def test_since_filters_old_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            code, output = run(["--path", str(repo), "--since", "2027-01-01T00:00:00", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["files"], [])
            self.assertEqual(report["commits"], 0)

    def test_scores_sort_and_top_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            (repo / "big.py").write_text(
                "def f(x):\n    if x:\n        for i in x:\n            while i:\n                i -= 1\n    return 0\n",
                encoding="utf-8")
            commit(repo, "big", "2026-01-03T10:00:00+00:00")
            code, output = run(["--path", str(repo), "--since", "2026-01-01T00:00:00", "--top", "1", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(len(report["files"]), 1)
            self.assertEqual(report["files"][0]["path"], "big.py")
            self.assertGreaterEqual(report["total_files"], 2)

    def test_fail_on_hotspot_uses_the_min_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            code, _ = run(["--path", str(repo), "--since", "2026-01-01T00:00:00",
                           "--fail-on", "hotspot", "--min-score", "1"])
            self.assertEqual(code, 1)

    def test_shallow_clone_is_not_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            clone = Path(tmp) / "clone"
            subprocess.run(["git", "clone", "-q", "--depth", "1",
                            f"file://{repo.as_posix()}", str(clone)],
                           check=True, capture_output=True)
            code, output = run(["--path", str(clone), "--since", "2026-01-01T00:00:00", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 2)
            self.assertFalse(report["measured"])
            self.assertIn("shallow", report["reason"])


if __name__ == "__main__":
    unittest.main()
