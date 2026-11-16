#!/usr/bin/env python3
"""parity.py - Puntua la paridad funcional de tu clon frente al mapa de la app original.

Acepta features.csv o features.json.

CSV:  id,area,priority,feature,status,notes
JSON: {"features": [{"id": "...", "area": "...", "priority": "must", ...}]}

priority: must | should | could
status:   done | partial | missing | out_of_scope

Pesos must=3, should=2, could=1. partial cuenta 0.5. out_of_scope sale del denominador.
Hay un must que no este done (aunque sea partial) => NO es desplegable.

Uso:
    python parity.py replica/features.csv
    python parity.py replica/features.json --json
    python parity.py replica/features.csv --markdown --out replica/parity.md

Codigo de salida: 0 desplegable, 1 faltan must, 2 error de lectura.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WEIGHTS = {"must": 3, "should": 2, "could": 1}
DONE = {"done", "complete", "completed", "yes", "y", "1", "true", "hecho", "listo", "finalizado"}
PARTIAL = {"partial", "wip", "in-progress", "in_progress", "half", "parcial", "en curso", "en_progreso"}
OUT = {
    "out_of_scope", "out-of-scope", "outofscope", "excluded", "skip", "skipped",
    "n/a", "na", "fuera de alcance", "fuera_de_alcance", "fuera",
}
MISSING = {"missing", "todo", "no", "0", "false", "pending", "pendiente", "falta"}

COMPLETION = {**{s: 1.0 for s in DONE}, **{s: 0.5 for s in PARTIAL}, **{s: 0.0 for s in MISSING}}


def normalize(value: str | None, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip().lower()


def normalize_row(raw: dict) -> dict:
    row = {normalize(k): v for k, v in raw.items() if k is not None}
    priority = normalize(row.get("priority") or row.get("prio") or row.get("prioridad"))
    if priority in {"m", "must-have", "must_have", "imprescindible"}:
        priority = "must"
    elif priority in {"s", "should-have", "should_have", "recomendado"}:
        priority = "should"
    elif priority in {"c", "could-have", "could_have", "opcional", "nice"}:
        priority = "could"
    if priority not in WEIGHTS:
        priority = "should"

    status = normalize(row.get("status") or row.get("estado"))
    if status in OUT:
        status = "out_of_scope"
    elif status in DONE:
        status = "done"
    elif status in PARTIAL:
        status = "partial"
    elif status in MISSING:
        status = "missing"
    else:
        status = "missing"

    return {
        "id": str(row.get("id") or row.get("feature") or "").strip(),
        "area": str(row.get("area") or row.get("module") or row.get("modulo") or "general").strip() or "general",
        "feature": str(row.get("feature") or row.get("name") or row.get("nombre") or "").strip(),
        "priority": priority,
        "status": status,
    }


def load(path: str) -> list[dict]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
        raw_rows = data.get("features", data) if isinstance(data, dict) else data
        if not isinstance(raw_rows, list):
            raise ValueError("El JSON debe ser una lista o tener la clave 'features'")
        return [normalize_row(r) for r in raw_rows]
    if ext in {".csv", ".tsv"}:
        delimiter = "\t" if ext == ".tsv" else ","
        with open(path, encoding="utf-8-sig", newline="") as fh:
            return [normalize_row(r) for r in csv.DictReader(fh, delimiter=delimiter)]
    raise ValueError("Formato no soportado: usa .csv, .tsv o .json")


def analyze(rows: list[dict]) -> dict:
    scoped = [r for r in rows if r["status"] != "out_of_scope"]
    total_weight = sum(WEIGHTS[r["priority"]] for r in scoped)
    score = (
        sum(WEIGHTS[r["priority"]] * COMPLETION[r["status"]] for r in scoped) / total_weight * 100
        if total_weight
        else 0.0
    )

    must_gaps = [
        r for r in scoped if r["priority"] == "must" and COMPLETION[r["status"]] < 1.0
    ]
    must_total = sum(1 for r in scoped if r["priority"] == "must")

    by_priority = {}
    for prio in ("must", "should", "could"):
        group = [r for r in scoped if r["priority"] == prio]
        weight = sum(WEIGHTS[p] for p in [prio] * len(group))
        done = sum(1 for r in group if r["status"] == "done")
        partial = sum(1 for r in group if r["status"] == "partial")
        pct = (
            sum(WEIGHTS[prio] * COMPLETION[r["status"]] for r in group) / weight * 100
            if weight
            else None
        )
        by_priority[prio] = {
            "total": len(group), "done": done, "partial": partial, "percent": pct,
        }

    areas: dict[str, dict] = {}
    for row in scoped:
        bucket = areas.setdefault(row["area"], {"weight": 0, "earned": 0.0, "gaps": 0})
        bucket["weight"] += WEIGHTS[row["priority"]]
        bucket["earned"] += WEIGHTS[row["priority"]] * COMPLETION[row["status"]]
        if row["priority"] == "must" and COMPLETION[row["status"]] < 1.0:
            bucket["gaps"] += 1
    for bucket in areas.values():
        bucket["percent"] = bucket["earned"] / bucket["weight"] * 100 if bucket["weight"] else 0.0

    return {
        "score": round(score, 1),
        "features": len(rows),
        "in_scope": len(scoped),
        "out_of_scope": len(rows) - len(scoped),
        "must_gaps": must_gaps,
        "must_total": must_total,
        "by_priority": by_priority,
        "areas": dict(sorted(areas.items(), key=lambda kv: kv[1]["percent"])),
        "shippable": not must_gaps and must_total > 0,
    }


def report_text(result: dict, path: str) -> str:
    out = [f"[*] Paridad funcional: {path}", ""]
    out.append(f"[#] Score: {result['score']}%  ({result['in_scope']} en alcance, {result['out_of_scope']} fuera)")
    for prio in ("must", "should", "could"):
        stats = result["by_priority"][prio]
        pct = "n/a" if stats["percent"] is None else f"{stats['percent']:.0f}%"
        out.append(
            f"    {prio:<6} {stats['done']:>3} done  {stats['partial']:>2} parcial  "
            f"de {stats['total']:>3}  -> {pct}"
        )
    out.append("")
    out.append("[#] Por area (peor primero):")
    for area, stats in result["areas"].items():
        flag = f"  !! {stats['gaps']} must pendiente(s)" if stats["gaps"] else ""
        out.append(f"    {stats['percent']:5.0f}%  {area}{flag}")
    if result["must_gaps"]:
        out.append("")
        out.append(f"[x] NO desplegable: {len(result['must_gaps'])} must sin terminar")
        for row in result["must_gaps"]:
            out.append(f"    - [{row['area']}] {row['feature'] or row['id']} ({row['status']})")
    elif result["must_total"] == 0:
        out.append("")
        out.append("[!] Ningun feature marcado como must: define prioridades o esto no vale como gate.")
    else:
        out.append("")
        out.append("[+] Todos los must estan done: paridad minima alcanzada.")
    return "\n".join(out)


def report_markdown(result: dict) -> str:
    lines = ["# Paridad funcional", "", f"**Score: {result['score']}%** — "
             f"{result['in_scope']} features en alcance, {result['out_of_scope']} fuera.", "",
             "| Prioridad | Done | Parcial | Total | % |", "| --- | --- | --- | --- | --- |"]
    for prio in ("must", "should", "could"):
        s = result["by_priority"][prio]
        pct = "n/a" if s["percent"] is None else f"{s['percent']:.0f}%"
        lines.append(f"| {prio} | {s['done']} | {s['partial']} | {s['total']} | {pct} |")
    lines += ["", "## Por area", "", "| Area | % | Must pendientes |", "| --- | --- | --- |"]
    for area, s in result["areas"].items():
        lines.append(f"| {area} | {s['percent']:.0f}% | {s['gaps']} |")
    lines += ["", "## Must pendientes", ""]
    if result["must_gaps"]:
        lines += [f"- [{r['area']}] {r['feature'] or r['id']} — `{r['status']}`" for r in result["must_gaps"]]
    elif result["must_total"] == 0:
        lines.append("_Ningun must definido: asigna prioridades antes de usar esto como gate._")
    else:
        lines.append("Ninguno. Desplegable en terminos de paridad.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score de paridad funcional de un clon.")
    parser.add_argument("manifest", nargs="?", default="features.csv", help="features.csv / .json")
    parser.add_argument("--json", action="store_true", help="Resumen en JSON")
    parser.add_argument("--markdown", action="store_true", help="Informe en Markdown")
    parser.add_argument("--out", help="Escribir el informe en este fichero")
    parser.add_argument("--no-fail", action="store_true", help="Salir con 0 aunque falten must")
    args = parser.parse_args(argv)

    try:
        rows = load(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[x] No se pudo leer {args.manifest}: {exc}", file=sys.stderr)
        return 2
    if not rows:
        print("[!] Manifiesto vacio: no hay features que puntuar.", file=sys.stderr)
        return 2

    result = analyze(rows)

    if args.json:
        text = json.dumps(result, ensure_ascii=False, indent=2)
    elif args.markdown:
        text = report_markdown(result)
    else:
        text = report_text(result, args.manifest)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text.rstrip() + "\n")
        print(f"[+] Informe escrito en {args.out}")
    else:
        print(text)

    if result["shippable"] or args.no_fail:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
