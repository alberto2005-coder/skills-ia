"""Núcleo compartido de `skill-evals`: casos, métricas, colisiones y presupuesto.

Sin red y solo stdlib. El router léxico de `tests/trigger_router.py` se reutiliza
tal cual: es el mismo que usa la suite de activación del repositorio, así que los
números de una evaluación coinciden con los del gate de CI.

Nada aquí escribe ficheros: `design.py`, `run.py` y `report.py` son los CLI.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PACKAGE_ROOT.parent

CASE_FORMAT = "skill-evals-cases"
CASE_VERSION = "1.0"
RUN_FORMAT = "skill-evals-run"

DEFAULT_THRESHOLD = 0.3
KINDS = ("positive", "negative", "boundary", "out_of_domain")
SPLITS = ("train", "test")

CATALOG_TOKEN_LIMIT = 8000
BODY_TOKEN_LIMIT = 5000
BODY_LINE_LIMIT = 500
COLLISION_JACCARD = 0.50
TOP_K = 3


def force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_router(repo_root: Path = REPO_ROOT):
    """Devuelve `(trigger_router, Router)` cargando el fixture del repositorio."""
    tests_dir = repo_root / "tests"
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))
    import trigger_router as tr  # noqa: E402  (tras ajustar sys.path)

    return tr, tr.Router.from_repo(repo_root)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def split_for(case_id: str) -> str:
    """Split determinista 60/40 por id, estable entre ejecuciones y máquinas."""
    digest = hashlib.sha1(case_id.encode("utf-8")).hexdigest()
    return "train" if int(digest[:8], 16) % 100 < 60 else "test"


def build_cases(phrases: dict, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Convierte `tests/phrases.json` en un fichero de casos versionable."""
    skills = phrases.get("skills") or {}
    if not isinstance(skills, dict) or not skills:
        raise ValueError("phrases.json sin bloque «skills»")

    cases: list[dict] = []
    for skill, entry in sorted(skills.items()):
        for index, prompt in enumerate(entry.get("positives") or [], 1):
            case_id = f"pos:{skill}:{index}"
            cases.append({
                "id": case_id,
                "prompt": prompt,
                "expect": skill,
                "kind": "positive",
                "split": split_for(case_id),
            })
        for index, negative in enumerate(entry.get("negatives") or [], 1):
            case_id = f"neg:{skill}:{index}"
            cases.append({
                "id": case_id,
                "prompt": negative["phrase"],
                "expect": negative["winner"],
                "forbid": skill,
                "kind": "negative",
                "split": split_for(case_id),
            })

    for index, prompt in enumerate(phrases.get("out_of_domain") or [], 1):
        case_id = f"ood:{index}"
        cases.append({
            "id": case_id,
            "prompt": prompt,
            "expect": None,
            "kind": "out_of_domain",
            "split": split_for(case_id),
        })

    for case_id, prompt in (("boundary:generic", "lorem ipsum dolor sit amet"), ("boundary:empty", "")):
        cases.append({
            "id": case_id,
            "prompt": prompt,
            "expect": None,
            "kind": "boundary",
            "split": split_for(case_id),
        })

    return {
        "format": CASE_FORMAT,
        "version": CASE_VERSION,
        "threshold": threshold,
        "source": "tests/phrases.json",
        "cases": cases,
    }


def validate_cases(document: dict, known_skills: set[str]) -> list[str]:
    """Problemas de esquema y cobertura; lista vacía si el fichero es válido."""
    problems: list[str] = []
    if document.get("format") != CASE_FORMAT:
        problems.append(f"format debe ser «{CASE_FORMAT}»")
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        return problems + ["sin lista «cases»"]

    seen: set[str] = set()
    covered: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            problems.append(f"caso no es objeto: {case!r}")
            continue
        case_id = case.get("id")
        if not case_id or case_id in seen:
            problems.append(f"id ausente o repetido: {case_id!r}")
        seen.add(case_id)
        if case.get("kind") not in KINDS:
            problems.append(f"{case_id}: kind inválido {case.get('kind')!r}")
        if case.get("split") not in SPLITS:
            problems.append(f"{case_id}: split inválido {case.get('split')!r}")
        if not isinstance(case.get("prompt"), str):
            problems.append(f"{case_id}: prompt debe ser texto")
        expect = case.get("expect")
        if expect is not None:
            if expect not in known_skills:
                problems.append(f"{case_id}: expect «{expect}» no existe")
            elif case.get("kind") == "positive":
                covered.add(expect)
        forbid = case.get("forbid")
        if forbid is not None and forbid not in known_skills:
            problems.append(f"{case_id}: forbid «{forbid}» no existe")

    missing = sorted(known_skills - covered)
    if missing:
        problems.append("skills sin casos positivos: " + ", ".join(missing))
    return problems


def _evaluate_case(router, case: dict, threshold: float) -> dict:
    prompt = case["prompt"]
    ranking = router.ranking(prompt)[:TOP_K]
    expect = case.get("expect")
    forbid = case.get("forbid")
    if not ranking:
        # Sin candidatos (router vacío o prompt degenerado) `ranking[0]`
        # lanzaba IndexError en vez de marcar el caso como fallido.
        return {
            "id": case["id"], "prompt": prompt, "kind": case["kind"],
            "split": case.get("split", "train"), "expect": expect,
            "forbid": forbid, "best": "", "score": 0.0, "rank": 0,
            "sibling": None, "passed": False, "ranking": [],
        }
    best, best_score = ranking[0]

    if expect is None:
        passed = best_score < threshold
        rank = 0
    else:
        # Una negativa se juzga por quién gana, no por su puntuación: la frase
        # puede ser deliberadamente débil y aun así demostrar que la prohibida
        # no se lleva la primera posición.
        passed = best == expect
        if case.get("kind") == "positive":
            passed = passed and best_score >= threshold
        rank = next(
            (position for position, (name, _) in enumerate(router.ranking(prompt), 1) if name == expect),
            0,
        )
        if forbid is not None and best == forbid:
            passed = False

    sibling = None
    if expect is not None and best != expect:
        if router.skills[best].package == router.skills[expect].package:
            sibling = best

    return {
        "id": case["id"],
        "prompt": prompt,
        "kind": case["kind"],
        "split": case.get("split", "train"),
        "expect": expect,
        "forbid": forbid,
        "best": best,
        "score": round(best_score, 4),
        "rank": rank,
        "sibling": sibling,
        "passed": passed,
        "ranking": [{"name": name, "score": round(value, 4)} for name, value in ranking],
    }


def _metrics(results: list[dict], threshold: float) -> dict:
    positives = [item for item in results if item["kind"] == "positive"]
    negatives = [item for item in results if item["kind"] == "negative"]
    outside = [item for item in results if item["kind"] in ("out_of_domain", "boundary")]

    def ratio(hit: int, total: int) -> float:
        return round(hit / total, 4) if total else 0.0

    correct = sum(1 for item in results if item["passed"])
    top1 = [item for item in positives if item["best"] == item["expect"]]
    mrr = sum(1.0 / item["rank"] for item in positives if item["rank"]) / len(positives) if positives else 0.0

    return {
        "cases": len(results),
        "passed": correct,
        "precision": ratio(correct, len(results)),
        "recall": ratio(len(top1), len(positives)),
        "mrr": round(mrr, 4),
        "false_negatives": len(positives) - len(top1),
        "false_positives": sum(1 for item in outside if item["score"] >= threshold),
        "collisions": sum(1 for item in results if item["sibling"]),
        "negative_violations": sum(1 for item in negatives if not item["passed"]),
        "by_kind": {
            kind: {
                "cases": sum(1 for item in results if item["kind"] == kind),
                "passed": sum(1 for item in results if item["kind"] == kind and item["passed"]),
            }
            for kind in KINDS
        },
        "by_split": {
            split: {
                "cases": sum(1 for item in results if item["split"] == split),
                "passed": sum(1 for item in results if item["split"] == split and item["passed"]),
            }
            for split in SPLITS
        },
    }


def _collisions(router, threshold: float = COLLISION_JACCARD) -> list[dict]:
    names = sorted(router.skills)
    found = []
    for left_index, left in enumerate(names):
        left_tokens = router.skills[left].token_set
        for right in names[left_index + 1:]:
            right_tokens = router.skills[right].token_set
            union = left_tokens | right_tokens
            if not union:
                continue
            similarity = len(left_tokens & right_tokens) / len(union)
            if similarity >= threshold:
                found.append({"a": left, "b": right, "jaccard": round(similarity, 4)})
    return sorted(found, key=lambda item: (-item["jaccard"], item["a"], item["b"]))


def description_collisions(router, threshold: float = COLLISION_JACCARD) -> list[dict]:
    """Pares de descripciones por encima del umbral de similitud."""
    return _collisions(router, threshold)


def _budget(router) -> dict:
    rows = []
    for name in sorted(router.skills):
        skill = router.skills[name]
        body = skill.path.read_text(encoding="utf-8")
        body_lines = len(body.splitlines())
        rows.append({
            "skill": name,
            "description_tokens": max(1, len(skill.description) // 4),
            "body_tokens": max(1, len(body) // 4),
            "body_lines": body_lines,
        })

    catalog_tokens = sum(row["description_tokens"] for row in rows)
    heaviest = sorted(rows, key=lambda row: (-row["body_tokens"], row["skill"]))[:5]
    over_budget = [
        row["skill"]
        for row in rows
        if row["body_tokens"] > BODY_TOKEN_LIMIT or row["body_lines"] >= BODY_LINE_LIMIT
    ]
    return {
        "skills": len(rows),
        "catalog_tokens": catalog_tokens,
        "catalog_limit": CATALOG_TOKEN_LIMIT,
        "catalog_ok": catalog_tokens <= CATALOG_TOKEN_LIMIT,
        "body_token_limit": BODY_TOKEN_LIMIT,
        "body_line_limit": BODY_LINE_LIMIT,
        "over_budget": over_budget,
        "heaviest": heaviest,
    }


def evaluate(router, document: dict) -> dict:
    """Ejecuta todos los casos y devuelve el informe máquina de una corrida."""
    threshold = float(document.get("threshold", DEFAULT_THRESHOLD))
    results = [_evaluate_case(router, case, threshold) for case in document["cases"]]
    metrics = _metrics(results, threshold)
    return {
        "format": RUN_FORMAT,
        "version": CASE_VERSION,
        "threshold": threshold,
        "metrics": metrics,
        "collisions": _collisions(router),
        "budget": _budget(router),
        "failures": [
            {
                "id": item["id"],
                "prompt": item["prompt"],
                "kind": item["kind"],
                "expect": item["expect"],
                "best": item["best"],
                "score": item["score"],
                "sibling": item["sibling"],
            }
            for item in results
            if not item["passed"]
        ],
        "cases": results,
    }


def score_cases(router, document: dict, split: str | None = None) -> tuple[dict, list[dict]]:
    """Métricas y resultados de un split (o de todo el conjunto si es None)."""
    threshold = float(document.get("threshold", DEFAULT_THRESHOLD))
    cases = document["cases"]
    if split is not None:
        cases = [case for case in cases if case.get("split") == split]
    results = [_evaluate_case(router, case, threshold) for case in cases]
    return _metrics(results, threshold), results


def diff_runs(current: dict, baseline: dict) -> dict:
    """Regresiones y arreglos por id de caso entre dos corridas."""
    before = {item["id"]: item["passed"] for item in baseline.get("cases", [])}
    after = {item["id"]: item["passed"] for item in current.get("cases", [])}
    regressions = sorted(case_id for case_id, ok in after.items() if before.get(case_id) and not ok)
    fixes = sorted(case_id for case_id, ok in after.items() if case_id in before and ok and not before[case_id])
    return {
        "regressions": regressions,
        "fixes": fixes,
        "new": sorted(case_id for case_id in after if case_id not in before),
        "removed": sorted(case_id for case_id in before if case_id not in after),
    }


def parse_gates(pairs: list[str]) -> dict[str, float]:
    """Convierte `precision=0.95` en `{"precision": 0.95}`."""
    gates: dict[str, float] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"gate sin «=»: {pair!r} (ejemplo: precision=0.95)")
        key, raw = pair.split("=", 1)
        key = key.strip()
        if key not in {"precision", "recall", "mrr"}:
            raise ValueError(f"métrica desconocida: {key!r}")
        value = float(raw)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"umbral fuera de rango: {pair!r}")
        gates[key] = value
    return gates
