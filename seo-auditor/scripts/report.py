# -*- coding: utf-8 -*-
"""Informe unificado: `audit.json` (máquina), `audit.md` (persona) y
`report.html` (imprimible con filtros 🔴🟡🟢).

La puntuación sale SIEMPRE de `checks.compute_rubric`, que solo usa la
evidencia guardada: por eso `rescore` puede recalcularla sin red.
"""
from __future__ import annotations

import html as html_mod
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import analyze, checks as checks_mod
except (ImportError, ValueError):
    import analyze
    import checks as checks_mod

TOOL_NAME = "seo-auditor"
TOOL_VERSION = "2.0.0"
SCHEMA_ID = "seo-auditor/audit"
SCHEMA_VERSION = "2.0"

DIM_LABEL = {
    "tecnico": "Técnico",
    "contenido": "Contenido",
    "schema": "Schema",
    "geo": "GEO",
    "seguridad": "Seguridad",
    "rendimiento": "Rendimiento",
}

LIMITS = [
    "La puntuación es interna y reproducible desde `checks`; no es una nota oficial de Google.",
    "No se consultan rankings, Search Console ni Analytics salvo que el usuario los aporte.",
    "El HTML analizado puede no incluir contenido generado por JavaScript.",
    "GEO se evalúa por señales estructurales y editoriales; no se infiere posición en respuestas de IA.",
    "LCP/CLS/TBT/Speed Index solo aparecen si se aporta un dato externo; si no, se marcan `estimate` o `skip`.",
    "La presencia por motor (`site:`) es indirecta y se marca `estimate`: no prueba indexación.",
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def build_payload(result, generated_at=None):
    """Construye el payload canónico de `audit.json`."""
    findings = result.get("findings") or []
    merged = checks_mod.merge_checks(result.get("checks"), findings)
    for rec in merged:
        rec["icon"] = checks_mod.icon_for(rec)
    rubric = checks_mod.compute_rubric(merged)
    counts = {"pass": 0, "fail": 0, "skip": 0}
    by_severity = {"must": {"pass": 0, "fail": 0, "skip": 0},
                   "should": {"pass": 0, "fail": 0, "skip": 0},
                   "nice": {"pass": 0, "fail": 0, "skip": 0}}
    for rec in merged:
        status = rec.get("status", "skip")
        counts[status] = counts.get(status, 0) + 1
        sev = rec.get("severity", "nice")
        if sev in by_severity:
            by_severity[sev][status] += 1

    payload = {
        "schema": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "generated_at": generated_at or _now(),
        "mode": result.get("mode", "page"),
        "target": result.get("target", result.get("start_url", result.get("root", ""))),
        "crawl": result.get("crawl"),
        "rubric": rubric,
        "score": rubric["total"],
        "verdict": rubric["verdict"],
        "verdict_line": rubric["verdict_line"],
        "dimensions": rubric["dimensions"],
        "counts": counts,
        "counts_by_severity": by_severity,
        "must_fails": rubric["must_fail_count"],
        "checks": merged,
        "findings": findings,
        "pages": result.get("pages", []),
        "data": result.get("data", {}),
        "limits": list(LIMITS),
    }
    return payload


# --- Markdown ---------------------------------------------------------------

def _table_rubric(payload):
    lines = ["| Dimensión | Peso | Puntuación | ✅ | ❌ | ⚪ |",
             "|---|---:|---:|---:|---:|---:|"]
    for dim in checks_mod.DIMENSIONS:
        item = payload["dimensions"].get(dim, {})
        score = item.get("score")
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            DIM_LABEL.get(dim, dim),
            item.get("weight", checks_mod.DIM_WEIGHTS.get(dim, 0)),
            "—" if score is None else "%s/100" % score,
            item.get("pass", 0), item.get("fail", 0), item.get("skip", 0)))
    return "\n".join(lines)


def _sort_checks(items):
    severity = {"must": 0, "should": 1, "nice": 2}
    status = {"fail": 0, "pass": 1, "skip": 2}
    return sorted(items, key=lambda c: (status.get(c.get("status"), 3),
                                        severity.get(c.get("severity"), 3),
                                        c.get("id", "")))


def render_markdown(payload):
    counts = payload.get("counts", {})
    checks = _sort_checks(payload.get("checks", []))
    lines = [
        "# Informe SEO — %s" % (payload.get("target") or "sitio"),
        "",
        "> **Veredicto:** %s" % payload.get("verdict_line", ""),
        "> **Puntuación:** %.1f/100 · 🔴 %d · 🟡 %d · 🟢 %d · ⚪ %d" % (
            payload.get("score", 0),
            _fail_by_severity(payload, "must"),
            _fail_by_severity(payload, "should"),
            _pass_count(payload),
            counts.get("skip", 0)),
        "> Modo: `%s` · Generado (UTC): %s · Motor: %s %s" % (
            payload.get("mode"), payload.get("generated_at"),
            TOOL_NAME, TOOL_VERSION),
        "",
        "> Cada número de este informe procede de la evidencia guardada en "
        "`audit.json`. Lo no medible se marca `skip` o `estimate`; no se inventan datos.",
        "",
        "## Rúbrica 0–100 por dimensiones",
        "",
        _table_rubric(payload),
        "",
        "Fórmula: %s" % payload.get("rubric", {}).get("formula", ""),
        "",
    ]

    crawl = payload.get("crawl")
    if crawl:
        lines += [
            "## Rastreo (declarado)",
            "",
            "- Tope de páginas: **%s** · Profundidad: **%s** · Ritmo: **%s req/s**" % (
                crawl.get("max_pages"), crawl.get("max_depth"),
                crawl.get("requests_per_second")),
            "- robots.txt respetado: **%s** · Páginas rastreadas: **%s**" % (
                "sí" if crawl.get("robots_respected") else "no",
                crawl.get("pages_fetched")),
            "",
        ]

    # Grupos por icono.
    groups = (
        ("🔴 Críticos (`must`)", lambda c: c.get("status") == "fail" and c.get("severity") == "must"),
        ("🟡 Avisos (`should`)", lambda c: c.get("status") == "fail" and c.get("severity") == "should"),
        ("🟢 Aprobados y mejoras opcionales", lambda c: c.get("status") == "pass"
         or (c.get("status") == "fail" and c.get("severity") == "nice")),
        ("⚪ No comprobados (`skip`)", lambda c: c.get("status") == "skip"),
    )
    for title, predicate in groups:
        subset = [c for c in checks if predicate(c)]
        lines += ["## %s — %d" % (title, len(subset)), ""]
        if not subset:
            lines += ["_Sin registros en este grupo._", ""]
            continue
        for rec in subset:
            icon = checks_mod.icon_for(rec)
            state = {"pass": "aprobado", "fail": "falla", "skip": "no aplica"}.get(
                rec.get("status"), rec.get("status"))
            lines.append("### %s `%s` — %s" % (icon, rec.get("id"), rec.get("title")))
            lines.append("- Dimensión: %s · Severidad: `%s` (%s) · Estado: %s" % (
                DIM_LABEL.get(rec.get("dimension"), rec.get("dimension", "")),
                rec.get("severity"), checks_mod.severity_label(rec.get("severity")), state))
            if rec.get("url"):
                lines.append("- Evidencia en: `%s`" % rec["url"])
            lines.append("- Evidencia: %s" % (rec.get("evidence") or "—"))
            if rec.get("status") == "fail":
                lines.append("- Recomendación: %s" % analyze.recommendation_for(rec.get("id")))
            if rec.get("citation"):
                lines.append("- Doc oficial: %s" % rec["citation"])
            if rec.get("note"):
                lines.append("- Nota: `%s`" % rec["note"])
            lines.append("")

    lines += ["## Datos medidos", ""]
    data = payload.get("data") or {}
    onpage = data.get("onpage") or {}
    if onpage.get("keyword_density"):
        lines += ["### Densidad de términos (informativa, no es objetivo SEO)",
                  "", "| Término | Apariciones | Densidad |", "|---|---:|---:|"]
        for row in onpage["keyword_density"].get("filas", [])[:8]:
            lines.append("| %s | %s | %s%% |" % (
                row["termino"], row["apariciones"], row["densidad_pct"]))
        lines.append("")
    if onpage.get("headings"):
        counts_h = onpage["headings"].get("counts", {})
        lines.append("- Encabezados: %s" % ", ".join(
            "%s=%s" % (k.upper(), v) for k, v in counts_h.items()))
    if data.get("security", {}).get("score") is not None:
        lines.append("- Seguridad HTTP: **%s/100** (%s)" % (
            data["security"]["score"], data["security"].get("formula", "")))
    if data.get("schema", {}).get("types"):
        lines.append("- Tipos JSON-LD: %s" % ", ".join(data["schema"]["types"]))
    if data.get("hreflang", {}).get("entries"):
        lines.append("- hreflang: %s" % ", ".join(
            "%s→%s" % (e["hreflang"], e["href"]) for e in data["hreflang"]["entries"]))
    perf = data.get("perf") or {}
    if perf:
        lines.append("- Rendimiento: TTFB=%s ms · HTML=%s bytes · encoding=%s · PSI: %s" % (
            perf.get("ttfb_ms"), perf.get("html_bytes"),
            perf.get("content_encoding"), perf.get("psi_url")))
    lines.append("")

    lines += ["## Límites y datos no comprobados", ""]
    for item in payload.get("limits", []):
        lines.append("- %s" % item)
    lines.append("")
    return "\n".join(lines)


def _fail_by_severity(payload, severity):
    return payload.get("counts_by_severity", {}).get(severity, {}).get("fail", 0)


def _pass_count(payload):
    return payload.get("counts", {}).get("pass", 0)


# --- HTML imprimible --------------------------------------------------------

def render_html(payload):
    checks = _sort_checks(payload.get("checks", []))
    counts = payload.get("counts", {})
    must_fail = _fail_by_severity(payload, "must")
    should_fail = _fail_by_severity(payload, "should")
    nice = payload.get("counts_by_severity", {}).get("nice", {}).get("fail", 0)

    def esc(value):
        return html_mod.escape(str(value if value is not None else ""))

    parts = []
    parts.append("<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
                 "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                 "<title>Informe SEO — %s</title>" % esc(payload.get("target")))
    parts.append("""<style>
:root{--rojo:#d93025;--amarillo:#f9ab00;--verde:#1e8e3e;--gris:#5f6368}
body{font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;margin:0;
background:#f1f3f4;color:#202124}
header{background:#fff;border-bottom:3px solid #1a73e8;padding:24px}
h1{margin:0 0 8px 0;font-size:26px}
.verdict{font-size:18px;font-weight:700;margin:8px 0}
.score{font-size:44px;font-weight:800;line-height:1}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;
max-width:1100px;margin:16px auto;padding:0 24px}
.card{background:#fff;border:1px solid #dadce0;border-radius:8px;padding:14px}
.card .n{font-size:26px;font-weight:700}
.card .l{font-size:12px;color:var(--gris);text-transform:uppercase;letter-spacing:.05em}
main{max-width:1100px;margin:0 auto;padding:0 24px 48px}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13px}
th,td{border-bottom:1px solid #e8eaed;padding:10px;text-align:left;vertical-align:top}
th{background:#f8f9fa;position:sticky;top:0}
tr.fail.must{background:#fce8e6}
tr.fail.should{background:#fef7e0}
tr.pass{background:#e6f4ea}
tr.skip{color:#80868b}
.badge{display:inline-block;border-radius:10px;padding:1px 8px;font-size:11px;font-weight:700}
.b-must{background:var(--rojo);color:#fff}.b-should{background:var(--amarillo);color:#3c2b00}
.b-nice{background:var(--verde);color:#fff}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}
.filters button{border:1px solid #dadce0;background:#fff;border-radius:18px;
padding:8px 16px;cursor:pointer;font-size:13px}
.filters button.active{background:#1a73e8;color:#fff;border-color:#1a73e8}
.hint{background:#e8f0fe;border:1px solid #c6dafc;border-radius:8px;padding:12px;
margin:16px 0;font-size:13px}
a{color:#1a73e8}
.dim{padding:4px 0}
.bar{height:8px;background:#e8eaed;border-radius:4px;overflow:hidden}
.bar span{display:block;height:100%;background:#1a73e8}
@media print{body{background:#fff}.filters,.hint{display:none}th{position:static}
tr{page-break-inside:avoid}header{padding:0 0 12px 0}}
</style></head><body>""")

    parts.append("<header><h1>Informe SEO — %s</h1>" % esc(payload.get("target")))
    parts.append("<div class=\"verdict\">%s</div>" % esc(payload.get("verdict_line")))
    parts.append("<div class=\"score\">%.1f<span style=\"font-size:18px\">/100</span></div>"
                 % float(payload.get("score") or 0))
    parts.append("<div style=\"color:var(--gris);font-size:12px\">Modo %s · %s · %s %s</div>"
                 % (esc(payload.get("mode")), esc(payload.get("generated_at")),
                    TOOL_NAME, TOOL_VERSION))
    parts.append("<div class=\"hint\">Para obtener el PDF: <strong>Imprimir</strong> "
                 "(Ctrl/Cmd+P) → <em>Guardar como PDF</em>. El filtro de abajo no se "
                 "imprime: se imprimen todas las filas.</div></header>")

    parts.append("<div class=\"grid\">")
    cards = [("🔴 Críticos", bool(must_fail), must_fail), ("🟡 Avisos", bool(should_fail), should_fail),
             ("🟢 Mejoras opcionales", bool(nice), nice), ("✅ Aprobados", counts.get("pass", 0) > 0,
                                                          counts.get("pass", 0)),
             ("⚪ No comprobados", counts.get("skip", 0) > 0, counts.get("skip", 0))]
    for label, _flag, number in cards:
        parts.append("<div class=\"card\"><div class=\"n\">%s</div>"
                     "<div class=\"l\">%s</div></div>" % (esc(number), esc(label)))
    parts.append("</div>")

    parts.append("<main><h2>Rúbrica por dimensiones</h2><div class=\"card\">")
    for dim in checks_mod.DIMENSIONS:
        item = payload.get("dimensions", {}).get(dim, {})
        score = item.get("score")
        width = 0 if score is None else max(0, min(100, score))
        parts.append("<div class=\"dim\"><strong>%s</strong> · peso %s · %s"
                     "<div class=\"bar\"><span style=\"width:%s%%\"></span></div></div>" % (
                         esc(DIM_LABEL.get(dim, dim)), esc(item.get("weight")),
                         "sin datos" if score is None else "%s/100" % score, width))
    parts.append("<p style=\"font-size:12px;color:var(--gris)\">%s</p></div>"
                 % esc(payload.get("rubric", {}).get("formula", "")))

    crawl = payload.get("crawl")
    if crawl:
        parts.append("<div class=\"hint\">Rastreo declarado: tope <strong>%s</strong> páginas · "
                     "profundidad <strong>%s</strong> · <strong>%s req/s</strong> · "
                     "robots.txt respetado: <strong>%s</strong></div>" % (
                         esc(crawl.get("max_pages")), esc(crawl.get("max_depth")),
                         esc(crawl.get("requests_per_second")),
                         "sí" if crawl.get("robots_respected") else "no"))

    parts.append("<div class=\"filters\">"
                 "<button data-filter=\"all\" class=\"active\">Todo (%d)</button>"
                 "<button data-filter=\"must\">🔴 Críticos (%d)</button>"
                 "<button data-filter=\"should\">🟡 Avisos (%d)</button>"
                 "<button data-filter=\"pass\">🟢 Aprobados (%d)</button>"
                 "<button data-filter=\"skip\">⚪ No comprobados (%d)</button>"
                 "</div>" % (len(checks), must_fail, should_fail,
                             counts.get("pass", 0), counts.get("skip", 0)))

    parts.append("<table><thead><tr><th>Estado</th><th>ID</th><th>Comprobación</th>"
                 "<th>Dimensión</th><th>Severidad</th><th>Evidencia</th>"
                 "<th>Doc oficial</th></tr></thead><tbody>")
    for rec in checks:
        status = rec.get("status", "skip")
        severity = rec.get("severity", "nice")
        row_class = status if status != "fail" else "fail " + severity
        badge = {"must": "b-must", "should": "b-should", "nice": "b-nice"}.get(severity, "b-nice")
        parts.append("<tr class=\"%s\" data-status=\"%s\" data-severity=\"%s\">" % (
            row_class, status, severity))
        parts.append("<td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td>" % (
            esc(checks_mod.icon_for(rec)), esc(rec.get("id")), esc(rec.get("title")),
            esc(DIM_LABEL.get(rec.get("dimension"), rec.get("dimension")))))
        parts.append("<td><span class=\"badge %s\">%s</span></td>" % (
            badge, esc(severity)))
        evidence = esc(rec.get("evidence"))
        if status == "fail":
            evidence += "<br><em>%s</em>" % esc(analyze.recommendation_for(rec.get("id")))
        parts.append("<td>%s</td>" % evidence)
        citation = rec.get("citation") or ""
        parts.append("<td>%s</td></tr>" % (
            "<a href=\"%s\" rel=\"noopener\">doc</a>" % esc(citation) if citation else "—"))
    parts.append("</tbody></table>")

    parts.append("<h2 style=\"margin-top:28px\">Datos medidos</h2><div class=\"card\">")
    data = payload.get("data") or {}
    rows = []
    onpage = data.get("onpage") or {}
    if onpage:
        rows.append(("Ratio texto/HTML", "%s%% (estimate)" % round(
            (onpage.get("text_ratio") or 0) * 100, 1)))
        rows.append(("Palabras", onpage.get("word_count")))
        rows.append(("Encabezados", onpage.get("headings", {}).get("counts")))
        rows.append(("Imágenes sin alt", len(onpage.get("images_without_alt") or [])))
    if data.get("schema"):
        rows.append(("Tipos JSON-LD", ", ".join(data["schema"].get("types") or []) or "ninguno"))
    if data.get("security", {}).get("score") is not None:
        rows.append(("Seguridad HTTP", "%s/100" % data["security"]["score"]))
    if data.get("perf"):
        rows.append(("TTFB", "%s ms" % data["perf"].get("ttfb_ms")))
        rows.append(("Peso HTML", "%s bytes" % data["perf"].get("html_bytes")))
        rows.append(("Compresión", data["perf"].get("content_encoding") or "ausente"))
    if data.get("serp"):
        rows.append(("Título", "%s caracteres · ~%s px (estimate)" % (
            data["serp"].get("title_chars"), data["serp"].get("title_px"))))
        rows.append(("Descripción", "%s caracteres" % data["serp"].get("description_chars")))
    for label, value in rows:
        parts.append("<div><strong>%s:</strong> %s</div>" % (esc(label), esc(value)))
    parts.append("<p><strong>PageSpeed Insights:</strong> %s</p></div>" % (
        "<a href=\"%s\" rel=\"noopener\">abrir</a>" % esc((data.get("perf") or {}).get("psi_url"))
        if (data.get("perf") or {}).get("psi_url") else "sin URL"))

    parts.append("<h2 style=\"margin-top:28px\">Límites</h2><div class=\"card\"><ul>")
    for item in payload.get("limits", []):
        parts.append("<li>%s</li>" % esc(item))
    parts.append("</ul></div></main>")

    parts.append("""<script>
document.querySelectorAll('.filters button').forEach(function(btn){
  btn.addEventListener('click', function(){
    var f = btn.getAttribute('data-filter');
    document.querySelectorAll('.filters button').forEach(function(b){b.classList.remove('active')});
    btn.classList.add('active');
    document.querySelectorAll('tbody tr').forEach(function(tr){
      var status = tr.getAttribute('data-status');
      var severity = tr.getAttribute('data-severity');
      var show = f === 'all' || (f === 'must' && status === 'fail' && severity === 'must')
        || (f === 'should' && status === 'fail' && severity === 'should')
        || (f === 'pass' && status === 'pass') || (f === 'skip' && status === 'skip');
      tr.style.display = show ? '' : 'none';
    });
  });
});
</script></body></html>""")
    return "\n".join(parts)


# --- Escritura / re-score ---------------------------------------------------

def write_report(result, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = build_payload(result)
    (out / "audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "audit.md").write_text(render_markdown(payload), encoding="utf-8")
    (out / "report.html").write_text(render_html(payload), encoding="utf-8")
    return str(out)


def rescore(payload, keep_timestamp=True):
    """Recalcula rúbrica, score y veredicto desde `checks`. Sin red."""
    if "checks" not in payload:
        raise ValueError("El JSON no contiene `checks`: no se puede re-puntuar.")
    new = dict(payload)
    recomputed = checks_mod.compute_rubric(payload.get("checks") or [])
    new["rubric"] = recomputed
    new["score"] = recomputed["total"]
    new["verdict"] = recomputed["verdict"]
    new["verdict_line"] = recomputed["verdict_line"]
    new["dimensions"] = recomputed["dimensions"]
    new["must_fails"] = recomputed["must_fail_count"]
    new["rescored_at"] = _now()
    new["rescored_without_network"] = True
    if not keep_timestamp:
        new["generated_at"] = new["rescored_at"]
    return new


def rescore_file(path, output_dir=None):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    new = rescore(payload)
    target_dir = Path(output_dir) if output_dir else Path(path).resolve().parent
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "audit.rescored.json").write_text(
        json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    (target_dir / "audit.rescored.md").write_text(render_markdown(new), encoding="utf-8")
    (target_dir / "report.rescored.html").write_text(render_html(new), encoding="utf-8")
    return new, str(target_dir)


# Compatibilidad con la API anterior.
def score(findings):
    return build_payload({"findings": findings})["score"]
