import argparse, json, re, sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from .source_audit import audit_source
    from .web_audit import audit_web
    from .report import write_report
except (ImportError, ValueError):
    _curr = Path(__file__).resolve().parent
    if str(_curr) not in sys.path:
        sys.path.insert(0, str(_curr))
    from source_audit import audit_source
    from web_audit import audit_web
    from report import write_report

def main():
    p=argparse.ArgumentParser(prog="seo-auditor",description="Auditor SEO Web / Source / Local / Hybrid")
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("audit")
    a.add_argument("target")
    a.add_argument("--mode",choices=["web","source","local","hybrid"],default="web")
    a.add_argument("--base-url",default=None,help="URL loopback para hybrid")
    a.add_argument("--max-pages",type=int,default=30)
    a.add_argument("--max-depth",type=int,default=3)
    a.add_argument("--timeout",type=int,default=10)
    a.add_argument("--output",default="reports")
    args=p.parse_args()
    if args.max_pages<1 or args.max_pages>500: p.error("--max-pages debe estar entre 1 y 500")
    result={"mode":args.mode,"findings":[]}
    if args.mode=="web":
        result.update(audit_web(args.target,args.max_pages,args.max_depth,args.timeout,False))
    elif args.mode=="local":
        result.update(audit_web(args.target,args.max_pages,args.max_depth,args.timeout,True))
    elif args.mode=="source":
        result.update(audit_source(args.target))
    elif args.mode=="hybrid":
        result.update(audit_source(args.target))
        if not args.base_url: p.error("hybrid requiere --base-url http://localhost:PUERTO")
        runtime=audit_web(args.base_url,args.max_pages,args.max_depth,args.timeout,True)
        result["runtime"]=runtime
        result["findings"].extend(runtime["findings"])
        result["pages_scanned"]=runtime["pages_scanned"]
    slug=re.sub(r"[^a-zA-Z0-9_-]+","-",Path(args.target.rstrip("/")).name or "website")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out=write_report(result,Path(args.output)/slug/stamp)
    print(f"Auditoría terminada. Informe: {out}/audit.md")
    print(f"Hallazgos: {len(result.get('findings',[]))}")
if __name__=="__main__": main()
