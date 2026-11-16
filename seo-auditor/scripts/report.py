from pathlib import Path
from datetime import datetime, timezone
import json, re

WEIGHTS={"critical":10,"high":6,"medium":3,"low":1}
def score(findings):
    # Heurística: no pretende estimar rankings; penaliza hallazgos confirmados.
    penalty=sum(WEIGHTS.get(f.get("severity","low"),1) for f in findings if f.get("confidence")!="low")
    return max(0,100-min(100,penalty))

def write_report(result, output_dir):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    findings=result.get("findings",[])
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    payload={"generated_at":datetime.now(timezone.utc).isoformat(),"score":score(findings),"result":result}
    (out/"audit.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Informe SEO Auditor","",f"- Generado (UTC): {payload['generated_at']}",f"- Puntuación heurística: **{payload['score']}/100**","",
           "> La puntuación es orientativa y depende de las comprobaciones ejecutadas. No predice posiciones ni sustituye datos de Search Console.","",
           "## Resumen",f"- Páginas/archivos analizados: {result.get('pages_scanned',result.get('files_scanned',0))}",f"- Hallazgos: {len(findings)}","",
           "## Hallazgos"]
    if not findings: lines.append("No se han detectado hallazgos con las comprobaciones ejecutadas.")
    for f in sorted(findings,key=lambda x:WEIGHTS.get(x.get("severity","low"),1),reverse=True):
        lines += [f"### [{f.get('severity','low').upper()}] {f.get('title','Hallazgo')}",
                  f"- Categoría: {f.get('category','')}",f"- Evidencia: {f.get('evidence','')}",
                  f"- URL/archivo: {f.get('url','')}",f"- Confianza: {f.get('confidence','medium')}",
                  f"- Impacto: {f.get('impact','medium')} · Esfuerzo: {f.get('effort','medium')}",
                  f"- Recomendación: {f.get('recommendation','')}",""]
    lines += ["## Limitaciones","- No se han consultado rankings ni Search Console salvo integración explícita.",
              "- El HTML recibido puede no incluir contenido generado por JavaScript.",
              "- GEO se evalúa mediante señales estructurales y editoriales; no se infiere una posición en respuestas de IA."]
    (out/"audit.md").write_text("\\n".join(lines),encoding="utf-8")
    return str(out)
