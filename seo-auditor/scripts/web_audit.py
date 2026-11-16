import re, time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser
try:
    from .models import Finding
    from .security import validate_target
except (ImportError, ValueError):
    from models import Finding
    from security import validate_target

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.title=[]; self.in_title=False
        self.h1=[]; self.in_h1=False; self.meta=[]; self.canonical=[]
        self.images=[]; self.text=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="title": self.in_title=True
        if tag=="h1": self.in_h1=True
        if tag=="a" and a.get("href"): self.links.append(a["href"])
        if tag=="meta": self.meta.append(a)
        if tag=="link" and "canonical" in a.get("rel","").lower(): self.canonical.append(a.get("href",""))
        if tag=="img": self.images.append(a)
    def handle_endtag(self, tag):
        if tag=="title": self.in_title=False
        if tag=="h1": self.in_h1=False
    def handle_data(self, data):
        s=data.strip()
        if s:
            if self.in_title: self.title.append(s)
            if self.in_h1: self.h1.append(s)
            self.text.append(s)

def audit_web(start_url, max_pages=30, max_depth=3, timeout=10, allow_local=False):
    validate_target(start_url, allow_local=allow_local)
    origin=urlparse(start_url); origin_host=origin.netloc
    queue=deque([(start_url,0)]); seen=set(); pages=[]; findings=[]
    while queue and len(pages)<max_pages:
        url,depth=queue.popleft()
        url=urldefrag(url)[0]
        if url in seen: continue
        seen.add(url)
        try:
            validate_target(url, allow_local=allow_local)
            req=Request(url,headers={"User-Agent":"SEOAuditor/1.0 (+authorized SEO audit)","Accept":"text/html,*/*;q=0.8"})
            with urlopen(req,timeout=timeout) as response:
                status=response.status; final=response.geturl()
                content_type=response.headers.get("Content-Type","")
                body=response.read(2_000_000)
            record={"url":url,"final_url":final,"status":status,"content_type":content_type}
            pages.append(record)
            if "html" not in content_type.lower(): continue
            parser=LinkParser()
            parser.feed(body.decode("utf-8",errors="replace"))
            title=" ".join(parser.title); h1=" ".join(parser.h1)
            metas={m.get("name","").lower():m.get("content","") for m in parser.meta}
            if not title:
                findings.append(Finding("WEB-TITLE-001","content","high","Falta title","No se detectó <title>.",url,"Añade un title único y descriptivo.",url,"high","low","high").to_dict())
            if not h1:
                findings.append(Finding("WEB-H1-001","content","medium","No se detecta H1","No se detectó un H1 en el HTML recibido.",url,"Revisa la jerarquía de encabezados.",url).to_dict())
            if "description" not in metas or not metas["description"].strip():
                findings.append(Finding("WEB-META-001","content","low","Falta meta description","No se detectó meta description.",url,"Añade una descripción útil.",url).to_dict())
            if metas.get("robots","").lower().find("noindex")>=0:
                findings.append(Finding("WEB-NOINDEX-001","technical","high","Directiva noindex","Meta robots contiene noindex.",url,"Confirma si la página debe excluirse del índice.",url).to_dict())
            for i,img in enumerate(parser.images,1):
                if "alt" not in img:
                    findings.append(Finding(f"WEB-ALT-{i:03d}","content","low","Imagen sin alt",f"Imagen #{i} sin atributo alt.",url,"Añade alt si aporta información; alt vacío si es decorativa.",url).to_dict())
            if depth<max_depth:
                for href in parser.links:
                    absolute=urljoin(final,href)
                    p=urlparse(absolute)
                    if p.scheme in ("http","https") and p.netloc==origin_host:
                        clean=urldefrag(absolute)[0]
                        if clean not in seen: queue.append((clean,depth+1))
        except Exception as exc:
            findings.append(Finding("WEB-FETCH-001","technical","medium","No se pudo recuperar la URL",str(exc),url,"Comprueba disponibilidad, DNS, TLS y permisos de rastreo.",url,"high","medium","medium").to_dict())
    return {"start_url":start_url,"pages_scanned":len(pages),"pages":pages,"findings":findings}
