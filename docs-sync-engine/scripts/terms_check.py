"""Revisa la terminología de la documentación contra un glosario aceptado/rechazado.

Uso:
    py docs-sync-engine/scripts/terms_check.py --path docs/ \\
        --accept accept.txt --reject reject.txt [--json] [--fail-on low|medium|none]

`reject.txt` admite una línea por término, o `malo => bueno` para sugerir el
reemplazo. `accept.txt` fija la grafía canónica: el término se busca sin
distinguir mayúsculas y se avisa si aparece con otra. El texto dentro de bloques
y de `código en línea` se ignora.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado ·
2 ruta o glosario ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
FENCE = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")


def glossary(path: Path | None) -> list[tuple[str, str]]:
    if path is None:
        return []
    entries = []
    # `utf-8-sig` quita el BOM (que se colaba como parte del primer término) y
    # `errors="replace"` evita el traceback con un glosario en latin-1.
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=>" in line:
            bad, good = (part.strip() for part in line.split("=>", 1))
            entries.append((bad, good))
        else:
            entries.append((line, ""))
    return entries


def visible_text(markdown: str) -> str:
    """Quita código sin mover las líneas: los bloques se sustituyen por sus saltos."""
    without_fences = FENCE.sub(lambda match: "\n" * match.group(0).count("\n"), markdown)
    return INLINE_CODE.sub("", without_fences)


def markdown_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(item for item in root.rglob("*.md") if item.is_file())


def check(root: Path, accepted: list[tuple[str, str]], rejected: list[tuple[str, str]]) -> list[dict]:
    findings = []
    for path in markdown_files(root):
        original = path.read_text(encoding="utf-8-sig", errors="replace")
        text = visible_text(original)
        lines = text.splitlines()
        for term, replacement in rejected:
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.I)
            for number, line in enumerate(lines, 1):
                if not pattern.search(line):
                    continue
                suggestion = f"; usa {replacement}" if replacement else ""
                findings.append({
                    "file": path.as_posix(),
                    "line": number,
                    "rule": "termino-rechazado",
                    "severity": "medium",
                    "term": term,
                    "message": f"«{term}» está en la lista de rechazados{suggestion}",
                })
        for term, _ in accepted:
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.I)
            exact = re.compile(rf"\b{re.escape(term)}\b")
            for number, line in enumerate(lines, 1):
                match = pattern.search(line)
                if match and not exact.search(line):
                    found = match.group(0)
                    findings.append({
                        "file": path.as_posix(),
                        "line": number,
                        "rule": "grafia-no-canonica",
                        "severity": "low",
                        "term": term,
                        "found": found,
                        "message": f"«{found}» aparece con otra grafía; la canónica es «{term}»",
                    })
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Glosario aceptado/rechazado sobre Markdown.")
    parser.add_argument("--path", required=True, help="fichero o carpeta Markdown")
    parser.add_argument("--accept", help="fichero con términos aceptados (grafía canónica)")
    parser.add_argument("--reject", help="fichero con términos rechazados, o «malo => bueno»")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="medium", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2
    try:
        accepted = glossary(Path(args.accept)) if args.accept else []
        rejected = glossary(Path(args.reject)) if args.reject else []
    except OSError as error:
        print(f"glosario ilegible: {error}")
        return 2

    findings = check(target, accepted, rejected)
    by_rule = {rule: sum(1 for item in findings if item["rule"] == rule)
               for rule in ("termino-rechazado", "grafia-no-canonica")}
    if args.json:
        print(json.dumps({"findings": findings, "by_rule": by_rule}, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"[{item['severity']}] {item['file']}:{item['line']} {item['rule']}: {item['message']}")
        print(f"hallazgos: {len(findings)}")
    if args.fail_on == "none":
        return 0
    floor = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= floor for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
