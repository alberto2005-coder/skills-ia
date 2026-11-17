"""Aplica un parche de un solo fichero con dry-run por defecto y sandbox declarado.

Uso:
    py appsec-audit/scripts/apply_patch.py <fichero> --diff parche.diff [--apply --yes]
        [--sandbox <nombre>] [--verify "<comando>"] [--json]

Sin `--apply --yes` no se escribe nada: solo se comprueba que el parche aplica
limpio y se muestra el resultado. La verificación posterior ejecuta un comando,
y por eso exige `--sandbox` con un nombre declarado: sin ese contrato, el
comando no se lanza aunque se pida.

Código de salida: 0 correcto · 1 rechazado o verificación fallida · 2 ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


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


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Aplica un parche con dry-run por defecto.")
    parser.add_argument("file")
    parser.add_argument("--diff", required=True)
    parser.add_argument("--apply", action="store_true", help="Escribe el resultado")
    parser.add_argument("--yes", action="store_true", help="Confirmación explícita de la escritura")
    parser.add_argument("--sandbox", help="Contrato de sandbox donde se ejecuta la verificación")
    parser.add_argument("--verify", help="Comando de verificación posterior")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    target = Path(args.file)
    diff_path = Path(args.diff)
    if not target.is_file():
        print(f"No existe el fichero: {target}", file=sys.stderr)
        return 2
    if not diff_path.is_file():
        print(f"No existe el parche: {diff_path}", file=sys.stderr)
        return 2

    try:
        content = target.read_text(encoding="utf-8").splitlines(keepends=True)
        hunks = parse_hunks(diff_path.read_text(encoding="utf-8"))
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
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"RECHAZADO: el parche no aplica ({len(errors)} problema(s))")
            for error in errors:
                print(f"  - {error}")
        return 1

    if not args.apply:
        report["status"] = "dry-run"
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"DRY-RUN: el parche aplica limpio ({report['changed_lines']} línea(s) afectadas)")
            print("No se ha escrito nada. Para aplicarlo: --apply --yes")
        return 0

    if not args.yes:
        report["status"] = "refused"
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print("RECHAZADO: --apply exige confirmación explícita con --yes", file=sys.stderr)
        return 1

    if args.verify and not args.sandbox:
        report["status"] = "refused"
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print("RECHAZADO: la verificación ejecuta un comando y exige --sandbox declarado",
                  file=sys.stderr)
        return 1

    backup = target.with_suffix(target.suffix + ".orig")
    shutil.copyfile(target, backup)
    target.write_text(render(result), encoding="utf-8")
    report["status"] = "applied"
    report["backup"] = str(backup)

    if args.verify:
        completed = subprocess.run(
            args.verify, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
        report["verification"] = {
            "sandbox": args.sandbox,
            "returncode": completed.returncode,
            "output": (completed.stdout + completed.stderr).strip()[:2000],
        }
        report["status"] = "applied" if completed.returncode == 0 else "verification_failed"

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Aplicado en {target} (backup {backup.name})")
        if args.verify:
            verification = report["verification"]
            print(f"Verificación en sandbox «{verification['sandbox']}»: "
                  f"exit {verification['returncode']}")
            if verification["output"]:
                print(verification["output"])
    return 0 if report["status"] == "applied" else 1


if __name__ == "__main__":
    sys.exit(main())
