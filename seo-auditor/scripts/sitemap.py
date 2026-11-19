from urllib.request import Request
import xml.etree.ElementTree as ET
try:
    from .security import build_safe_opener, validate_target
except (ImportError, ValueError):
    from security import build_safe_opener, validate_target


def parse_sitemap(source: str, timeout=10, allow_local=False):
    if source.startswith(("http://", "https://")):
        validate_target(source, allow_local=allow_local)
        req = Request(source, headers={"User-Agent": "SEOAuditor/1.0"})
        # `urlopen` crudo seguía redirecciones sin volver a validar el destino:
        # un sitemap público podía acabar en una IP privada.
        with build_safe_opener(allow_local).open(req, timeout=timeout) as r:
            data = r.read(5_000_000)
    else:
        from pathlib import Path
        data = Path(source).read_bytes()
    root = ET.fromstring(data)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [x.text for x in root.findall(".//sm:loc", ns) if x.text]
    return {"type": "sitemapindex" if root.tag.endswith("sitemapindex") else "urlset",
            "count": len(urls), "urls": urls}
