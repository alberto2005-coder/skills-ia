# -*- coding: utf-8 -*-
"""Compare / monitor: diff entre dos `audit.json`.

Clasifica cada comprobación en mejorado / empeorado / nuevo / resuelto, y
compara puntuación y veredicto. Funciona sin red: solo lee los JSON guardados.
"""
from __future__ import annotations

import json
from pathlib import Path

STATUS_LABEL = {"pass": "aprobado", "fail": "falla", "skip": "no aplica"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _index(payload):
    out = {}
    for rec in payload.get("checks") or []:
        out[(rec.get("id", ""), rec.get("url", ""))] = rec
    return out


def compare(old, new):
    """Devuelve el diff estructurado entre dos payloads de auditoría."""
    before = _index(old)
    after = _index(new)
    entries = []
    counts = {"mejorado": 0, "empeorado": 0, "nuevo": 0, "resuelto": 0,
              "eliminado": 0, "igual": 0}

    for key in sorted(set(before) | set(after)):
        old_rec = before.get(key)
        new_rec = after.get(key)
        check_id, url = key
        if old_rec and new_rec:
            old_status = old_rec.get("status")
            new_status = new_rec.get("status")
            if old_status == new_status:
                counts["igual"] += 1
                continue
            if old_status == "fail" and new_status == "pass":
                kind = "mejorado"
            elif old_status == "pass" and new_status == "fail":
                kind = "empeorado"
            else:
                kind = "mejorado" if new_status == "pass" else "empeorado"
            entries.append({
                "tipo": kind, "id": check_id, "url": url,
                "antes": old_status, "ahora": new_status,
                "severidad": new_rec.get("severity_level") or old_rec.get("severity_level"),
                "titulo": new_rec.get("title") or old_rec.get("title"),
                "evidencia_antes": old_rec.get("evidence", ""),
                "evidencia_ahora": new_rec.get("evidence", ""),
                "citation": new_rec.get("citation") or old_rec.get("citation", ""),
            })
            counts[kind] += 1
        elif new_rec:
            kind = "nuevo" if new_rec.get("status") != "pass" else "igual"
            if new_rec.get("status") == "fail":
                entries.append({
                    "tipo": "nuevo", "id": check_id, "url": url,
                    "antes": None, "ahora": new_rec.get("status"),
                    "severidad": new_rec.get("severity_level"),
                    "titulo": new_rec.get("title"),
                    "evidencia_antes": "",
                    "evidencia_ahora": new_rec.get("evidence", ""),
                    "citation": new_rec.get("citation", ""),
                })
                counts["nuevo"] += 1
            else:
                counts["igual"] += 1
        else:
            if old_rec.get("status") == "fail":
                entries.append({
                    "tipo": "resuelto", "id": check_id, "url": url,
                    "antes": old_rec.get("status"), "ahora": None,
                    "severidad": old_rec.get("severity_level"),
                    "titulo": old_rec.get("title"),
                    "evidencia_antes": old_rec.get("evidence", ""),
                    "evidencia_ahora": "",
                    "citation": old_rec.get("citation", ""),
                })
                counts["resuelto"] += 1
            else:
                counts["eliminado"] += 1

    result = {
        "schema": "seo-auditor/compare",
        "schema_version": "1.0",
        "before": {
            "generated_at": old.get("generated_at"),
            "target": old.get("target"),
            "score": old.get("score"),
            "verdict": old.get("verdict"),
        },
        "after": {
            "generated_at": new.get("generated_at"),
            "target": new.get("target"),
            "score": new.get("score"),
            "verdict": new.get("verdict"),
        },
        "score_delta": round(float(new.get("score") or 0) - float(old.get("score") or 0), 1),
        "verdict_changed": old.get("verdict") != new.get("verdict"),
        "counts": counts,
        "entries": entries,
        "new_must_fails": [e for e in entries
                           if e["tipo"] in ("empeorado", "nuevo")
                           and e.get("severidad") == "must"],
    }
    return result


def render_markdown(diff):
    lines = [
        "# Comparativa de auditorías",
        "",
        "- Antes: %s (`%s`) — **%s/100** %s" % (
            diff["before"].get("generated_at"), diff["before"].get("target"),
            diff["before"].get("score"), diff["before"].get("verdict")),
        "- Ahora: %s (`%s`) — **%s/100** %s" % (
            diff["after"].get("generated_at"), diff["after"].get("target"),
            diff["after"].get("score"), diff["after"].get("verdict")),
        "- Delta de puntuación: **%+.1f**%s" % (
            diff["score_delta"],
            " · el veredicto cambió" if diff.get("verdict_changed") else ""),
        "",
        "| Resultado | Nº |",
        "|---|---:|",
    ]
    for key in ("mejorado", "empeorado", "nuevo", "resuelto", "eliminado", "igual"):
        lines.append("| %s | %s |" % (key, diff["counts"].get(key, 0)))
    lines.append("")

    groups = (
        ("Nuevos fallos `must`", diff.get("new_must_fails") or []),
        ("Empeorado", [e for e in diff["entries"] if e["tipo"] == "empeorado"]),
        ("Nuevo", [e for e in diff["entries"] if e["tipo"] == "nuevo"]),
        ("Mejorado", [e for e in diff["entries"] if e["tipo"] == "mejorado"]),
        ("Resuelto", [e for e in diff["entries"] if e["tipo"] == "resuelto"]),
    )
    for title, entries in groups:
        lines += ["## %s — %d" % (title, len(entries)), ""]
        if not entries:
            lines += ["_Sin cambios en este grupo._", ""]
            continue
        lines += ["| Check | URL | Antes | Ahora | Evidencia ahora |", "|---|---|---|---|---|"]
        for entry in entries:
            lines.append("| `%s` %s | %s | %s | %s | %s |" % (
                entry["id"], entry.get("titulo") or "",
                entry.get("url") or "—",
                STATUS_LABEL.get(entry.get("antes"), entry.get("antes") or "—"),
                STATUS_LABEL.get(entry.get("ahora"), entry.get("ahora") or "—"),
                (entry.get("evidencia_ahora") or "—").replace("|", "/")[:200]))
        lines.append("")
    lines += ["> El diff se calcula sobre `checks` guardados: no se vuelve a "
              "consultar la web.", ""]
    return "\n".join(lines)


def write(diff, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "compare.json").write_text(json.dumps(diff, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    (out / "compare.md").write_text(render_markdown(diff), encoding="utf-8")
    return str(out)
