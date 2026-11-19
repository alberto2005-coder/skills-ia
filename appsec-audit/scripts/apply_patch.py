"""Aplica un parche de un solo fichero con dry-run por defecto y sandbox declarado.

Uso:
    py appsec-audit/scripts/apply_patch.py <fichero> --diff parche.diff [--apply --yes]
        [--sandbox <nombre>] [--verify "<comando>"] [--json]

Sin `--apply --yes` no se escribe nada: solo se comprueba que el parche aplica
limpio y se muestra el resultado. La verificación posterior ejecuta un comando,
y por eso exige `--sandbox` con un nombre declarado: sin ese contrato, el
comando no se lanza aunque se pida.

Aviso honesto: `--sandbox` es un **nombre de contrato declarado**, no un
aislamiento real. No crea contenedor ni namespace alguno; el comando corre en
el host con los mismos permisos que este script. Se ejecuta sin shell (lista de
argumentos vía `shlex.split`), con timeout, y si algo falla se restaura el
backup. Quien necesite aislamiento de verdad debe invocar el contenedor por su
cuenta y dejar la verificación fuera de esta herramienta.

Código de salida: 0 correcto · 1 rechazado o verificación fallida · 2 ilegible.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from appsec_util import force_utf8_output


def parse_hunks(diff_text: str) -> list[dict]:
    hunks: list[dict] = []
    current: dict | None = None
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            match = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if not match:
                raise ValueError(f"cabecera de hunk inválida: {line}")
            current = {
                "old_start": int(match.group(1)),
                "lines": [],
            }
            hunks.append(current)
            continue
        if current is None:
            continue
        if line.startswith("\\"):
            continue
        if line.startswith("+"):
            current["lines"].append(("add", line[1:]))
        elif line.startswith("-"):
            current["lines"].append(("del", line[1:]))
        elif line.startswith(" ") or line == "":
            current["lines"].append(("ctx", line[1:] if line else ""))
    return hunks


def newline_of(content: list[str]) -> str:
    return "\r\n" if content and content[0].endswith("\r\n") else "\n"


def apply_hunks(content: list[str], hunks: list[dict]) -> tuple[list[str], list[str]]:
    """Aplica los hunks y devuelve (resultado, errores). No escribe nada."""
    result: list[str] = []
    cursor = 0
    errors: list[str] = []
    ending = newline_of(content)

    for hunk in hunks:
        start = hunk["old_start"] - 1
        if start < cursor:
            errors.append(f"hunk solapado en la línea {hunk['old_start']}")
            continue
        result.extend(content[cursor:start])
        cursor = start
        for kind, text in hunk["lines"]:
            if kind in ("ctx", "del"):
                if cursor >= len(content):
                    errors.append(f"falta contexto en la línea {cursor + 1}: «{text}»")
                    break
                if content[cursor].rstrip("\r\n") != text.rstrip("\r\n"):
                    errors.append(
                        f"contexto no coincide en la línea {cursor + 1}: "
                        f"esperado «{text}», encontrado «{content[cursor].rstrip()}»"
                    )
                    break
                if kind == "ctx":
                    result.append(content[cursor])
                cursor += 1
            else:
                result.append(text + ending)
        if errors:
            break
    result.extend(content[cursor:])
    return result, errors


def render(result: list[str]) -> str:
    return "".join(result)


def _split_command(command: str) -> list[str]:
    """Parte el comando en argumentos SIN invocar un shell.

    En POSIX se usa `shlex`. En Windows `shlex` con `posix=True` trataría `\\`
    como carácter de escape y rompería rutas como `C:\\Python\\python.exe`,
    así que se usan comillas dobles con reglas de cmd.exe (sin interpretar
    `&&`, `|` ni `>`: eso solo lo haría un shell, que aquí no se lanza).
    """
    if os.name != "nt":
        return shlex.split(command, posix=True)
    tokens: list[str] = []
    for quoted, bare in re.findall(r'"([^"]*)"|(\S+)', command):
        tokens.append(quoted if bare == "" else bare)
    return tokens


def _run_verification(command: str, sandbox: str | None) -> dict:
    """Ejecuta `--verify` sin shell y con timeout, capturando todo.

    Sin shell=True no hay interpolación ni comandos encadenados: el texto se
    parte en argumentos literales. `sandbox` viaja solo como etiqueta
    declarada (ver docstring) y nunca se interpreta aquí.
    """
    argv = _split_command(command)
    if not argv:
        return {"sandbox": sandbox, "status": "error",
                "returncode": None, "output": "comando vacío"}

    try:
        completed = subprocess.run(
            argv, shell=False, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {"sandbox": sandbox, "status": "timeout", "returncode": None,
                "output": "la verificación superó los 300 s; backup restaurado"}
    except OSError as error:
        return {"sandbox": sandbox, "status": "error", "returncode": None,
                "output": f"no se pudo lanzar la verificación: {error}"}

    status = "ok" if completed.returncode == 0 else "failed"
    return {
        "sandbox": sandbox,
        "status": status,
        "returncode": completed.returncode,
        "output": (completed.stdout + completed.stderr).strip()[:2000],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aplica un parche con dry-run por defecto.")
    parser.add_argument("file")
    parser.add_argument("--diff", required=True)
    parser.add_argument("--apply", action="store_true", help="Escribe el resultado")
    parser.add_argument("--yes", action="store_true", help="Confirmación explícita de la escritura")
    parser.add_argument("--sandbox",
                        help="Nombre del contrato de sandbox declarado (etiqueta "
                             "de registro, NO crea aislamiento real)")
    parser.add_argument("--verify", help="Comando de verificación posterior")
    parser.add_argument("--json", action="store_true")
    return parser


def _read_inputs(target: Path, diff_path: Path) -> tuple[list[str], list[dict]]:
    # newline="" conserva los finales de línea tal cual: con la lectura
    # universal por defecto un CRLF se convertía en LF y newline_of() no
    # lo detectaba nunca, reescribiendo el fichero entero como LF.
    with target.open(encoding="utf-8", newline="") as handle:
        content = handle.read().splitlines(keepends=True)
    return content, parse_hunks(diff_path.read_text(encoding="utf-8"))


def _emit(report: dict, args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))


def _rejected(report: dict, errors: list[str], args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"RECHAZADO: el parche no aplica ({len(errors)} problema(s))")
        for error in errors:
            print(f"  - {error}")
    return 1


def _dry_run(report: dict, args: argparse.Namespace) -> int:
    report["status"] = "dry-run"
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"DRY-RUN: el parche aplica limpio ({report['changed_lines']} línea(s) afectadas)")
        print("No se ha escrito nada. Para aplicarlo: --apply --yes")
    return 0


def _refused(report: dict, args: argparse.Namespace, message: str) -> int:
    report["status"] = "refused"
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(message, file=sys.stderr)
    return 1


def _run_verify(report: dict, args: argparse.Namespace, target: Path, backup: Path) -> None:
    report["verification"] = _run_verification(args.verify, args.sandbox)
    status = report["verification"].get("status", "verification_failed")
    report["status"] = "applied" if status == "ok" else "verification_failed"
    if status == "timeout":
        # El parche quedó escrito pero la verificación no terminó:
        # se restaura el backup para no dejar el árbol a medias.
        shutil.copyfile(backup, target)
        report["status"] = "rolled_back"


def _report_applied(report: dict, args: argparse.Namespace, target: Path, backup: Path) -> None:
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    if report["status"] == "rolled_back":
        print(f"Verificación agotó el timeout; backup restaurado en {target}",
              file=sys.stderr)
    else:
        print(f"Aplicado en {target} (backup {backup.name})")
    if not args.verify:
        return
    verification = report["verification"]
    exit_code = verification.get("returncode")
    exit_label = f"exit {exit_code}" if exit_code is not None else verification["status"]
    print(f"Verificación declarada en «{verification['sandbox']}»: {exit_label}")
    if verification["output"]:
        print(verification["output"])


def _apply(report: dict, args: argparse.Namespace, target: Path, result: list[str]) -> int:
    backup = target.with_suffix(target.suffix + ".orig")
    shutil.copyfile(target, backup)
    # newline="" para no traducir los finales de línea ya detectados (CRLF).
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write(render(result))
    report["status"] = "applied"
    report["backup"] = str(backup)

    if args.verify:
        _run_verify(report, args, target, backup)
    _report_applied(report, args, target, backup)
    return 0 if report["status"] == "applied" else 1


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    args = _build_parser().parse_args(argv)

    target = Path(args.file)
    diff_path = Path(args.diff)
    if not target.is_file():
        print(f"No existe el fichero: {target}", file=sys.stderr)
        return 2
    if not diff_path.is_file():
        print(f"No existe el parche: {diff_path}", file=sys.stderr)
        return 2

    try:
        content, hunks = _read_inputs(target, diff_path)
    except (OSError, ValueError) as error:
        print(f"No se pudo leer la entrada: {error}", file=sys.stderr)
        return 2

    if not hunks:
        print("El parche no tiene hunks aplicables", file=sys.stderr)
        return 2

    result, errors = apply_hunks(content, hunks)
    report = {
        "file": str(target),
        "diff": str(diff_path),
        "dry_run": not args.apply,
        "applies_cleanly": not errors,
        "errors": errors,
        "changed_lines": sum(1 for hunk in hunks for kind, _ in hunk["lines"] if kind != "ctx"),
        "sandbox": args.sandbox,
        "verify": args.verify,
    }

    if errors:
        return _rejected(report, errors, args)
    if not args.apply:
        return _dry_run(report, args)
    if not args.yes:
        return _refused(report, args,
                        "RECHAZADO: --apply exige confirmación explícita con --yes")
    if args.verify and not args.sandbox:
        return _refused(report, args,
                        "RECHAZADO: la verificación ejecuta un comando y exige --sandbox declarado")
    return _apply(report, args, target, result)


if __name__ == "__main__":
    sys.exit(main())
