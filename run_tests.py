"""Ejecuta todas las suites de pruebas del repositorio."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = (
    ("agent-red-team", "unittest"),
    ("api-contract-guard", "unittest"),
    ("appsec-audit", "unittest"),
    ("db-architect", "unittest"),
    ("docs-sync-engine", "unittest"),
    ("finops-auditor", "unittest"),
    ("humanizador-anti-ia", "unittest"),
    ("premium-web-designer", "custom"),
    ("refactor-surgeon", "unittest"),
    ("replica", "unittest"),
    ("seo-auditor", "unittest"),
    ("skill-evals", "unittest"),
    (".", "unittest"),
)


def main():
    failures = []

    for folder, runner in SUITES:
        test_dir = ROOT / folder / "tests" if folder != "." else ROOT / "tests"
        print("\n" + "=" * 72, flush=True)
        print("Suite: {}".format(test_dir.relative_to(ROOT)), flush=True)
        print("=" * 72, flush=True)

        if runner == "custom":
            command = [sys.executable, str(test_dir / "run_tests.py")]
        else:
            command = [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(test_dir),
                "-p",
                "test_*.py",
                "-v",
            ]

        result = subprocess.run(command, cwd=str(ROOT), check=False)
        if result.returncode:
            failures.append((folder, result.returncode))

    if failures:
        print("\nSuites fallidas: {}".format(
            ", ".join("{} (código {})".format(name, code) for name, code in failures)
        ))
        return 1

    print("\nTodas las suites finalizaron correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
