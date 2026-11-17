"""Puerta de entrega para una web estática: comprueba lo medible sin navegador.

Uso:
    py premium-web-designer/scripts/delivery_check.py <carpeta> [--public] [--json]

Sin `--public` la puerta asume un prototipo local y deja en aviso el mínimo de un
sitio publicado (canonical, Open Graph con imagen, robots.txt y sitemap.xml).
Con `--public` esos cuatro pasan a `must` y bloquean la entrega.

Código de salida: 0 si no falla ninguna comprobación `must`, 1 si falla alguna,
2 si la carpeta no existe o no contiene HTML.

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
        self.first_anchor: dict[str, str] | None = None
        self._buffer: list[str] = []
        self._capture: str | None = None
        self._jsonld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: (value or "") for key, value in attrs}

        if tag == "html":
            self.lang = values.get("lang", "")
        elif tag == "title":
            self._capture = "title"
            self._buffer = []
        elif tag == "meta":
            self.metas.append(values)
        elif tag == "link":
            self.links.append(values)
        elif tag == "script":
            self.scripts.append(values)
            if values.get("type", "").lower() == "application/ld+json":
                self._jsonld = True
                self._capture = "jsonld"
                self._buffer = []
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._capture = "heading"
            self._buffer = []
        elif tag == "img":
            self.images += 1
            if "alt" not in values:
                self.images_without_alt += 1
        elif tag == "a" and self.first_anchor is None:
            self.first_anchor = values

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._capture == "title":
            self.title = " ".join("".join(self._buffer).split())
            self._capture = None
        elif tag == "script" and self._jsonld:
            self.jsonld.append("".join(self._buffer))
            self._jsonld = False
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
                "severity": severity,
                "ok": ok,
                "title": title,
                "detail": detail,
            }
        )

    @property
    def failures(self) -> list[dict[str, str]]:
        return [item for item in self.items if not item["ok"]]

    def must_failures(self) -> list[dict[str, str]]:
        return [item for item in self.failures if item["severity"] == MUST]


def find_files(root: Path, suffix: str) -> list[Path]:
    found = []
    for path in root.rglob(f"*{suffix}"):
        if any(part in SKIP_DIRS for part in path.parts):
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
        SHOULD,
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

    h1_count = sum(1 for level, _ in page.headings if level == 1)
    result.add(
        "HTML-010",
        MUST,
        h1_count == 1,
        "Exactamente un h1",
        f"{h1_count} encontrados",
    )

    skipped_levels = ""
    previous = 0
    for level, text in page.headings:
        if previous and level > previous + 1:
            skipped_levels = f"salto h{previous} → h{level} en «{text[:40]}»"
            break
        previous = level
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

    invalid_jsonld = ""
    for block in page.jsonld:
        try:
            json.loads(block)
        except json.JSONDecodeError as error:
            invalid_jsonld = str(error)
            break
    result.add(
        "HTML-013",
        SHOULD,
        bool(page.jsonld) and not invalid_jsonld,
        "JSON-LD presente y válido",
        invalid_jsonld or ("ausente" if not page.jsonld else f"{len(page.jsonld)} bloques"),
    )

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
    css = "\n".join(read_text(path) for path in find_files(root, ".css"))

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
        lines.append(f"[{marker}] {item['severity']:<6} {item['id']} {item['title']}{detail}")

    must_failed = result.must_failures()
    should_failed = [item for item in result.failures if item["severity"] == SHOULD]
    nice_failed = [item for item in result.failures if item["severity"] == NICE]

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
