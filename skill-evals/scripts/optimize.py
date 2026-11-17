"""Optimiza la descripción de una skill con candidatos deterministas.

Uso:
    py skill-evals/scripts/optimize.py --skill appsec-recon --cases casos.json
    py skill-evals/scripts/optimize.py --skill appsec-recon --cases casos.json --apply

Ciclo, igual que skill-reach y skill-creator pero sin modelo:

1. Detecta las positivas de **train** que fallan y extrae los términos que sí
   usa el usuario y no están en la descripción.
2. Propone candidatos que añaden esos términos (varias tallas, sin duplicados).
3. Evalúa todos en train y descarta los que no mejoran.
4. Elige el ganador por **test**, nunca por train, para no sobreajustar.
5. Emite el diff unificado y la mejora medida. Sin `--apply` no escribe nada.

Código de salida: 0 con mejora · 1 sin mejora · 2 entrada ilegible.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import textwrap
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evalkit  # noqa: E402

FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)
DESCRIPTION = re.compile(r"^description:", re.M)
WORD = re.compile(r"[a-z0-9]+")
CANDIDATE_SIZES = (3, 6, 9)


def _read(path: Path) -> dict:
    try:
        return evalkit.read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"no se pudo leer {path}: {error}") from error


def rewrite_description(text: str, description: str, width: int = 78) -> str:
    """Sustituye el bloque `description` del frontmatter y deja el resto intacto."""
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("SKILL.md sin frontmatter delimitado por ---")
    block = match.group(1)
    lines = block.splitlines()
    start = next((index for index, line in enumerate(lines)
                  if line.startswith("description:")), None)
    if start is None:
        raise ValueError("frontmatter sin «description»")
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end][0].isspace()):
        end += 1

    wrapped = textwrap.wrap(description.strip(), width=width - 2) or [""]
    replacement = ["description: >"] + ["  " + line for line in wrapped]
    new_block = "\n".join(lines[:start] + replacement + lines[end:])
    return text[:match.start(1)] + new_block + text[match.end(1):]


def missing_terms(tr, router, cases: list[dict], skill: str, limit: int) -> list[str]:
    """Términos de las frases que fallan que la descripción no contiene."""
    skill_obj = router.skills[skill]
    counts: dict[str, int] = {}
    for case in cases:
        if case.get("kind") != "positive" or case.get("expect") != skill:
            continue
        for word in WORD.findall(router_normalize(case["prompt"])):
            if len(word) <= 3 or word in tr.STOPWORDS:
                continue
            if tr.stem(word) in skill_obj.token_set:
                continue
            counts[word] = counts.get(word, 0) + 1
    ordered = sorted(counts, key=lambda word: (-counts[word], word))
    return ordered[:limit]


def router_normalize(text: str) -> str:
    """Normaliza igual que el router (minúsculas y sin acentos)."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def candidate_descriptions(description: str, terms: list[str]) -> list[dict]:
    """Un candidato por talla, con los términos en el mismo orden determinista."""
    candidates = []
    sizes = sorted({min(size, len(terms)) for size in CANDIDATE_SIZES} | {len(terms)})
    for size in sizes:
        selected = terms[:size]
        if not selected:
            continue
        text = description.rstrip() + " También cubre: " + ", ".join(selected) + "."
        candidates.append({"terms": selected, "description": text})
    return candidates


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.name


def _with_description(tr, router, skill: str, description: str):
    skills = [
        tr.Skill(item.package, item.name, item.path,
                 description if item.name == skill else item.description)
        for item in router.skills.values()
    ]
    return tr.Router(skills)


def _better(candidate: dict, baseline: dict) -> bool:
    return (candidate["precision"], candidate["recall"]) > (baseline["precision"], baseline["recall"])


def plan(router, tr, document: dict, skill: str, max_terms: int = 9) -> dict:
    """Devuelve el plan de optimización completo, sin escribir en disco."""
    threshold = float(document.get("threshold", evalkit.DEFAULT_THRESHOLD))
    baseline_train, train_results = evalkit.score_cases(router, document, "train")
    baseline_test, _ = evalkit.score_cases(router, document, "test")
    baseline_collisions = len(evalkit.description_collisions(router))

    failing = {item["id"] for item in train_results if not item["passed"]}
    train_cases = [case for case in document["cases"]
                   if case.get("id") in failing and case.get("expect") == skill]
    terms = missing_terms(tr, router, train_cases, skill, max_terms)
    skill_obj = router.skills[skill]

    evaluated = []
    for candidate in candidate_descriptions(skill_obj.description, terms):
        new_router = _with_description(tr, router, skill, candidate["description"])
        train, _ = evalkit.score_cases(new_router, document, "train")
        test, _ = evalkit.score_cases(new_router, document, "test")
        collisions = len(evalkit.description_collisions(new_router))
        accepted = (
            _better(train, baseline_train)
            and collisions <= baseline_collisions
        )
        evaluated.append({
            "terms": candidate["terms"],
            "description": candidate["description"],
            "train": {"precision": train["precision"], "recall": train["recall"]},
            "test": {"precision": test["precision"], "recall": test["recall"]},
            "collisions": collisions,
            "accepted": accepted,
        })

    eligible = [item for item in evaluated if item["accepted"]]
    chosen = None
    if eligible:
        # Selección final por test; desempate por menos términos añadidos.
        chosen = max(eligible, key=lambda item: (
            item["test"]["precision"], item["test"]["recall"], -len(item["terms"]),
        ))
        if not _better(chosen["test"], baseline_test):
            chosen = None

    status = "improved" if chosen else ("no_improvement" if eligible else "no_candidates")
    diff = ""
    if chosen:
        old_text = skill_obj.path.read_text(encoding="utf-8")
        new_text = rewrite_description(old_text, chosen["description"])
        diff = "".join(difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{_display_path(skill_obj.path)}",
            tofile=f"b/{_display_path(skill_obj.path)}",
            lineterm="\n" if "\r\n" not in old_text else "\r\n",
        ))

    return {
        "skill": skill,
        "threshold": threshold,
        "status": status,
        "terms": terms,
        "baseline": {
            "train": baseline_train,
            "test": baseline_test,
            "collisions": baseline_collisions,
        },
        "candidates": evaluated,
        "chosen": chosen,
        "diff": diff,
    }


def apply_plan(skill_path: Path, chosen: dict) -> None:
    raw = skill_path.read_bytes().decode("utf-8")
    updated = rewrite_description(raw, chosen["description"])
    skill_path.write_bytes(updated.encode("utf-8"))


def _print_plan(result: dict) -> None:
    baseline = result["baseline"]
    print(f"skill: {result['skill']} · estado: {result['status']}")
    print(f"términos ausentes en train: {', '.join(result['terms']) or 'ninguno'}")
    print(f"base  train p/r {baseline['train']['precision']:.3f}/{baseline['train']['recall']:.3f}"
          f" · test p/r {baseline['test']['precision']:.3f}/{baseline['test']['recall']:.3f}"
          f" · colisiones {baseline['collisions']}")
    for candidate in result["candidates"]:
        mark = "ACEPTA" if candidate["accepted"] else "descarta"
        print(f"  {mark} +{len(candidate['terms'])} términos "
              f"train {candidate['train']['precision']:.3f}/{candidate['train']['recall']:.3f} "
              f"test {candidate['test']['precision']:.3f}/{candidate['test']['recall']:.3f}")
    chosen = result["chosen"]
    if chosen:
        print(f"elegido por test: +{', '.join(chosen['terms'])}")
        print(result["diff"], end="")
    else:
        print("sin candidato que mejore test; no se toca la descripción.")


def main(argv: list[str] | None = None) -> int:
    evalkit.force_utf8_output()
    parser = argparse.ArgumentParser(description="Optimiza la descripción de una skill.")
    parser.add_argument("--skill", required=True, help="skill objetivo")
    parser.add_argument("--cases", required=True, help="fichero de casos")
    parser.add_argument("--repo", default=str(evalkit.REPO_ROOT), help="raíz del repositorio")
    parser.add_argument("--max-terms", type=int, default=9)
    parser.add_argument("--apply", action="store_true", help="escribe el cambio en SKILL.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    tr, router = evalkit.load_router(repo)
    if args.skill not in router.skills:
        print(f"skill desconocida: {args.skill}")
        return 2

    document = _read(Path(args.cases))
    problems = evalkit.validate_cases(document, router.names)
    if problems:
        for problem in problems:
            print(f"  - {problem}")
        return 2

    result = plan(router, tr, document, args.skill, args.max_terms)
    applied = False
    if result["chosen"] and args.apply:
        apply_plan(router.skills[args.skill].path, result["chosen"])
        applied = True
    result["applied"] = applied

    if args.json:
        payload = {key: value for key, value in result.items() if key != "candidates"}
        payload["candidates"] = [
            {key: value for key, value in item.items() if key != "description"}
            for item in result["candidates"]
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_plan(result)
        if applied:
            print(f"aplicado en {router.skills[args.skill].path.name}")

    return 0 if result["chosen"] else 1


if __name__ == "__main__":
    sys.exit(main())
