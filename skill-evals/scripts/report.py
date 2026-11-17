"""Convierte una corrida de `run.py` en informe Markdown o HTML autónomo.

Uso:
    py skill-evals/scripts/report.py --run run.json --out informe.md
    py skill-evals/scripts/report.py --run run.json --baseline anterior.json --format html

Sin red, sin plantillas externas y sin reloj: el informe solo depende de los
JSON de entrada, así que dos ejecuciones con los mismos datos coinciden byte a
byte. El HTML es un fichero único con estilos embebidos, apto para adjuntar.

Código de salida: 0 correcto · 2 entrada ilegible.
"""

from __future__ import annotations

import argparse
import html
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


def _rows(run: dict, diff: dict | None) -> list[tuple[str, str]]:
    metrics = run["metrics"]
    budget = run["budget"]
    rows = [
        ("Casos", str(metrics["cases"])),
        ("Aprobados", str(metrics["passed"])),
        ("Precisión", f"{metrics['precision']:.3f}"),
        ("Recall", f"{metrics['recall']:.3f}"),
        ("MRR", f"{metrics['mrr']:.3f}"),
        ("Falsos negativos", str(metrics["false_negatives"])),
        ("Falsos positivos", str(metrics["false_positives"])),
        ("Colisiones", str(metrics["collisions"])),
        ("Tokens de catálogo", f"{budget['catalog_tokens']} (límite {budget['catalog_limit']})"),
        ("Fuera de presupuesto", ", ".join(budget["over_budget"]) or "ninguna"),
    ]
    if diff is not None:
        rows.extend([
            ("Regresiones", str(len(diff["regressions"]))),
            ("Arreglos", str(len(diff["fixes"]))),
            ("Casos nuevos", str(len(diff["new"]))),
        ])
    return rows


def render_markdown(run: dict, diff: dict | None = None) -> str:
    metrics = run["metrics"]
    budget = run["budget"]
    verdict = run.get("gate", {}).get("verdict", "pass")
    lines = [
        "# Informe de evaluación de skills",
        "",
        f"**Veredicto: {verdict.upper()}** · umbral de activación {run['threshold']}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
    ]
    lines.extend(f"| {name} | {value} |" for name, value in _rows(run, diff))

    lines.extend(["", "## Por tipo y split", "", "| Tipo | Casos | Aprobados |", "|---|---:|---:|"])
    for kind, data in metrics["by_kind"].items():
        lines.append(f"| {kind} | {data['cases']} | {data['passed']} |")
    lines.extend(["", "| Split | Casos | Aprobados |", "|---|---:|---:|"])
    for split, data in metrics["by_split"].items():
        lines.append(f"| {split} | {data['cases']} | {data['passed']} |")

    failures = run.get("failures") or []
    lines.extend(["", f"## Fallos ({len(failures)})", ""])
    if failures:
        lines.extend(["| Caso | Esperado | Ganador | Puntuación | Hermana |", "|---|---|---|---:|---|"])
        for item in failures:
            lines.append(
                f"| `{item['id']}` | {item['expect'] or '—'} | {item['best']} | "
                f"{item['score']:.3f} | {item['sibling'] or '—'} |"
            )
    else:
        lines.append("Ninguno: todos los casos pasan con el umbral actual.")

    collisions = run.get("collisions") or []
    lines.extend(["", f"## Colisiones de descripción ({len(collisions)})", ""])
    if collisions:
        lines.extend(["| Skill A | Skill B | Jaccard |", "|---|---|---:|"])
        lines.extend(f"| {item['a']} | {item['b']} | {item['jaccard']:.2f} |" for item in collisions)
    else:
        lines.append("Sin pares por encima del umbral de similitud.")

    lines.extend(["", "## Presupuesto de contexto", "", "| Skill | Descripción | Cuerpo | Líneas |",
                  "|---|---:|---:|---:|"])
    for item in budget["heaviest"]:
        lines.append(
            f"| {item['skill']} | {item['description_tokens']} | "
            f"{item['body_tokens']} | {item['body_lines']} |"
        )
    lines.append("")
    lines.append(f"Catálogo completo: {budget['catalog_tokens']} tokens estimados "
                 f"({budget['skills']} skills).")

    if diff is not None:
        lines.extend(["", "## Cambios contra la línea base", ""])
        for label, key in (("Regresiones", "regressions"), ("Arreglos", "fixes"),
                           ("Nuevos", "new"), ("Retirados", "removed")):
            values = diff[key]
            lines.append(f"- **{label}**: {', '.join(values) if values else 'ninguno'}")

    lines.append("")
    return "\n".join(lines)


def render_html(run: dict, diff: dict | None = None) -> str:
    metrics = run["metrics"]
    verdict = run.get("gate", {}).get("verdict", "pass")
    escape = html.escape

    summary = "".join(
        f"<tr><th>{escape(name)}</th><td>{escape(value)}</td></tr>" for name, value in _rows(run, diff)
    )
    kinds = "".join(
        f"<tr><td>{escape(kind)}</td><td>{data['cases']}</td><td>{data['passed']}</td></tr>"
        for kind, data in metrics["by_kind"].items()
    )
    splits = "".join(
        f"<tr><td>{escape(split)}</td><td>{data['cases']}</td><td>{data['passed']}</td></tr>"
        for split, data in metrics["by_split"].items()
    )
    failures = "".join(
        "<tr><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td><td>{:.3f}</td><td>{}</td></tr>".format(
            escape(item["id"]), escape(item.get("prompt", "")), escape(item["expect"] or "—"),
            escape(item["best"]), item["score"], escape(item["sibling"] or "—"),
        )
        for item in run.get("failures") or []
    ) or '<tr><td colspan="6">Ninguno.</td></tr>'
    collisions = "".join(
        f"<tr><td>{escape(item['a'])}</td><td>{escape(item['b'])}</td>"
        f"<td>{item['jaccard']:.2f}</td></tr>"
        for item in run.get("collisions") or []
    ) or '<tr><td colspan="3">Sin colisiones.</td></tr>'
    budget = "".join(
        f"<tr><td>{escape(item['skill'])}</td><td>{item['description_tokens']}</td>"
        f"<td>{item['body_tokens']}</td><td>{item['body_lines']}</td></tr>"
        for item in run["budget"]["heaviest"]
    )
    delta = ""
    if diff is not None:
        delta = "<h2>Cambios contra la línea base</h2><ul>" + "".join(
            f"<li><strong>{escape(label)}</strong>: "
            f"{escape(', '.join(diff[key]) if diff[key] else 'ninguno')}</li>"
            for label, key in (("Regresiones", "regressions"), ("Arreglos", "fixes"),
                               ("Nuevos", "new"), ("Retirados", "removed"))
        ) + "</ul>"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Informe de evaluación de skills</title>
<style>
body{{font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;margin:0;background:#f5f6f8;color:#1f2328}}
main{{max-width:960px;margin:0 auto;padding:32px}}
h1{{margin:0 0 8px;font-size:28px}}
h2{{margin-top:32px;font-size:20px;border-bottom:1px solid #d8dee4;padding-bottom:6px}}
table{{border-collapse:collapse;width:100%;background:#fff;margin-top:8px}}
th,td{{border:1px solid #d8dee4;padding:8px 10px;text-align:left;font-size:14px}}
th{{background:#f0f3f6}}
.verdict{{display:inline-block;padding:4px 10px;border-radius:6px;font-weight:600;
background:{'#e6f4ea' if verdict == 'pass' else '#fde8e8'};
color:{'#137333' if verdict == 'pass' else '#b3261e'}}}
code{{background:#f0f3f6;padding:1px 4px;border-radius:4px}}
</style>
</head>
<body>
<main>
<h1>Informe de evaluación de skills</h1>
<p><span class="verdict">{escape(verdict.upper())}</span> · umbral de activación {run['threshold']}</p>
<h2>Resumen</h2>
<table>{summary}</table>
<h2>Por tipo</h2>
<table><tr><th>Tipo</th><th>Casos</th><th>Aprobados</th></tr>{kinds}</table>
<h2>Por split</h2>
<table><tr><th>Split</th><th>Casos</th><th>Aprobados</th></tr>{splits}</table>
<h2>Fallos</h2>
<table><tr><th>Caso</th><th>Prompt</th><th>Esperado</th><th>Ganador</th><th>Puntuación</th><th>Hermana</th></tr>{failures}</table>
<h2>Colisiones de descripción</h2>
<table><tr><th>Skill A</th><th>Skill B</th><th>Jaccard</th></tr>{collisions}</table>
<h2>Presupuesto de contexto</h2>
<table><tr><th>Skill</th><th>Descripción</th><th>Cuerpo</th><th>Líneas</th></tr>{budget}</table>
<p>Catálogo completo: {run['budget']['catalog_tokens']} tokens estimados
({run['budget']['skills']} skills).</p>
{delta}
</main>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    evalkit.force_utf8_output()
    parser = argparse.ArgumentParser(description="Informe de una corrida de skill-evals.")
    parser.add_argument("--run", required=True, help="JSON de run.py")
    parser.add_argument("--baseline", help="corrida anterior para el diff")
    parser.add_argument("--format", choices=("md", "html"), default="md")
    parser.add_argument("--out", help="fichero de salida (por defecto, stdout)")
    args = parser.parse_args(argv)

    run = _read(Path(args.run))
    if run.get("format") != evalkit.RUN_FORMAT:
        print(f"{args.run}: no es una corrida de skill-evals")
        return 2
    diff = _read(Path(args.baseline)) if args.baseline else None
    text = render_html(run, diff) if args.format == "html" else render_markdown(run, diff)

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"escrito: {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
