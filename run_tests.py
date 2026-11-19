"""Ejecuta todas las suites de pruebas del repositorio."""

import re
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
    total_tests = 0

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

        result = subprocess.run(
            command,
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)

        output = result.stdout + "\n" + result.stderr
        match = re.search(r"Ran (\d+) tests?", output)
        if match:
            total_tests += int(match.group(1))
        else:
            total_tests += len(re.findall(r"\.\.\.\s*(?:ok|FAIL|ERROR)", output))

        if result.returncode:
            failures.append((folder, result.returncode))

    total_suites = len(SUITES)
    passed_suites = total_suites - len(failures)

    print("\n" + "=" * 72)
    print(f"Resumen: {passed_suites}/{total_suites} suites ejecutadas con éxito.")
    print(f"Total ejecutado: {total_suites} suites y {total_tests} tests.")

    if failures:
        print(
            "Suites fallidas ({}): {}".format(
                len(failures),
                ", ".join(f"{name} (código {code})" for name, code in failures),
            )
        )
        return 1

    print("Todas las suites finalizaron correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
