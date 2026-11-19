"""Puerta de entrega para una web estática: comprueba lo medible sin navegador.

Uso:
    py premium-web-designer/scripts/delivery_check.py <carpeta> [--public] [--json]

Sin `--public` la puerta asume un prototipo local y deja en aviso el mínimo de un
sitio publicado (canonical, Open Graph con imagen, robots.txt y sitemap.xml).
Con `--public` esos cuatro pasan a `must` y bloquean la entrega.

Código de salida: 0 si no falla ninguna comprobación `must`, 1 si falla alguna
(incluido HTML-000 cuando la carpeta no contiene HTML), 2 si la carpeta no
existe.

Solo cubre lo estático. Desbordamiento, líneas del titular, solapes y foco se
miden en el navegador con el protocolo de `premium-qa`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

MUST, SHOULD, NICE = "must", "should", "nice"
GATE_SEVERITY = {MUST: "high", SHOULD: "medium", NICE: "low"}

HEADER_FILES = ("_headers", "netlify.toml", "vercel.json")
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".cache", "vendor"}

TITLE_RANGE = (15, 65)
DESCRIPTION_RANGE = (70, 165)
TAP_TARGET = re.compile(r"min-height:\s*(?:2\.75rem|44px)")
STICKY = re.compile(r"position:\s*(?:sticky|fixed)")
SCROLL_OFFSET = re.compile(r"scroll-(?:padding|margin)-top")
LOCAL_ASSET = re.compile(r"^(?!https?:|//|data:)(.+\.(?:css|js))(\?.*)?$")


class Page(HTMLParser):
    """Recolecta lo que la puerta necesita del documento."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title = ""
        self.metas: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.scripts: list[dict[str, str]] = []
        self.headings: list[tuple[int, str]] = []
        self.images = 0
        self.images_without_alt = 0
        self.jsonld: list[str] = []
        self.styles: list[str] = []
        self.first_anchor: dict[str, str] | None = None
        self._buffer: list[str] = []
        self._capture: str | None = None
        self._jsonld = False

    # Despacho por etiqueta: el parser es el mismo, pero ninguna rama vive
    # dentro de las demás.
    _START_TAGS = {
        "html": "_start_html",
        "title": "_capture_title",
        "meta": "_start_meta",
        "link": "_start_link",
        "script": "_start_script",
        "style": "_capture_style",
        "h1": "_capture_heading",
        "h2": "_capture_heading",
        "h3": "_capture_heading",
        "h4": "_capture_heading",
        "h5": "_capture_heading",
        "h6": "_capture_heading",
        "img": "_start_img",
        "a": "_start_anchor",
    }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: (value or "") for key, value in attrs}
        handler = self._START_TAGS.get(tag)
        if handler is not None:
            getattr(self, handler)(values)

    def _start_html(self, values: dict[str, str]) -> None:
        self.lang = values.get("lang", "")

    def _capture_title(self, values: dict[str, str]) -> None:
        self._capture = "title"
        self._buffer = []

    def _start_meta(self, values: dict[str, str]) -> None:
        self.metas.append(values)

    def _start_link(self, values: dict[str, str]) -> None:
        self.links.append(values)

    def _start_script(self, values: dict[str, str]) -> None:
        self.scripts.append(values)
        if values.get("type", "").lower() == "application/ld+json":
            self._jsonld = True
            self._capture = "jsonld"
            self._buffer = []

    def _capture_style(self, values: dict[str, str]) -> None:
        self._capture = "style"
        self._buffer = []

    def _capture_heading(self, values: dict[str, str]) -> None:
        self._capture = "heading"
        self._buffer = []

    def _start_img(self, values: dict[str, str]) -> None:
        self.images += 1
        if "alt" not in values:
            self.images_without_alt += 1

    def _start_anchor(self, values: dict[str, str]) -> None:
        if self.first_anchor is None:
            self.first_anchor = values

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._capture == "title":
            self.title = " ".join("".join(self._buffer).split())
            self._capture = None
        elif tag == "script" and self._jsonld:
            self.jsonld.append("".join(self._buffer))
            self._jsonld = False
            self._capture = None
        elif tag == "style" and self._capture == "style":
            self.styles.append("".join(self._buffer))
            self._capture = None
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._capture == "heading":
            text = " ".join("".join(self._buffer).split())
            self.headings.append((int(tag[1]), text))
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)


class Result:
    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def add(self, check_id: str, severity: str, ok: bool, title: str, detail: str = "") -> None:
        self.items.append(
            {
                "id": check_id,
                "severity": GATE_SEVERITY.get(severity, "medium"),
                "gate": severity,
                "ok": ok,
                "title": title,
                "detail": detail,
            }
        )

    @property
    def failures(self) -> list[dict[str, str]]:
        return [item for item in self.items if not item["ok"]]

    def must_failures(self) -> list[dict[str, str]]:
        return [item for item in self.failures if item["gate"] == MUST]


def find_files(root: Path, suffix: str) -> list[Path]:
    found = []
    for path in root.rglob(f"*{suffix}"):
        # Solo las partes RELATIVAS a la carpeta entregada: si la raíz era
        # `.../dist/site`, el "dist" del path absoluto descartaba todo el HTML
        # y la puerta fallaba con HTML-000 sobre un sitio correcto.
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            parts = path.parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        found.append(path)
    return sorted(found)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def check_page(root: Path, result: Result, public: bool = False) -> None:
    pages = find_files(root, ".html")
    index = next((path for path in pages if path.name == "index.html"), pages[0] if pages else None)

    if index is None:
        result.add("HTML-000", MUST, False, "No hay ningún documento HTML")
        return

    page = Page()
    page.feed(read_text(index))
    page.close()

    assets, versioned = _link_assets(page)
    _check_meta(result, page, public)
    _check_structure(result, page)
    _check_assets(result, page, assets, versioned)


def _link_assets(page: Page) -> tuple[list[str], list[str]]:
    assets = sorted(
        {LOCAL_ASSET.match(link.get("href", "")).group(1) for link in page.links if LOCAL_ASSET.match(link.get("href", ""))}
        | {LOCAL_ASSET.match(script.get("src", "")).group(1) for script in page.scripts if LOCAL_ASSET.match(script.get("src", ""))}
    )
    references = [link.get("href", "") for link in page.links] + [
        script.get("src", "") for script in page.scripts
    ]
    versioned = [
        reference.split("?")[0]
        for reference in references
        if "?" in reference and reference.split("?")[0].endswith((".css", ".js"))
    ]
    return assets, versioned


def _check_meta(result: Result, page: Page, public: bool) -> None:
    result.add(
        "HTML-001",
        MUST,
        bool(page.lang.strip()),
        "Atributo lang en <html>",
        f"lang={page.lang!r}" if page.lang else "ausente",
    )

    result.add(
        "HTML-002",
        MUST,
        bool(page.title),
        "<title> presente",
        page.title or "ausente",
    )

    if page.title:
        low, high = TITLE_RANGE
        result.add(
            "HTML-003",
            SHOULD,
            low <= len(page.title) <= high,
            f"Longitud del título entre {low} y {high} caracteres",
            f"{len(page.title)} caracteres",
        )

    description = next(
        (meta.get("content", "") for meta in page.metas if meta.get("name", "").lower() == "description"),
        "",
    )
    result.add(
        "HTML-004",
        # En un sitio publicado la meta description es parte del mínimo: con
        # `--public` avisaba pero no bloqueaba.
        MUST if public else SHOULD,
        bool(description.strip()),
        "Meta description",
        f"{len(description)} caracteres" if description else "ausente",
    )
    if description:
        low, high = DESCRIPTION_RANGE
        result.add(
            "HTML-005",
            NICE,
            low <= len(description) <= high,
            f"Longitud de la descripción entre {low} y {high}",
            f"{len(description)} caracteres",
        )

    viewport = any(meta.get("name", "").lower() == "viewport" for meta in page.metas)
    result.add("HTML-006", MUST, viewport, "Meta viewport", "ausente" if not viewport else "")

    canonical = any(link.get("rel", "").lower() == "canonical" for link in page.links)
    result.add(
        "HTML-007",
        MUST if public else SHOULD,
        canonical,
        "Enlace canonical",
        "ausente" if not canonical else "",
    )

    og = {
        meta.get("property", "").lower()
        for meta in page.metas
        if meta.get("property", "").lower().startswith("og:")
    }
    result.add(
        "HTML-008",
        MUST if public else SHOULD,
        {"og:title", "og:description", "og:image"} <= og,
        "Open Graph completo (title, description, image)",
        f"presentes: {sorted(og) or 'ninguno'}",
    )

    twitter = any(meta.get("name", "").lower().startswith("twitter:") for meta in page.metas)
    result.add("HTML-009", NICE, twitter, "Twitter card", "ausente" if not twitter else "")


def _check_structure(result: Result, page: Page) -> None:
    h1_count = sum(1 for level, _ in page.headings if level == 1)
    result.add(
        "HTML-010",
        MUST,
        h1_count == 1,
        "Exactamente un h1",
        f"{h1_count} encontrados",
    )

    skipped_levels = _heading_gap(page.headings)
    result.add(
        "HTML-011",
        SHOULD,
        not skipped_levels,
        "Jerarquía de encabezados sin saltos",
        skipped_levels,
    )

    result.add(
        "HTML-012",
        MUST,
        page.images_without_alt == 0,
        "Todas las imágenes con alt",
        f"{page.images_without_alt} de {page.images} sin alt" if page.images else "sin imágenes",
    )

    ok_jsonld, detail = _jsonld_status(page)
    result.add("HTML-013", SHOULD, ok_jsonld, "JSON-LD presente y válido", detail)


def _heading_gap(headings: list[tuple[int, str]]) -> str:
    previous = 0
    for level, text in headings:
        if previous and level > previous + 1:
            return f"salto h{previous} → h{level} en «{text[:40]}»"
        previous = level
    return ""


def _jsonld_status(page: Page) -> tuple[bool, str]:
    invalid = ""
    for block in page.jsonld:
        try:
            json.loads(block)
        except json.JSONDecodeError as error:
            invalid = str(error)
            break
    if invalid:
        return False, invalid
    if not page.jsonld:
        return False, "ausente"
    return True, f"{len(page.jsonld)} bloques"


def _check_assets(result: Result, page: Page, assets: list[str], versioned: list[str]) -> None:
    skip_link = bool(page.first_anchor) and page.first_anchor.get("href", "").startswith("#")
    result.add("HTML-014", SHOULD, skip_link, "Enlace de salto al contenido", "" if skip_link else "el primer enlace no apunta a un ancla")

    missing_versions = [asset for asset in assets if asset not in versioned]
    result.add(
        "HTML-015",
        SHOULD,
        not missing_versions,
        "CSS y JS locales con versión en la URL",
        f"sin versión: {', '.join(missing_versions)}" if missing_versions else "",
    )


def check_css(root: Path, result: Result) -> None:
    css_files = "\n".join(read_text(path) for path in find_files(root, ".css"))
    # Los estilos `<style>` no pasaban por ninguna comprobación: un sitio que
    # declaraba `:focus-visible` inline fallaba CSS-001 igualmente.
    inline = []
    for path in find_files(root, ".html"):
        page = Page()
        try:
            page.feed(read_text(path))
            page.close()
        except Exception:
            continue
        inline.extend(page.styles)
    css = css_files + "\n" + "\n".join(inline)

    if not css.strip():
        result.add("CSS-000", NICE, False, "Sin hojas de estilo locales", "la comprobación de estilos se omite")
        return

    result.add(
        "CSS-001",
        SHOULD,
        ":focus-visible" in css,
        "Estados de foco visibles (:focus-visible)",
        "" if ":focus-visible" in css else "no se declara ninguno",
    )

    result.add(
        "CSS-002",
        SHOULD,
        "prefers-reduced-motion" in css,
        "Respeto a prefers-reduced-motion",
        "" if "prefers-reduced-motion" in css else "ausente",
    )

    sticky = bool(STICKY.search(css))
    offset = bool(SCROLL_OFFSET.search(css))
    result.add(
        "CSS-003",
        SHOULD,
        not sticky or offset,
        "Compensación de cabecera pegajosa en anclas",
        "hay position: sticky/fixed sin scroll-padding-top ni scroll-margin-top" if sticky and not offset else "",
    )

    result.add(
        "CSS-004",
        NICE,
        bool(TAP_TARGET.search(css)),
        "Altura mínima de 44px declarada para controles",
        "no se detecta min-height: 2.75rem/44px" if not TAP_TARGET.search(css) else "",
    )

    result.add(
        "CSS-005",
        NICE,
        len(re.findall(r"@media", css)) >= 2,
        "Al menos dos puntos de ruptura",
        f"{len(re.findall(r'@media', css))} media queries",
    )


def check_files(root: Path, result: Result, public: bool = False) -> None:
    robots = root / "robots.txt"
    robots_text = read_text(robots) if robots.is_file() else ""
    result.add(
        "FILE-001",
        MUST if public else SHOULD,
        robots.is_file(),
        "robots.txt",
        "ausente" if not robots.is_file() else "",
    )
    result.add(
        "FILE-002",
        SHOULD,
        robots.is_file() and "sitemap:" in robots_text.lower(),
        "robots.txt declara el sitemap",
        "sin línea Sitemap:" if robots.is_file() else "robots.txt ausente",
    )

    sitemap = root / "sitemap.xml"
    result.add(
        "FILE-003",
        MUST if public else SHOULD,
        sitemap.is_file(),
        "sitemap.xml",
        "ausente" if not sitemap.is_file() else "",
    )

    llms = root / "llms.txt"
    result.add("FILE-004", NICE, llms.is_file(), "llms.txt para superficies de IA", "ausente" if not llms.is_file() else "")


def check_headers(root: Path, result: Result, public: bool = False) -> None:
    """Cabeceras de seguridad declaradas por el hosting. Solo en modo --public."""
    if not public:
        return

    files = [root / name for name in HEADER_FILES if (root / name).is_file()]
    text = "\n".join(read_text(path) for path in files).lower()
    declared = ", ".join(path.name for path in files) or "ninguno"

    result.add(
        "HDR-001",
        SHOULD,
        bool(files),
        "Fichero de cabeceras del sitio (_headers, netlify.toml o vercel.json)",
        declared,
    )

    csp = "content-security-policy" in text
    result.add(
        "HDR-002",
        SHOULD,
        csp,
        "Content-Security-Policy declarada",
        "presente" if csp else "ausente",
    )

    hsts = "strict-transport-security" in text
    if not hsts:
        detail = "ausente"
    elif "max-age" not in text:
        detail = "sin max-age"
    else:
        detail = "presente"
    result.add(
        "HDR-003",
        SHOULD,
        hsts and "max-age" in text,
        "Strict-Transport-Security con max-age",
        detail,
    )


def render(root: Path, result: Result, public: bool = False) -> str:
    icons = {True: "OK  ", False: "FALLA"}
    mode = "sitio publicado" if public else "prototipo local (usa --public al publicar)"
    lines = [f"Puerta de entrega — {root}", f"Modo: {mode}", ""]

    for item in result.items:
        marker = icons[item["ok"]]
        detail = f" · {item['detail']}" if item["detail"] else ""
        lines.append(f"[{marker}] {item['gate']:<6} {item['id']} {item['title']}{detail}")

    must_failed = result.must_failures()
    should_failed = [item for item in result.failures if item["gate"] == SHOULD]
    nice_failed = [item for item in result.failures if item["gate"] == NICE]

    lines += [
        "",
        f"Resumen: {len(must_failed)} must fallidos · {len(should_failed)} avisos · {len(nice_failed)} sugerencias",
    ]

    if must_failed:
        lines.append("Entrega bloqueada hasta resolver los must.")
    else:
        lines.append("Ninguna comprobación must falla. Falta la medición en navegador de premium-qa.")

    return "\n".join(lines)


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Puerta de entrega para una web estática.")
    parser.add_argument("target", help="Carpeta del sitio")
    parser.add_argument(
        "--public",
        action="store_true",
        help="Exige el mínimo de un sitio publicado: canonical, Open Graph con imagen, robots.txt y sitemap.xml pasan a must.",
    )
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv)

    root = Path(args.target)

    if not root.is_dir():
        print(f"No existe la carpeta: {root}", file=sys.stderr)
        return 2

    result = Result()
    check_page(root, result, public=args.public)
    check_css(root, result)
    check_files(root, result, public=args.public)
    check_headers(root, result, public=args.public)

    if args.json:
        print(
            json.dumps(
                {
                    "target": str(root),
                    "public": args.public,
                    "must_failed": len(result.must_failures()),
                    "items": result.items,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(render(root, result, public=args.public))

    return 1 if result.must_failures() else 0


if __name__ == "__main__":
    sys.exit(main())
