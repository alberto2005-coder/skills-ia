import json, re
from pathlib import Path
from html.parser import HTMLParser
try:
    from .models import Finding
except (ImportError, ValueError):
    from models import Finding

class JSONLDParser(HTMLParser):
    def __init__(self): super().__init__(); self.active=False; self.buf=[]; self.blocks=[]
    def handle_starttag(self,tag,attrs):
        if tag=="script" and dict(attrs).get("type","").lower()=="application/ld+json":
            self.active=True; self.buf=[]
    def handle_data(self,data):
        if self.active: self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=="script" and self.active:
            self.blocks.append("".join(self.buf)); self.active=False

def inspect_html(path):
    p=JSONLDParser(); p.feed(Path(path).read_text(encoding="utf-8",errors="replace"))
    out=[]
    for i,raw in enumerate(p.blocks,1):
        try:
            data=json.loads(raw)
            out.append({"block":i,"valid_json":True,"types":extract_types(data)})
        except json.JSONDecodeError as e:
            out.append({"block":i,"valid_json":False,"error":str(e)})
    return out

def extract_types(obj):
    found=[]
    if isinstance(obj,dict):
        t=obj.get("@type")
        if isinstance(t,str): found.append(t)
        elif isinstance(t,list): found.extend(map(str,t))
        for v in obj.values(): found.extend(extract_types(v))
    elif isinstance(obj,list):
        for v in obj: found.extend(extract_types(v))
    return sorted(set(found))
