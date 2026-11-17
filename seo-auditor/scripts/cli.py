# -*- coding: utf-8 -*-
"""CLI de seo-auditor.

Comandos:
  audit     auditoría completa (web / source / local / hybrid / page)
  rescore   recálculo de la rúbrica desde audit.json (sin red)
  compare   diff entre dos audit.json
  serp      simulador SERP + tarjetas sociales
  perf      TTFB, peso, compresión y recursos
  headers   seguridad HTTP (HSTS, CSP, XFO, XCTO, RP, PP, mixed content)
  schema    JSON-LD + rich preview
  hreflang  pares, autorreferencia, x-default y <html lang>
  onpage    ratio, jerarquía H, imágenes sin alt y densidad
  index     directivas de indexación cruzadas (+ presencia opcional)
  fix       modo Execute con dry-run (--apply para escribir)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

try:
    from . import (analyze, compare as compare_mod, execute, indexcheck,
                   perf, report, schema_audit, serp, source_audit,
                   web_audit)
    from .httpbody import decode_body
    from .page import parse_file, parse_html
except (ImportError, ValueError):
    import analyze
    import compare as compare_mod
    import execute
    import indexcheck
    import perf
    import report
    import schema_audit
    import serp
    import source_audit
    import web_audit
    from httpbody import decode_body
    from page import parse_file, parse_html

VERSION = report.TOOL_VERSION


def _force_utf8(stream):
    """Consola cp1252 en Windows no puede imprimir 🔴/🟡; forzamos UTF-8."""
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


_force_utf8(sys.stdout)
_force_utf8(sys.stderr)


# --- utilidades -------------------------------------------------------------

def _slug(target):
    base = Path(target.rstrip("/\\")).name or "website"
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", base) or "website"


def _stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _print_checks(checks, only=None, label=None):
    if label:
        print("\n== %s ==" % label)
    for rec in checks:
        if only and rec.get("dimension") not in only:
            continue
        icon = {"pass": "🟢", "fail": "🔴" if rec.get("severity") == "must" else "🟡",
                "skip": "⚪"}.get(rec.get("status"), "⚪")
        print("%s %-18s %s" % (icon, rec.get("id"), rec.get("evidence", "")))


def _http_ok(url, timeout=10, allow_local=False):
    try:
        from .security import build_safe_opener, validate_target
    except (ImportError, ValueError):
        from security import build_safe_opener, validate_target
    try:
        validate_target(url, allow_local=allow_local)
        request = Request(url, headers={"User-Agent": "SEOAuditor/1.0 (+audit)"})
        with build_safe_opener(allow_local).open(request, timeout=timeout) as response:
            body = decode_body(response.read(200_000), dict(response.headers))
            return 200 <= (response.status or 0) < 300 and len(body) > 0
    except (HTTPError, URLError, ValueError, OSError):
        return False


def _is_url(target):
    return target.lower().startswith(("http://", "https://"))


def _resolve_path(target):
    path = Path(target)
    if path.is_dir():
        for name in ("index.html", "index.htm", "index.php"):
            if (path / name).exists():
                return path / name
        for candidate in sorted(path.glob("*.html")):
            return candidate
        raise SystemExit("No se encontró HTML en %s" % path)
    if not path.exists():
        raise SystemExit("No existe el archivo: %s" % target)
    return path


def run_pipeline(target, allow_local=False, robots_path=None, presence=False,
                 timeout=10, mode=None):
    """Analiza un archivo HTML o una URL con todos los módulos disponibles.

    `mode` es el modo declarado por el comando (`page`, `web`, ...); si no se
    indica, una URL cuenta como `web` y un fichero como `page`.
    """
    measured = None
    headers = {}
    if _is_url(target):
        measured = perf.measure(target, timeout=timeout, allow_local=allow_local)
        page = parse_html(measured["body"].decode("utf-8", errors="replace"))
        page_url = measured["final_url"]
        headers = measured["headers"]
        label = page_url
    else:
        path = _resolve_path(target)
        page = parse_file(str(path))
        page_url = ""
        label = str(path)

    robots = None
    robots_url = ""
    if robots_path:
        robots = indexcheck.parse_robots(
            Path(robots_path).read_text(encoding="utf-8", errors="replace"))
    elif measured:
        text, robots_url = indexcheck.fetch_robots(
            page_url, timeout=timeout, allow_local=allow_local)
        robots = indexcheck.parse_robots(text)

    sitemap_urls = list((robots or {}).get("sitemaps", []))
    if measured:
        origin = re.match(r"^(https?://[^/]+)", page_url)
        if origin and not sitemap_urls:
            candidate = origin.group(1) + "/sitemap.xml"
            if _http_ok(candidate, timeout, allow_local):
                sitemap_urls.append(candidate)

    llms_status = None
    llms_full_status = None
    if measured:
        origin = re.match(r"^(https?://[^/]+)", page_url)
        if origin:
            llms_status = _http_ok(origin.group(1) + "/llms.txt", timeout, allow_local)
            llms_full_status = _http_ok(origin.group(1) + "/llms-full.txt",
                                        timeout, allow_local)
    elif Path(target).is_dir():
        llms_status = (Path(target) / "llms.txt").exists()
        llms_full_status = (Path(target) / "llms-full.txt").exists()

    presence_data = None
    if presence and measured:
        print("Comprobando presencia con `site:` (indirecto, estimate)...")
        presence_data = indexcheck.check_presence(page_url, timeout=timeout)

    page_map = {page_url or label: page.hreflangs}
    checks, data = analyze.document_checks(
        page, url=label, page_url=page_url, headers=headers or None,
        robots=robots, sitemap_urls=sitemap_urls, page_map=page_map,
        llms_status=llms_status, http_llms_status=llms_full_status,
        presence=presence_data)

    if measured:
        perf_checks, perf_data = perf.analyze(
            headers, len(measured["body"]), measured["ttfb_ms"],
            measured["total_ms"], page, url=page_url)
        checks.extend(perf_checks)
        data["perf"] = perf_data
        data["http"] = {"status": measured["status"],
                        "final_url": measured["final_url"],
                        "headers": headers}

    if mode is None:
        mode = "web" if measured else "page"
    result = {
        "mode": mode,
        "target": label,
        "pages_scanned": 1,
        "pages": [label],
        "checks": checks,
        "findings": analyze.to_findings(checks),
        "data": data,
    }
    return result, page, page_url or label


def _write(result, out_dir):
    out = report.write_report(result, out_dir)
    payload = json.loads((Path(out) / "audit.json").read_text(encoding="utf-8"))
    return out, payload


def _summary(out, payload):
    counts = payload.get("counts", {})
    print("")
    print(payload.get("verdict_line"))
    print("Puntuación: %.1f/100 · 🔴 %d · 🟡 %d · ✅ %d · ⚪ %d" % (
        payload.get("score", 0),
        payload.get("counts_by_severity", {}).get("must", {}).get("fail", 0),
        payload.get("counts_by_severity", {}).get("should", {}).get("fail", 0),
        counts.get("pass", 0), counts.get("skip", 0)))
    print("Informe: %s/audit.md" % out)
    print("Máquina: %s/audit.json" % out)
    print("Imprimible: %s/report.html" % out)


def _load_json(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "checks" not in data:
        raise SystemExit("El archivo no es un audit.json de seo-auditor 2.x: %s" % path)
    return data


# --- comandos ---------------------------------------------------------------

def cmd_audit(args):
    target = args.target
    if args.mode in ("web", "local"):
        result = web_audit.audit_web(
            target, max_pages=args.max_pages, max_depth=args.max_depth,
            timeout=args.timeout, allow_local=(args.mode == "local"),
            rate=args.rate, respect_robots=not args.no_respect_robots)
    elif args.mode == "source":
        result = source_audit.audit_source(target, max_files=args.max_files)
    elif args.mode == "hybrid":
        if not args.base_url:
            raise SystemExit("hybrid requiere --base-url http://localhost:PUERTO")
        source = source_audit.audit_source(target, max_files=args.max_files)
        runtime = web_audit.audit_web(
            args.base_url, max_pages=args.max_pages, max_depth=args.max_depth,
            timeout=args.timeout, allow_local=True, rate=args.rate,
            respect_robots=not args.no_respect_robots)
        source["checks"].extend(runtime["checks"])
        source["findings"].extend(runtime["findings"])
        source["pages_scanned"] = runtime["pages_scanned"]
        source["crawl"] = runtime["crawl"]
        source["mode"] = "hybrid"
        source_data = source.get("data", {})
        source["data"] = runtime.get("data", {})
        source["data"]["source"] = source_data
        result = source
    else:  # page
        result, _page, _url = run_pipeline(
            target, allow_local=args.allow_local, robots_path=args.robots,
            presence=args.presence, timeout=args.timeout, mode="page")

    out, payload = _write(
        result, Path(args.output) / _slug(str(result.get("target", target))) / _stamp())
    _summary(out, payload)

    if args.presence and result.get("data", {}).get("index", {}).get("presence"):
        print("\nPresencia (estimate):")
        for item in result["data"]["index"]["presence"]:
            print("  %-12s %-10s %s" % (item.get("engine"), item.get("status"),
                                        item.get("note", "")))


def cmd_rescore(args):
    try:
        original = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        original = {}
    before = original.get("score")
    payload, out = report.rescore_file(args.audit, args.output)
    print("Re-score sin red completado.")
    print(payload["verdict_line"])
    print("Puntuación recalculada: %.1f/100 (antes: %s)" % (
        payload["score"],
        "—" if before is None else "%.1f/100" % before))
    print("Escrito en: %s" % out)


def cmd_compare(args):
    old = compare_mod.load(args.old)
    new = compare_mod.load(args.new)
    diff = compare_mod.compare(old, new)
    out = compare_mod.write(diff, args.output)
    print("Delta de puntuación: %+.1f (%s → %s)" % (
        diff["score_delta"], diff["before"].get("score"), diff["after"].get("score")))
    for key in ("mejorado", "empeorado", "nuevo", "resuelto"):
        print("  %-10s %s" % (key, diff["counts"].get(key, 0)))
    if diff["new_must_fails"]:
        print("⚠ Nuevos fallos `must`:")
        for entry in diff["new_must_fails"]:
            print("  %s (%s)" % (entry["id"], entry["url"]))
    print("Comparativa: %s/compare.md" % out)


def cmd_serp(args):
    result, page, page_url = run_pipeline(args.target, timeout=args.timeout)
    out_dir = Path(args.output)
    out, payload = _write(result, out_dir)
    path, metrics = serp.write(page, page_url, out_dir / "serp",
                               title=args.title, description=args.description)
    print("\n== SERP ==")
    print("Título: %d caracteres · ~%s px (límite ~580 px, estimate)%s" % (
        metrics["title_chars"], metrics["title_px"],
        " · SE RECORTA" if metrics["title_truncated"] else ""))
    print("Descripción: %d caracteres%s" % (
        metrics["description_chars"],
        " · SE RECORTA" if metrics["description_truncated"] else ""))
    if metrics["og_missing"]:
        print("Open Graph faltante: %s" % ", ".join(metrics["og_missing"]))
    print("Preview: %s" % path)
    _summary(out, payload)


def cmd_perf(args):
    if not _is_url(args.target):
        raise SystemExit("perf requiere una URL http(s) para medir TTFB y compresión.")
    result, _page, _url = run_pipeline(args.target, timeout=args.timeout)
    out, payload = _write(result, Path(args.output))
    perf_data = result["data"].get("perf", {})
    print("\n== Rendimiento ==")
    print("TTFB: %s ms · HTML: %s bytes · Encoding: %s" % (
        perf_data.get("ttfb_ms"), perf_data.get("html_bytes"),
        perf_data.get("content_encoding") or "ausente"))
    print("CSS externos: %s · JS externos: %s" % (
        perf_data.get("css_externos"), perf_data.get("js_externos")))
    print("PageSpeed Insights: %s" % perf_data.get("psi_url"))
    _print_checks(result["checks"], only={"rendimiento"})
    _summary(out, payload)


def cmd_headers(args):
    if not _is_url(args.target):
        raise SystemExit("headers requiere una URL http(s).")
    result, _page, _url = run_pipeline(args.target, timeout=args.timeout)
    out, payload = _write(result, Path(args.output))
    security = result["data"].get("security", {})
    print("\n== Seguridad HTTP ==")
    print("Score: %s/100" % security.get("score"))
    for name, item in (security.get("headers") or {}).items():
        print("  %-30s %s" % (name, "OK" if item.get("ok") else "FALTA/%s" % item.get("detalle")))
    if security.get("mixed_content"):
        print("Mixed content: %s recurso(s)" % len(security["mixed_content"]))
    _summary(out, payload)


def cmd_schema(args):
    result, page, page_url = run_pipeline(args.target, timeout=args.timeout)
    out, payload = _write(result, Path(args.output))
    schema_data = result["data"].get("schema", {})
    print("\n== Schema.org ==")
    print("Tipos: %s" % (", ".join(schema_data.get("types") or []) or "ninguno"))
    print("Bloques: %s · inválidos: %s" % (
        len(schema_data.get("blocks") or []),
        schema_data.get("invalid_blocks") or "ninguno"))
    if args.rich_preview:
        blocks = schema_audit.blocks_from_page(page)
        path = schema_audit.write_rich_preview(
            blocks, Path(out) / "schema", url=page_url)
        print("Rich preview: %s" % path)
    _print_checks(result["checks"], only={"schema"})
    _summary(out, payload)


def cmd_hreflang(args):
    result, page, page_url = run_pipeline(args.target, timeout=args.timeout)
    out, payload = _write(result, Path(args.output))
    data = result["data"].get("hreflang", {})
    print("\n== hreflang ==")
    print("<html lang>=%r · pares=%s" % (data.get("html_lang"),
                                         len(data.get("entries") or [])))
    for entry in data.get("entries") or []:
        print("  %-10s %s" % (entry["hreflang"], entry["href"]))
    _print_checks(result["checks"], only={"tecnico"})
    _summary(out, payload)


def cmd_onpage(args):
    result, page, page_url = run_pipeline(args.target, timeout=args.timeout)
    out, payload = _write(result, Path(args.output))
    data = result["data"].get("onpage", {})
    print("\n== On-page ==")
    print("Palabras: %s · ratio texto/HTML: %.1f%% (estimate)" % (
        data.get("word_count"), (data.get("text_ratio") or 0) * 100))
    print("Encabezados: %s" % (data.get("headings", {}).get("counts")))
    missing = data.get("images_without_alt") or []
    if missing:
        print("Imágenes sin alt (%d): %s" % (len(missing), ", ".join(missing[:10])))
    rows = (data.get("keyword_density") or {}).get("filas") or []
    if rows:
        print("\n| Término | Apariciones | Densidad |")
        print("|---|---:|---:|")
        for row in rows[:10]:
            print("| %s | %s | %s%% |" % (row["termino"], row["apariciones"],
                                          row["densidad_pct"]))
    _print_checks(result["checks"], only={"contenido"})
    _summary(out, payload)


def cmd_index(args):
    result, page, page_url = run_pipeline(
        args.target, robots_path=args.robots, presence=args.presence,
        timeout=args.timeout)
    out, payload = _write(result, Path(args.output))
    data = result["data"].get("index", {})
    print("\n== Indexación ==")
    print("robots.txt: %s" % (data.get("robots_url") or "no consultado"))
    print("Sitemaps: %s" % (", ".join(data.get("sitemaps") or []) or "ninguno"))
    print("Meta robots: %r · X-Robots-Tag: %r" % (
        data.get("meta_robots"), data.get("x_robots_tag")))
    _print_checks(result["checks"], only={"tecnico"})
    if data.get("presence"):
        print("\nPresencia (indirecta, estimate):")
        for item in data["presence"]:
            print("  %-12s %-10s %s" % (item["engine"], item["status"], item.get("note", "")))
    _summary(out, payload)


def cmd_fix(args):
    payload = _load_json(args.input)
    plan = execute.build_plan(payload, args.output)
    print("Dry-run: se han generado %d borradores DRAFT en %s" % (
        len(plan["files"]), plan["output_dir"]))
    for path in plan["files"]:
        print("  %s" % path)
    print("\nNada se ha aplicado al sitio. Revisa los TODO antes de publicar.")
    if not args.apply:
        return
    if not args.dest:
        raise SystemExit("--apply requiere --dest <carpeta del proyecto>")
    confirmed = args.yes
    if not confirmed:
        answer = input("¿Aplicar robots.txt/llms.txt sobre %s? [s/N] " % args.dest)
        confirmed = answer.strip().lower().startswith("s")
    if not confirmed:
        print("Aplicación cancelada por el usuario.")
        return
    applied = execute.apply_plan(args.output, args.dest, confirm=True)
    for path in applied["applied"]:
        print("Aplicado: %s" % path)
    if applied["skipped_snippets"]:
        print("Snippets no aplicados (integrar a mano): %s" % ", ".join(
            applied["skipped_snippets"]))
    print(applied["note"])


# --- parser -----------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="seo-auditor",
        description="Auditor SEO determinista (stdlib) con rúbrica 0–100, "
                    "GEO, seguridad, rendimiento y 8 módulos IndexPulse.")
    parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="auditoría completa")
    audit.add_argument("target", help="URL o carpeta/archivo local")
    audit.add_argument("--mode", choices=["web", "source", "local", "hybrid", "page"],
                       default="web")
    audit.add_argument("--base-url", default=None, help="URL loopback para hybrid")
    audit.add_argument("--max-pages", type=int, default=30)
    audit.add_argument("--max-depth", type=int, default=3)
    audit.add_argument("--max-files", type=int, default=500)
    audit.add_argument("--timeout", type=int, default=10)
    audit.add_argument("--rate", type=float, default=1.0,
                       help="peticiones por segundo (por defecto 1)")
    audit.add_argument("--no-respect-robots", action="store_true",
                       help="NO recomendado: ignora robots.txt durante el crawl")
    audit.add_argument("--robots", default=None,
                       help="robots.txt local para el modo page")
    audit.add_argument("--presence", action="store_true",
                       help="comprobar presencia con site: (indirecto, solo si se pide)")
    audit.add_argument("--allow-local", action="store_true")
    audit.add_argument("--output", default="reports")
    audit.set_defaults(func=cmd_audit)

    rescore = sub.add_parser("rescore", help="recalcular la rúbrica sin red")
    rescore.add_argument("audit", help="ruta a audit.json")
    rescore.add_argument("--output", default=None)
    rescore.set_defaults(func=cmd_rescore)

    compare = sub.add_parser("compare", help="diff entre dos audit.json")
    compare.add_argument("old")
    compare.add_argument("new")
    compare.add_argument("--output", default="output/compare")
    compare.set_defaults(func=cmd_compare)

    serp_cmd = sub.add_parser("serp", help="simulador SERP + tarjetas sociales")
    serp_cmd.add_argument("target")
    serp_cmd.add_argument("--title", default=None)
    serp_cmd.add_argument("--description", default=None)
    serp_cmd.add_argument("--timeout", type=int, default=10)
    serp_cmd.add_argument("--output", default="output")
    serp_cmd.set_defaults(func=cmd_serp)

    perf_cmd = sub.add_parser("perf", help="TTFB, peso, compresión y recursos")
    perf_cmd.add_argument("target")
    perf_cmd.add_argument("--timeout", type=int, default=10)
    perf_cmd.add_argument("--output", default="output")
    perf_cmd.set_defaults(func=cmd_perf)

    headers = sub.add_parser("headers", help="seguridad HTTP")
    headers.add_argument("target")
    headers.add_argument("--timeout", type=int, default=10)
    headers.add_argument("--output", default="output")
    headers.set_defaults(func=cmd_headers)

    schema = sub.add_parser("schema", help="JSON-LD y rich preview")
    schema.add_argument("target")
    schema.add_argument("--rich-preview", action="store_true", default=True)
    schema.add_argument("--timeout", type=int, default=10)
    schema.add_argument("--output", default="output")
    schema.set_defaults(func=cmd_schema)

    href = sub.add_parser("hreflang", help="SEO internacional")
    href.add_argument("target")
    href.add_argument("--timeout", type=int, default=10)
    href.add_argument("--output", default="output")
    href.set_defaults(func=cmd_hreflang)

    onpage_cmd = sub.add_parser("onpage", help="auditoría on-page")
    onpage_cmd.add_argument("target")
    onpage_cmd.add_argument("--timeout", type=int, default=10)
    onpage_cmd.add_argument("--output", default="output")
    onpage_cmd.set_defaults(func=cmd_onpage)

    index_cmd = sub.add_parser("index", help="indexación y directivas cruzadas")
    index_cmd.add_argument("target")
    index_cmd.add_argument("--robots", default=None, help="robots.txt local")
    index_cmd.add_argument("--presence", action="store_true")
    index_cmd.add_argument("--timeout", type=int, default=10)
    index_cmd.add_argument("--output", default="output")
    index_cmd.set_defaults(func=cmd_index)

    fix = sub.add_parser("fix", help="Execute con dry-run (--apply para escribir)")
    fix.add_argument("--input", required=True, help="audit.json de referencia")
    fix.add_argument("--output", default="output")
    fix.add_argument("--apply", action="store_true")
    fix.add_argument("--dest", default=None, help="carpeta destino del proyecto")
    fix.add_argument("--yes", action="store_true", help="confirmación no interactiva")
    fix.set_defaults(func=cmd_fix)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "max_pages", None) is not None:
        if args.max_pages < 1 or args.max_pages > 500:
            parser.error("--max-pages debe estar entre 1 y 500")
    try:
        args.func(args)
    except (ValueError, PermissionError) as exc:
        raise SystemExit("Error: %s" % exc)


if __name__ == "__main__":
    main()
