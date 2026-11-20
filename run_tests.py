"""Ejecuta todas las suites de pruebas del repositorio y sus puertas locales."""

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
# Puertas sin tests: comprobaciones que no cuentan casos pero rompen la entrega.
GATES = (("auditoría de documentación", "tests/audit_docs.py"),)

# Las suites imprimen emoji y acentos: la consola de Windows (cp1252) los rechaza y
# tumbaba el runner a mitad de la matriz. UTF-8 con reemplazo escribe siempre.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _banner(title):
    print("\n" + "=" * 72, flush=True)
    print(title, flush=True)
    print("=" * 72, flush=True)


def _command(folder, runner, test_dir):
    if runner == "custom":
        return [sys.executable, str(test_dir / "run_tests.py")]
    return [
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


def _run(command):
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result


def _plural(count, singular, plural):
    return singular if count == 1 else plural


def _count(output):
    """Tests anunciados por unittest, o puntos de progreso si no hubo resumen."""
    match = re.search(r"Ran (\d+) tests?", output)
    if match:
        return int(match.group(1))
    return len(re.findall(r"\.\.\.\s*(?:ok|FAIL|ERROR)", output))


def run_suite(folder, runner):
    """Ejecuta una suite y devuelve su código de salida y sus tests."""
    test_dir = ROOT / folder / "tests" if folder != "." else ROOT / "tests"
    _banner("Suite: {}".format(test_dir.relative_to(ROOT)))
    result = _run(_command(folder, runner, test_dir))
    return result.returncode, _count(result.stdout + "\n" + result.stderr)


def run_gate(label, script):
    """Ejecuta una puerta local y devuelve su etiqueta y código de salida."""
    _banner("Puerta: {}".format(script))
    result = _run([sys.executable, str(ROOT / script)])
    return label, result.returncode


def main():
    failures = []
    total_tests = 0

    for folder, runner in SUITES:
        code, tests = run_suite(folder, runner)
        total_tests += tests
        if code:
            failures.append((folder, code))

    gate_failures = []
    for label, script in GATES:
        name, code = run_gate(label, script)
        if code:
            gate_failures.append((name, code))

    total_suites = len(SUITES)
    passed_suites = total_suites - len(failures)
    total_gates = len(GATES)
    passed_gates = total_gates - len(gate_failures)

    print("\n" + "=" * 72)
    print(
        f"Resumen: {passed_suites}/{total_suites} suites y "
        f"{passed_gates}/{total_gates} puertas ejecutadas con éxito."
    )
    print(
        f"Total ejecutado: {total_suites} suites, {total_gates} "
        f"{_plural(total_gates, 'puerta', 'puertas')} y {total_tests} tests."
    )

    if failures or gate_failures:
        broken = failures + gate_failures
        print(
            "Suites o puertas fallidas ({}): {}".format(
                len(broken),
                ", ".join(f"{name} (código {code})" for name, code in broken),
            )
        )
        return 1

    print("Todas las suites y puertas finalizaron correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
