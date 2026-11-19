"""Lint de frontmatter, manifiestos, enlaces relativos e índice del repositorio.

Uso:
    py tests/lint_frontmatter.py [--json]

Comprueba, con el parser YAML del entorno (PyYAML, dependencia de desarrollo):

1. Frontmatter de cada `SKILL.md` fuera de `tests/`: YAML válido, `name` en
   minúsculas (máx. 64) e igual al nombre de su carpeta, `description` de 20 a
   1024 caracteres y cuerpo por debajo de 500 líneas.
2. Cada entrada de los `skills.json` de paquete resuelve a un fichero con el
   nombre declarado.
3. La versión de cada paquete sale de su manifiesto: el índice raíz y el
   `metadata.version` de cada `SKILL.md` dicen lo mismo que `skills.json`.
4. Cada enlace relativo de cada Markdown resuelve a un fichero existente.
5. El índice raíz `skills.json` cuadra con el disco: `skills_total`, el número
   de skills por paquete y la cobertura de todos los `SKILL.md`.
6. Cada paquete del índice tiene su guía `docs/<paquete>.md` y un enlace a ella
   en `README.md` y en `docs/index.md`.

Es la puerta de CI independiente de `unittest`.

Código de salida: 0 limpio · 1 con problemas.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"tests", "fixtures", "node_modules", "__pycache__", ".venv", ".git"}
FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
LINK_IGNORED_PREFIXES = ("http://", "https://", "mailto:", "#", "/")
MAX_NAME = 64
MIN_DESCRIPTION = 20
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def parse_frontmatter(block: str) -> tuple[dict, list[str]]:
    """Campos del bloque y, si el YAML no parsea, el problema en vez de un dict vacío.

    Se valida con PyYAML a propósito: el parseo a mano aceptaba valores como
    `description: texto. English: more text`, donde `: ` dentro de un escalar plano
    hace que un parser real rechace el bloque entero.
    """
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f" en la línea {mark.line + 1} del bloque" if mark is not None else ""
        problem = getattr(error, "problem", None) or "no se pudo parsear"
        return {}, [f"frontmatter con YAML inválido{where}: {problem}"]
    if not isinstance(data, dict):
        return {}, ["el frontmatter debe ser un mapa YAML de pares clave: valor"]
    return data, []


def lint_file(path: Path) -> list[str]:
    problems: list[str] = []
    text = path.read_text(encoding="utf-8")

    match = FRONTMATTER.match(text)
    if not match:
        return ["sin bloque de frontmatter delimitado por ---"]

    fields, problems = parse_frontmatter(match.group(1))
    name = fields.get("name")
    if not isinstance(name, str) or not name.strip():
        problems.append("falta «name» o no es texto")
    else:
        if not NAME_PATTERN.match(name):
            problems.append(
                f"name «{name}» debe usar minúsculas, dígitos y guiones simples"
            )
        if len(name) > MAX_NAME:
            problems.append(f"name de {len(name)} caracteres; máximo {MAX_NAME}")
        if name != path.parent.name:
            problems.append(f"name «{name}» no coincide con la carpeta «{path.parent.name}»")

    description = fields.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append("falta «description» o no es texto")
    else:
        length = len(description.strip())
        if not MIN_DESCRIPTION <= length <= MAX_DESCRIPTION:
            problems.append(
                f"description de {length} caracteres; debe estar entre "
                f"{MIN_DESCRIPTION} y {MAX_DESCRIPTION}"
            )

    body_lines = len(text[match.end():].splitlines())
    if body_lines >= MAX_BODY_LINES:
        problems.append(
            f"cuerpo de {body_lines} líneas; debe quedar por debajo de {MAX_BODY_LINES}"
        )

    return problems


def iter_skill_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.glob("**/SKILL.md")
        if not SKIP_PARTS & set(path.relative_to(root).parts)
    )


def iter_markdown_files(root: Path) -> list[Path]:
    """Markdown del repositorio, sin los borradores de plan de la raíz."""
    return sorted(
        path
        for path in root.glob("**/*.md")
        if not SKIP_PARTS & set(path.relative_to(root).parts)
        and not (path.parent == root and path.name.lower().startswith("plan"))
    )


def lint_links(root: Path) -> dict[str, list[str]]:
    """Comprueba que cada enlace relativo de cada Markdown resuelva a un fichero."""
    problems: dict[str, list[str]] = {}
    for markdown in iter_markdown_files(root):
        relative = markdown.relative_to(root).as_posix()
        for target in MARKDOWN_LINK.findall(markdown.read_text(encoding="utf-8")):
            if target.startswith(LINK_IGNORED_PREFIXES):
                continue
            clean = target.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            if not (markdown.parent / clean).exists():
                problems.setdefault(relative, []).append(f"enlace relativo roto: {target}")
    return problems


def lint_manifests(root: Path) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}
    for manifest_path in sorted(root.glob("*/skills.json")):
        relative = manifest_path.relative_to(root).as_posix()
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            problems.setdefault(relative, []).append(f"JSON inválido: {error}")
            continue

        entries = data.get("skills")
        if not isinstance(entries, list) or not entries:
            problems.setdefault(relative, []).append("sin lista «skills»")
            continue

        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("path") or not entry.get("name"):
                problems.setdefault(relative, []).append(f"entrada incompleta: {entry!r}")
                continue
            target = manifest_path.parent / entry["path"]
            if not target.is_file():
                problems.setdefault(relative, []).append(
                    f"«{entry['name']}» apunta a un fichero inexistente: {entry['path']}"
                )
            elif entry["path"] != "SKILL.md" and target.parent.name != entry["name"]:
                problems.setdefault(relative, []).append(
                    f"«{entry['name']}» no coincide con la carpeta {target.parent.name}"
                )
    return problems


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def lint_versions(root: Path) -> dict[str, list[str]]:
    """El manifiesto del paquete es la única fuente de la versión.

    El índice raíz y el `metadata.version` de cada `SKILL.md` tienen que decir
    lo mismo que `skills.json`; si divergen, la publicación etiquetaría una
    versión distinta de la que declara el paquete.
    """
    index_path = root / "skills.json"
    if not index_path.is_file():
        return {}
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"skills.json": ["JSON inválido: %s" % error]}

    problems: dict[str, list[str]] = {}
    for entry in index.get("packages") or []:
        relative = entry.get("path") or entry.get("name")
        if not relative:
            continue
        manifest_path = root / relative / "skills.json"
        manifest_name = manifest_path.relative_to(root).as_posix()
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            problems.setdefault(manifest_name, []).append("no se pudo leer el manifiesto: %s" % error)
            continue
        version = manifest.get("version")
        if not isinstance(version, str) or not SEMVER.match(version):
            problems.setdefault(manifest_name, []).append("version %r no es X.Y.Z" % (version,))
            continue
        if entry.get("version") != version:
            problems.setdefault("skills.json", []).append(
                "«%s»: el índice declara %r y el manifiesto %r"
                % (entry.get("name"), entry.get("version"), version)
            )
        for skill_md in sorted(manifest_path.parent.glob("**/SKILL.md")):
            relative_skill = skill_md.relative_to(root)
            if not skill_md.is_file() or SKIP_PARTS & set(relative_skill.parts):
                continue
            match = FRONTMATTER.match(skill_md.read_text(encoding="utf-8"))
            if not match:
                continue  # el pase de frontmatter ya lo reporta
            fields, _ = parse_frontmatter(match.group(1))
            metadata = fields.get("metadata")
            declared = metadata.get("version") if isinstance(metadata, dict) else None
            if str(declared) != version:
                problems.setdefault(relative_skill.as_posix(), []).append(
                    "metadata.version %r no coincide con el manifiesto (%s)" % (declared, version)
                )
    return problems


def lint_index(root: Path) -> list[str]:
    """Cuadra el índice raíz con los SKILL.md y los manifiestos del disco."""
    index_path = root / "skills.json"
    if not index_path.is_file():
        return []

    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"JSON inválido: {error}"]

    problems: list[str] = []
    packages = index.get("packages")
    if not isinstance(packages, list) or not packages:
        return ["sin lista «packages»"]

    on_disk = {path.parent.name: path for path in iter_skill_files(root)}
    covered: set[str] = set()
    total = 0

    for package in packages:
        name = package.get("name", "")
        skills = package.get("skills") or []
        count = package.get("skill_count")
        manifest_path = package.get("manifest", f"{name}/skills.json")

        if count != len(skills):
            problems.append(
                f"«{name}»: skill_count={count} pero declara {len(skills)} skills"
            )
        total += len(skills)

        manifest_file = root / manifest_path
        if not manifest_file.is_file():
            problems.append(f"«{name}»: manifiesto inexistente {manifest_path}")
            continue

        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            problems.append(f"«{name}»: manifiesto con JSON inválido: {error}")
            continue

        manifest_skills = [entry.get("name") for entry in manifest.get("skills", [])]
        if sorted(manifest_skills) != sorted(skills):
            problems.append(
                f"«{name}»: el índice lista skills que el manifiesto no declara"
            )

        for skill in skills:
            path = on_disk.get(skill)
            if path is None:
                problems.append(f"«{name}»: falta el SKILL.md de {skill}")
                continue
            expected = root / Path(package.get("path", name))
            if path.parent == root or expected not in path.parents:
                problems.append(
                    f"«{skill}» vive en {path.relative_to(root).as_posix()}, fuera del paquete «{name}»"
                )
            covered.add(skill)

    declared = index.get("skills_total")
    if declared != total:
        problems.append(f"skills_total={declared} pero los paquetes suman {total}")
    if declared != len(on_disk):
        problems.append(f"skills_total={declared} y hay {len(on_disk)} SKILL.md en el disco")

    missing = sorted(set(on_disk) - covered)
    if missing:
        problems.append("SKILL.md fuera del índice: " + ", ".join(missing))

    return problems


def lint_package_docs(root: Path) -> dict[str, list[str]]:
    """Cada paquete del índice debe tener guía en `docs/` y estar enlazado en README e índice."""
    index_path = root / "skills.json"
    if not index_path.is_file():
        return {}

    try:
        packages = json.loads(index_path.read_text(encoding="utf-8")).get("packages") or []
    except json.JSONDecodeError:
        return {}

    problems: dict[str, list[str]] = {}
    for package in packages:
        name = package.get("name")
        if not name:
            continue
        guide = root / "docs" / f"{name}.md"
        if not guide.is_file():
            problems.setdefault("docs/", []).append(f"falta la guía docs/{name}.md")

    for document_name, mentions in (("README.md", "docs/{name}.md"), ("docs/index.md", None)):
        document = root / document_name
        text = document.read_text(encoding="utf-8") if document.is_file() else ""
        for package in packages:
            package_name = package.get("name")
            if not package_name:
                continue
            if mentions is None:
                linked = f"({package_name}.md)" in text
            else:
                linked = mentions.format(name=package_name) in text
            if not linked:
                problems.setdefault(document_name, []).append(
                    f"el paquete «{package_name}» no tiene enlace a su guía"
                )

    return problems


def lint_repository(root: Path = ROOT) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}
    for path in iter_skill_files(root):
        found = lint_file(path)
        if found:
            problems[path.relative_to(root).as_posix()] = found
    for path, found in lint_manifests(root).items():
        problems.setdefault(path, []).extend(found)
    for path, found in lint_links(root).items():
        problems.setdefault(path, []).extend(found)
    for path, found in lint_package_docs(root).items():
        problems.setdefault(path, []).extend(found)
    for path, found in lint_versions(root).items():
        problems.setdefault(path, []).extend(found)
    index_problems = lint_index(root)
    if index_problems:
        problems.setdefault("skills.json", []).extend(index_problems)
    return problems


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Lint de frontmatter, manifiestos, enlaces e índice.")
    parser.add_argument("--root", default=str(ROOT), help="Raíz del repositorio")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    problems = lint_repository(root)

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}, indent=2, ensure_ascii=False))
    elif problems:
        for path, found in sorted(problems.items()):
            print(f"{path}")
            for item in found:
                print(f"  - {item}")
        print(f"\n{len(problems)} fichero(s) con problemas.")
    else:
        total = len(iter_skill_files(root))
        print(f"OK: {total} SKILL.md, sus manifiestos, enlaces relativos e índice coherentes.")

    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
