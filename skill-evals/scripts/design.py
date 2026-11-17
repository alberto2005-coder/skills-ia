"""Diseña y valida el conjunto de casos de evaluación de una skill.

Uso:
    py skill-evals/scripts/design.py --from-phrases tests/phrases.json --out casos.json
    py skill-evals/scripts/design.py --from-phrases tests/phrases.json --check
    py skill-evals/scripts/design.py --check --cases casos.json

Genera casos deterministas desde `tests/phrases.json` (positivas, negativas con
ganadora esperada, fuera de dominio y límites), los reparte 60/40 en train/test
por hash del id y comprueba esquema y cobertura: toda skill del catálogo debe
tener al menos una positiva. Sin red, sin modelo y sin reloj.

Código de salida: 0 correcto · 1 problemas de validación · 2 entrada ilegible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evalkit  # noqa: E402


def _read(path: Path) -> dict:
    try:
        return evalkit.read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"no se pudo leer {path}: {error}") from error


def _write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _summary(document: dict) -> dict:
    cases = document["cases"]
    skills = {case["expect"] for case in cases if case.get("expect")}
    return {
        "cases": len(cases),
        "skills": len(skills),
        "train": sum(1 for case in cases if case["split"] == "train"),
        "test": sum(1 for case in cases if case["split"] == "test"),
        "by_kind": {
            kind: sum(1 for case in cases if case["kind"] == kind)
            for kind in evalkit.KINDS
        },
    }


def main(argv: list[str] | None = None) -> int:
    evalkit.force_utf8_output()
    parser = argparse.ArgumentParser(description="Diseña y valida casos de evaluación.")
    parser.add_argument("--from-phrases", help="phrases.json del repositorio")
    parser.add_argument("--out", help="fichero de casos a escribir")
    parser.add_argument("--cases", help="fichero de casos existente para --check")
    parser.add_argument("--threshold", type=float, default=evalkit.DEFAULT_THRESHOLD)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    _, router = evalkit.load_router()

    if args.cases:
        document = _read(Path(args.cases))
        problems = evalkit.validate_cases(document, router.names)
        if problems and not args.check:
            for problem in problems:
                print(f"  - {problem}")
            return 1
    elif args.from_phrases:
        try:
            phrases = _read(Path(args.from_phrases))
            document = evalkit.build_cases(phrases, args.threshold)
        except (KeyError, ValueError) as error:
            print(f"phrases inválido: {error}")
            return 2
        problems = evalkit.validate_cases(document, router.names)
    else:
        parser.error("indica --from-phrases o --cases")
        return 2

    summary = _summary(document)
    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems, "summary": summary},
                         indent=2, ensure_ascii=False))
    else:
        print(f"casos: {summary['cases']} · skills: {summary['skills']} · "
              f"train/test: {summary['train']}/{summary['test']}")
        print("por tipo: " + ", ".join(f"{kind}={count}" for kind, count in summary["by_kind"].items()))
        if problems:
            for problem in problems:
                print(f"  - {problem}")

    if args.check and args.from_phrases:
        if args.out:
            parser.error("--check no escribe; quita --out")
        return 0 if not problems else 1

    if args.out:
        if problems:
            print("no se escribe un conjunto inválido")
            return 1
        _write(Path(args.out), document)
        print(f"escrito: {args.out}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
