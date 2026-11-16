import os, re, json
from pathlib import Path
from html.parser import HTMLParser
try:
    from .models import Finding
except (ImportError, ValueError):
    from models import Finding

EXCLUDED_DIRS = {".git", "node_modules", "vendor", "dist", "build", "coverage",
                 ".next", ".nuxt", ".venv", "venv", "__pycache__", ".idea"}
SENSITIVE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
                   "credentials.json", "secrets.json"}
HTML_EXTS = {".html", ".htm", ".php", ".twig", ".njk", ".liquid", ".jsx", ".tsx", ".vue", ".svelte"}

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts=[]; self.in_title=False; self.h1=[]; self.in_h1=False
        self.meta=[]; self.links=[]; self.canonicals=[]; self.jsonld=[]
        self.robots=[]; self.images=[]; self.text_chars=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="title": self.in_title=True
        if tag=="h1": self.in_h1=True
        if tag=="meta": self.meta.append(a)
        if tag=="link" and "canonical" in a.get("rel","").lower(): self.canonicals.append(a.get("href",""))
        if tag=="a" and a.get("href"): self.links.append(a["href"])
        if tag=="img": self.images.append(a)
        if tag=="script" and a.get("type","").lower()=="application/ld+json": self.jsonld.append("pending")
    def handle_endtag(self, tag):
        if tag=="title": self.in_title=False
        if tag=="h1": self.in_h1=False
    def handle_data(self, data):
        s=data.strip()
        if self.in_title and s: self.title_parts.append(s)
        if self.in_h1 and s: self.h1.append(s)
        self.text_chars += len(s)

def analyze_html(path: Path, rel: str) -> list[Finding]:
    findings=[]
    try:
        raw=path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    p=PageParser()
    try: p.feed(raw)
    except Exception: pass
    title=" ".join(p.title_parts).strip()
    h1=" ".join(p.h1).strip()
    metas={m.get("name","").lower():m.get("content","") for m in p.meta}
    if not title:
        findings.append(Finding("SRC-TITLE-001","content","high","Falta la etiqueta title",
            f"Archivo: {rel}","Añade un title único y descriptivo.",rel,"high","low","high"))
    elif len(title)>60:
        findings.append(Finding("SRC-TITLE-002","content","low","Title posiblemente largo",
            f"{len(title)} caracteres en {rel}","Revisa si puede ser más conciso sin perder intención.",rel,"medium","low","low"))
    if not h1:
        findings.append(Finding("SRC-H1-001","content","medium","No se detecta H1",
            f"Archivo: {rel}","Incluye un encabezado principal que describa el propósito de la página.",rel,"medium","low","medium"))
    if "description" not in metas or not metas["description"].strip():
        findings.append(Finding("SRC-META-001","content","low","Falta meta description",
            f"Archivo: {rel}","Añade una descripción útil; no garantiza un snippet concreto.",rel,"high","low","low"))
    if metas.get("robots","").lower().find("noindex")>=0:
        findings.append(Finding("SRC-ROBOTS-001","technical","high","Directiva noindex en el código",
            f"meta robots={metas['robots']} en {rel}","Confirma que la exclusión es intencionada; no la elimines sin validar el objetivo.",rel,"high","low","high"))
    if not p.canonicals:
        findings.append(Finding("SRC-CANON-001","technical","low","No se detecta canonical",
            f"Archivo: {rel}","Comprueba si esta plantilla necesita canonical absoluto y coherente.",rel,"medium","low","low"))
    for i,img in enumerate(p.images,1):
        if not img.get("alt"):
            findings.append(Finding(f"SRC-ALT-{i:03d}","content","low","Imagen sin atributo alt",
                f"Imagen #{i} en {rel}","Añade texto alternativo descriptivo cuando la imagen transmita información; usa alt vacío si es decorativa.",rel,"high","low","low"))
    if not raw.strip():
        findings.append(Finding("SRC-EMPTY-001","technical","medium","Archivo HTML vacío",rel,"Comprueba si la plantilla se genera dinámicamente.",rel))
    return findings

def detect_framework(root: Path) -> list[str]:
    checks = {
        "Next.js": ["next.config.js","next.config.mjs","next.config.ts"],
        "Astro": ["astro.config.mjs","astro.config.ts"],
        "Vite/React": ["vite.config.js","vite.config.ts"],
        "Laravel": ["artisan"],
        "WordPress": ["wp-config.php"],
        "Shopify theme": ["config/settings_schema.json"],
    }
    found=[]
    for name, markers in checks.items():
        if any((root/m).exists() for m in markers): found.append(name)
    if (root/"package.json").exists():
        try:
            pkg=json.loads((root/"package.json").read_text(encoding="utf-8"))
            deps={**pkg.get("dependencies",{}),**pkg.get("devDependencies",{})}
            if "next" in deps and "Next.js" not in found: found.append("Next.js")
            if "astro" in deps and "Astro" not in found: found.append("Astro")
            if "react" in deps and not any(x in found for x in ("Next.js","Vite/React")): found.append("React")
        except Exception: pass
    return found or ["HTML/CSS/JS o framework no identificado"]

def audit_source(root: str, max_files: int=500) -> dict:
    base=Path(root).resolve()
    if not base.is_dir(): raise ValueError(f"No es un directorio: {base}")
    findings=[]; pages=[]; count=0
    for current, dirs, names in os.walk(base):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for name in names:
            if name.lower() in SENSITIVE_NAMES or name.startswith(".env"): continue
            path=Path(current)/name
            if path.suffix.lower() not in HTML_EXTS: continue
            count+=1
            if count>max_files: break
            rel=str(path.relative_to(base))
            pages.append(rel)
            findings.extend(analyze_html(path, rel))
        if count>max_files: break
    return {"root":str(base),"frameworks":detect_framework(base),"files_scanned":len(pages),
            "pages":pages,"findings":[f.to_dict() for f in findings]}
