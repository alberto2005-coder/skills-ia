"""Router léxico determinista para los tests de activación de skills.

No usa red ni dependencias externas: puntúa cuánto se parece una frase del
usuario a la `description` del frontmatter de cada SKILL.md. Sirve como fixture
de test, no como producto: si dos sub-skills empatan, sus descripciones se
solapan y el test falla con el detalle.

Criterios:
- stemming ligero (prefijo de 5 letras) para que "auditoría" y "auditar" casen;
- IDF sobre el corpus para que los términos distintivos pesen más;
- bigramas para premiar frases, no solo palabras sueltas;
- una frase de dos tokens exige las dos coincidencias: un sustantivo genérico
  suelto ("resume este texto") no activa nada;
- desempate por especificidad (sub-skill antes que maestro) y, después,
  alfabético, para que el resultado sea reproducible.
"""
from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

STOPWORDS = frozenset(
    """
    de la que el en y a los del se las por un para con no una su al lo como mas
    pero sus le ya o este si porque esta entre cuando muy sin sobre tambien me
    hasta hay donde quien desde todo nos durante todos uno les ni contra otros
    ese eso ante ellos e esto mi antes algunos unos yo otro otras otra tanto
    esa estos mucho quienes nada muchos cual poco ella estar estas algunas algo
    nosotros mis tu te ti tus ellas os mio mia mios mias tuyo tuya tuyos tuyas
    suyo suya suyos suyas nuestro nuestra nuestros nuestras vuestro vuestra
    vuestros vuestras esos esas estoy estamos estan estare estara estaria estaba
    estuve estuvo estuvimos estuvieron estando estado estados he has ha hemos
    han haya hayan habre habra habria habia hubo hubiera hubiese habiendo habido
    the a an and or of to in for on with is are be this that these those it its
    as at by from we you they i not do does did should would can could will just
    use when where how what which who whom whose all any each more most other
    some such only own same so than too very dont now
    """.split()
)

WORD_RE = re.compile(r"[a-z0-9]+")


def normalize(text: str) -> str:
    """Minúsculas sin acentos ni diacríticos."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def stem(token: str) -> str:
    """Stemming ligero: prefijo de 5 letras para palabras largas."""
    return token[:5] if len(token) >= 6 else token


def tokenize(text: str) -> list[str]:
    """Tokens normalizados, sin stopwords y con stemming ligero."""
    return [
        stem(word)
        for word in WORD_RE.findall(normalize(text))
        if len(word) > 2 and word not in STOPWORDS
    ]


def bigrams(tokens: list[str]) -> set[tuple[str, str]]:
    return set(zip(tokens, tokens[1:]))


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extrae `name` y `description` del frontmatter sin dependencias YAML."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not match:
        return {}
    data: dict[str, str] = {}
    lines = match.group(1).splitlines()
    index = 0
    while index < len(lines):
        found = re.match(r"^(name|description):\s*(.*?)\s*$", lines[index])
        if not found:
            index += 1
            continue

        key, value = found.groups()
        if key == "description" and value.startswith((">", "|")):
            parts = []
            index += 1
            while index < len(lines):
                line = lines[index]
                if line.strip() and not line[0].isspace():
                    break
                parts.append(line.strip())
                index += 1
            separator = " " if value.startswith(">") else "\n"
            data[key] = separator.join(parts).strip()
            continue

        if value:
            data[key] = value
        index += 1
    return data


def discover(repo_root: Path) -> list[tuple[str, str, Path, str]]:
    """Devuelve (paquete, nombre, ruta, descripción) de cada SKILL.md real.

    Ignora los fixtures de `tests/`, que son muestras de terceros.
    """
    found = []
    for path in sorted(repo_root.glob("**/SKILL.md")):
        if "tests" in path.relative_to(repo_root).parts:
            continue
        meta = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not meta.get("name") or not meta.get("description"):
            continue
        package = path.relative_to(repo_root).parts[0]
        found.append((package, meta["name"], path, meta["description"]))
    return found


class Skill:
    """Documento indexado de una skill."""

    def __init__(self, package: str, name: str, path: Path, description: str) -> None:
        self.package = package
        self.name = name
        self.path = path
        self.description = description
        self.tokens = tokenize(description)
        self.token_set = set(self.tokens)
        self.bigram_set = bigrams(self.tokens)
        self.name_tokens = set(tokenize(name.replace("-", " ")))
        # Un SKILL.md de sub-skill está un nivel más abajo que el maestro.
        self.depth = len(path.parts)

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"Skill({self.name!r})"


class Router:
    """Puntúa frases contra las descripciones con TF-IDF y bigramas."""

    def __init__(self, skills: list[Skill]) -> None:
        self.skills = {skill.name: skill for skill in skills}
        documents = [skill.token_set for skill in self.skills.values()]
        document_frequency: Counter[str] = Counter()
        for tokens in documents:
            document_frequency.update(tokens)
        total = len(documents)
        self.idf = {
            token: math.log((1 + total) / (1 + df)) + 1.0
            for token, df in document_frequency.items()
        }

    @classmethod
    def from_repo(cls, repo_root: Path) -> "Router":
        return cls([Skill(*item) for item in discover(repo_root)])

    @property
    def names(self) -> set[str]:
        return set(self.skills)

    def score(self, phrase: str, skill_name: str) -> float:
        skill = self.skills[skill_name]
        phrase_tokens = tokenize(phrase)
        unique = list(dict.fromkeys(phrase_tokens))
        if not unique:
            return 0.0
        matched = [token for token in unique if token in skill.token_set]
        if not matched:
            return 0.0
        # Con dos tokens no basta con uno: «resume este texto» no debe activar
        # una skill solo porque su descripción mencione el sustantivo «texto».
        if len(unique) == 2 and len(matched) < 2:
            return 0.0

        coverage = len(matched) / len(unique)
        total_idf = sum(self.idf.get(token, 1.0) for token in unique)
        idf_coverage = sum(self.idf.get(token, 1.0) for token in matched) / total_idf

        phrase_bigrams = bigrams(unique)
        bigram_coverage = (
            len(phrase_bigrams & skill.bigram_set) / len(phrase_bigrams)
            if phrase_bigrams
            else 0.0
        )

        name_hits = len(skill.name_tokens & set(unique))
        name_score = name_hits / len(skill.name_tokens) if skill.name_tokens else 0.0

        base = (
            0.50 * idf_coverage
            + 0.28 * bigram_coverage
            + 0.14 * coverage
            + 0.08 * name_score
        )
        # Una sola palabra rara en común no activa una skill: si la frase tiene
        # tres o más términos y no cubre ni la mitad, se penaliza a la mitad.
        if len(unique) >= 3 and coverage < 0.5:
            base *= 0.5
        return round(base, 6)

    def _order(self, name: str, value: float) -> tuple[float, int, str]:
        """Orden determinista: puntuación, luego especificidad, luego nombre."""
        return (-value, -self.skills[name].depth, name)

    def ranking(self, phrase: str) -> list[tuple[str, float]]:
        """Ranking completo: a igual puntuación gana la skill más específica."""
        scored = [(name, self.score(phrase, name)) for name in self.skills]
        return sorted(scored, key=lambda item: self._order(*item))

    def best(self, phrase: str) -> tuple[str, float]:
        return self.ranking(phrase)[0]

    def best_in(self, phrase: str, package: str) -> tuple[str, float]:
        names = [name for name, skill in self.skills.items() if skill.package == package]
        scored = [(name, self.score(phrase, name)) for name in names]
        return sorted(scored, key=lambda item: self._order(*item))[0]

    def top_ties(self, phrase: str) -> list[str]:
        """Skills empatadas en la primera posición (misma puntuación)."""
        ranking = self.ranking(phrase)
        best = ranking[0][1]
        return [name for name, value in ranking if value == best]

    def siblings(self, skill_name: str) -> list[str]:
        package = self.skills[skill_name].package
        return sorted(
            name
            for name, skill in self.skills.items()
            if skill.package == package and name != skill_name
        )


def main() -> int:
    """Calibración manual: `py tests/trigger_router.py`."""
    root = Path(__file__).resolve().parent.parent
    datasets = json.loads((Path(__file__).parent / "phrases.json").read_text(encoding="utf-8"))
    router = Router.from_repo(root)
    print(f"skills indexadas: {len(router.skills)}")

    failures = 0
    for skill_name, entries in datasets["skills"].items():
        for phrase in entries.get("positives", []):
            top = router.ranking(phrase)[:2]
            ok = top[0][0] == skill_name
            failures += 0 if ok else 1
            print(f"{'ok ' if ok else 'FALLO'} + {skill_name:24} -> {top}")
        for negative in entries.get("negatives", []):
            phrase, winner = negative["phrase"], negative["winner"]
            top = router.ranking(phrase)[:2]
            ok = top[0][0] == winner and top[0][0] != skill_name
            failures += 0 if ok else 1
            print(f"{'ok ' if ok else 'FALLO'} - {skill_name:24} -> {top} (esperado {winner})")

    threshold = datasets["threshold"]
    for phrase in datasets["out_of_domain"]:
        name, value = router.best(phrase)
        ok = value < threshold
        failures += 0 if ok else 1
        print(f"{'ok ' if ok else 'FALLO'} ? fuera de dominio -> {name} {value} (umbral {threshold})")

    print(f"\nfallos de calibración: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
