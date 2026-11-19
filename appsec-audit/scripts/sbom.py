"""SBOM CycloneDX, cruce con avisos y alcanzabilidad por imports.

Uso:
    py appsec-audit/scripts/sbom.py build   <dir> --output sbom.cdx.json [--now ISO]
    py appsec-audit/scripts/sbom.py audit   <sbom.cdx.json> --advisories avisos.json
        [--repo <dir>] [--output deps.json] [--json] [--fail-on reachable|none]
    py appsec-audit/scripts/sbom.py validate <sbom.cdx.json> [--json]

Lee manifiestos y código; nunca instala ni ejecuta el proyecto auditado.
Código de salida: 0 correcto · 1 inválido o puerta bloqueada · 2 fichero ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from appsec_util import TOOL_VERSION, force_utf8_output

SPEC_VERSION = "1.5"
HIGH_SEVERITIES = ("critical", "high")
SOURCE_EXTS = (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go")
SKIP_DIRS = {"node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".git"}
TEST_HINTS = {"test", "tests", "spec", "__tests__", "testing"}
MAX_SOURCE_BYTES = 512 * 1024

REQUIREMENT_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.\-]+)\s*(?:\[[^\]]*\])?\s*(?P<spec>.*?)\s*$"
)
COMPARATOR_RE = re.compile(r"^(<=|>=|<|>|=)?\s*([0-9][0-9A-Za-z.\-]*)$")
# Separador de pre-release: `-rc1`, `.dev0`, `-beta.2`, ...
PRE_RELEASE_RE = re.compile(
    r"[-.]((?:a|b|c|rc|alpha|beta|dev|pre|snapshot)[-.]?\d*)$", re.I
)


def version_key(value: str) -> tuple[int, ...]:
    # Cortar el sufijo pre-release: `2.0.0-rc1` no es (2,0,0,1) por encima
    # de 2.0.0, sino la misma versión todavía no finalizada.
    text = PRE_RELEASE_RE.split(str(value), 1)[0]
    parts = [int(number) for number in re.findall(r"\d+", text)]
    return tuple(parts) if parts else (0,)


def prerelease_of(value: str) -> tuple[int, ...]:
    """Sufijo pre-release como clave comparable: menor que la versión base.

    `2.0.0-rc1` debe verse por debajo de `2.0.0`, no por encima. Devuelve
    `()` para versiones finales, que así ordenan por delante de cualquier
    pre-release del mismo número.
    """
    match = PRE_RELEASE_RE.search(str(value))
    if not match:
        return ()
    suffix = match.group(1)
    numbers = tuple(int(n) for n in re.findall(r"\d+", suffix))
    words = {"a": 0, "alpha": 0, "pre": 0, "b": 1, "beta": 1, "c": 2, "rc": 2,
             "snapshot": 3}
    key = words.get(re.match(r"[a-z]+", suffix, re.I).group(0).lower(), 9)
    # Negativo: cuanto más "temprano" el sufijo, menor es la clave.
    return (-key, -numbers[0] if numbers else 0)


def compare_versions(left: str, right: str) -> int:
    a, b = version_key(left), version_key(right)
    width = max(len(a), len(b))
    a += (0,) * (width - len(a))
    b += (0,) * (width - len(b))
    if a != b:
        return (a > b) - (a < b)
    # Mismo número: la final gana al pre-release.
    pa, pb = prerelease_of(left), prerelease_of(right)
    return (pa > pb) - (pa < pb)


def satisfies(version: str, spec: str) -> bool:
    """True si la versión cumple todos los comparadores del rango afectado."""
    spec = (spec or "").strip()
    if not spec or spec == "*":
        return True
    for token in re.split(r"[\s,]+", spec):
        if not token:
            continue
        match = COMPARATOR_RE.match(token)
        if not match:
            raise ValueError(f"rango no interpretable: {token}")
        operator, target = match.group(1) or "=", match.group(2)
        result = compare_versions(version, target)
        ok = {
            "=": result == 0,
            ">": result > 0,
            ">=": result >= 0,
            "<": result < 0,
            "<=": result <= 0,
        }[operator]
        if not ok:
            return False
    return True


def clean_version(raw: object) -> str:
    text = str(raw or "").strip()
    text = re.sub(r"^[\^~=v\s]+", "", text)
    return text if re.match(r"^[0-9]", text) else "unpinned"


def purl_for(ecosystem: str, name: str, version: str) -> str:
    qualifier = "" if version == "unpinned" else f"@{version}"
    if ecosystem == "npm":
        encoded = name.replace("@", "%40") if name.startswith("@") else name
        return f"pkg:npm/{encoded}{qualifier}"
    if ecosystem == "pypi":
        return f"pkg:pypi/{name.lower().replace('_', '-')}{qualifier}"
    return f"pkg:golang/{name}{qualifier}"


def component(ecosystem: str, name: str, version: str, source: str, scope: str = "runtime") -> dict:
    purl = purl_for(ecosystem, name, version)
    return {
        "type": "library",
        "bom-ref": purl,
        "name": name,
        "version": version,
        "purl": purl,
        "properties": [
            {"name": "appsec:ecosystem", "value": ecosystem},
            {"name": "appsec:source", "value": source},
            {"name": "appsec:scope", "value": scope},
        ],
    }


def parse_package_json(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        # Una raíz en lista/cadena hacía fallar .get con AttributeError.
        raise ValueError(f"{path.name}: la raíz debe ser un objeto JSON")
    components = []
    for section, scope in (("dependencies", "runtime"), ("devDependencies", "dev")):
        block = data.get(section)
        if not isinstance(block, dict):
            # `dependencies` como lista (forma válida en algunos manifiestos)
            # no debe romper el SBOM entero.
            continue
        for name, raw in sorted(block.items()):
            components.append(component("npm", name, clean_version(raw), path.name, scope))
    return components


def parse_requirements(path: Path) -> list[dict]:
    components = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.split("#", 1)[0].split(";", 1)[0].strip()
        if not stripped or stripped.startswith(("-", "git+", "http")):
            continue
        match = REQUIREMENT_RE.match(stripped)
        if not match:
            continue
        name, spec = match.group("name"), match.group("spec")
        version = spec[2:].strip() if spec.startswith("==") else "unpinned"
        components.append(component("pypi", name, clean_version(version), path.name))
    return components


def parse_pyproject(path: Path) -> list[dict]:
    # utf-8-sig: un BOM de Windows/macOS no debe volver invisible `[project]`.
    text = path.read_text(encoding="utf-8-sig")
    # Primero se aísla el bloque [project]: la regex no puede cruzar ningún
    # `[`, así que un campo como `authors = [{name = "x"}]` antes de
    # `dependencies` hacía desaparecer todas las dependencias en silencio.
    section = re.search(r"^\[project\]\s*$", text, re.M)
    if not section:
        return []
    rest = text[section.end():]
    next_section = re.search(r"^\s*\[", rest, re.M)
    block_text = rest[:next_section.start()] if next_section else rest
    block = re.search(r"dependencies\s*=\s*\[(.*?)\]", block_text, re.S)
    if not block:
        return []
    components = []
    for requirement in re.findall(r"[\"']([^\"']+)[\"']", block.group(1)):
        match = REQUIREMENT_RE.match(requirement)
        if not match:
            continue
        name, spec = match.group("name"), match.group("spec")
        version = spec[2:].strip() if spec.startswith("==") else "unpinned"
        components.append(component("pypi", name, clean_version(version), path.name))
    return components


def parse_go_mod(path: Path) -> list[dict]:
    components = []
    in_block = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_block = True
            continue
        if in_block and stripped == ")":
            in_block = False
            continue
        entry = None
        if in_block:
            entry = stripped
        elif stripped.startswith("require "):
            entry = stripped[len("require "):].strip()
        if not entry or entry.startswith("//"):
            continue
        indirect = "// indirect" in entry
        fields = entry.split("//", 1)[0].split()
        if len(fields) < 2:
            continue
        scope = "indirect" if indirect else "runtime"
        components.append(component("golang", fields[0], fields[1].lstrip("v"), path.name, scope))
    return components


def build_components(target: Path) -> list[dict]:
    components: list[dict] = []
    parsers = {
        "package.json": parse_package_json,
        "requirements.txt": parse_requirements,
        "pyproject.toml": parse_pyproject,
        "go.mod": parse_go_mod,
    }
    for filename, parser in parsers.items():
        path = target / filename
        if path.is_file():
            try:
                components.extend(parser(path))
            except (json.JSONDecodeError, OSError, ValueError):
                continue
    unique = {item["bom-ref"]: item for item in components}
    return [unique[key] for key in sorted(unique)]


def build_bom(target: Path, now: str | None = None) -> dict:
    components = build_components(target)
    name = target.resolve().name or "target"
    seed = "|".join([name] + [item["bom-ref"] for item in components])
    metadata: dict = {
        "tools": {
            "components": [{"type": "application", "name": "appsec-audit", "version": TOOL_VERSION}]
        },
        "component": {"type": "application", "name": name, "bom-ref": f"appsec-audit:{name}"},
    }
    if now:
        metadata["timestamp"] = now
    return {
        "bomFormat": "CycloneDX",
        "specVersion": SPEC_VERSION,
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, seed)}",
        "version": 1,
        "metadata": metadata,
        "components": components,
    }


def ecosystem_of(item: dict) -> str:
    for prop in item.get("properties") or []:
        if isinstance(prop, dict) and prop.get("name") == "appsec:ecosystem":
            return str(prop.get("value"))
    return ""


def is_test_path(path: Path, repo: Path) -> bool:
    relative = path.relative_to(repo)
    if TEST_HINTS & {part.lower() for part in relative.parts[:-1]}:
        return True
    name = relative.name.lower()
    return (
        name.startswith("test_")
        or name.endswith(("_test.py", "_test.go"))
        or ".test." in name
        or ".spec." in name
    )


def import_patterns(ecosystem: str, name: str) -> list[re.Pattern]:
    if ecosystem == "npm":
        escaped = re.escape(name)
        return [
            re.compile(rf"""(?:require\s*\(\s*|from\s+|import\s*\(\s*)['"]{escaped}(?:[/'"])"""),
        ]
    if ecosystem == "pypi":
        module = re.escape(name.replace("-", "_").lower())
        return [
            re.compile(rf"^\s*(?:from|import)\s+{module}\b", re.IGNORECASE | re.MULTILINE),
        ]
    escaped = re.escape(name)
    return [re.compile(rf"""^\s*(?:\w+\s+)?"{escaped}(?:/|")""", re.MULTILINE)]


def scan_imports(repo: Path, components: list[dict]) -> dict[str, str]:
    """Devuelve por bom-ref: reachable, test-only o not-imported."""
    wanted = {
        item["bom-ref"]: import_patterns(ecosystem_of(item), item["name"])
        for item in components
    }
    found: dict[str, str] = {ref: "not-imported" for ref in wanted}
    for path in sorted(repo.glob("**/*")):
        if path.suffix.lower() not in SOURCE_EXTS or not path.is_file():
            continue
        relative_parts = {part.lower() for part in path.relative_to(repo).parts[:-1]}
        if SKIP_DIRS & relative_parts:
            continue
        try:
            if path.stat().st_size > MAX_SOURCE_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        test_file = is_test_path(path, repo)
        for ref, patterns in wanted.items():
            if found[ref] == "reachable":
                continue
            if any(pattern.search(text) for pattern in patterns):
                found[ref] = "test-only" if test_file else "reachable"
    return found


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_bom(bom: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(bom, dict):
        return ["la raíz debe ser un objeto JSON"]
    if bom.get("bomFormat") != "CycloneDX":
        errors.append("bomFormat debe ser CycloneDX")
    if not str(bom.get("specVersion", "")).startswith("1."):
        errors.append("specVersion debe ser 1.x")
    components = bom.get("components")
    if not isinstance(components, list):
        return errors + ["«components» debe ser una lista"]
    seen: set[str] = set()
    for position, item in enumerate(components, start=1):
        if not isinstance(item, dict):
            errors.append(f"components[{position}]: no es un objeto")
            continue
        for key in ("type", "name", "version", "bom-ref"):
            if not item.get(key):
                errors.append(f"components[{position}]: falta «{key}»")
        ref = item.get("bom-ref")
        if isinstance(ref, str):
            if ref in seen:
                errors.append(f"components[{position}]: bom-ref duplicado «{ref}»")
            seen.add(ref)
        purl = item.get("purl")
        if purl is not None and not str(purl).startswith("pkg:"):
            errors.append(f"components[{position}]: purl debe empezar por pkg:")
    return errors


def index_components(bom: dict) -> list[dict]:
    return [item for item in bom.get("components") or [] if isinstance(item, dict)]


def audit(sbom: dict, advisories: list[dict], repo: Path | None) -> dict:
    components = index_components(sbom)
    reachability = scan_imports(repo, components) if repo else {}
    vulnerable = []
    unknown = []

    for item in components:
        version = str(item.get("version") or "")
        matches = []
        for advisory in advisories:
            if not isinstance(advisory, dict):
                continue
            if str(advisory.get("package", "")).lower() != str(item.get("name", "")).lower():
                continue
            ecosystem = advisory.get("ecosystem")
            if ecosystem and ecosystem != ecosystem_of(item):
                continue
            if version == "unpinned":
                unknown.append({"component": item.get("name"), "advisory": advisory.get("id"), "reason": "unpinned"})
                continue
            try:
                affected = satisfies(version, str(advisory.get("affected") or ""))
            except ValueError:
                unknown.append({"component": item.get("name"), "advisory": advisory.get("id"), "reason": "rango no interpretable"})
                continue
            if not affected:
                continue
            matches.append({
                "id": advisory.get("id"),
                "severity": advisory.get("severity"),
                "affected": advisory.get("affected"),
                "fixed": advisory.get("fixed"),
                "summary": advisory.get("summary"),
                "reachability": reachability.get(item["bom-ref"], "unknown"),
            })
        if matches:
            vulnerable.append({
                "purl": item.get("purl"),
                "name": item.get("name"),
                "version": version,
                "advisories": matches,
            })

    statuses = [entry["reachability"] for group in vulnerable for entry in group["advisories"]]
    blocked = any(
        entry["reachability"] == "reachable" and str(entry["severity"]).lower() in HIGH_SEVERITIES
        for group in vulnerable for entry in group["advisories"]
    )

    return {
        "sbom": None,
        "repo": str(repo) if repo else None,
        "components": len(components),
        "vulnerable": vulnerable,
        "unresolved": unknown,
        "counts": {
            "components": len(components),
            "vulnerable_components": len(vulnerable),
            "reachable": statuses.count("reachable"),
            "test_only": statuses.count("test-only"),
            "not_imported": statuses.count("not-imported"),
            "unknown": statuses.count("unknown"),
        },
        "gate": {"fail_on": "reachable", "blocked": blocked},
    }


def load_advisories(path: Path) -> list[dict]:
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("advisories"), list):
        raise ValueError("el fichero de avisos no tiene una lista «advisories»")
    return data["advisories"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SBOM CycloneDX con CVE y alcanzabilidad.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Genera el SBOM de un directorio")
    build.add_argument("target")
    build.add_argument("--output")
    build.add_argument("--now")

    audit_cmd = sub.add_parser("audit", help="Cruza avisos y calcula alcanzabilidad")
    audit_cmd.add_argument("sbom")
    audit_cmd.add_argument("--advisories", required=True)
    audit_cmd.add_argument("--repo")
    audit_cmd.add_argument("--output")
    audit_cmd.add_argument("--json", action="store_true")
    audit_cmd.add_argument("--fail-on", choices=("reachable", "none"), default="reachable")

    validate = sub.add_parser("validate", help="Valida la estructura mínima del SBOM")
    validate.add_argument("sbom")
    validate.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    args = _build_parser().parse_args(argv)

    if args.command == "build":
        return _command_build(args)

    path = Path(args.sbom)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2

    if args.command == "validate":
        return _command_validate(args, path)
    return _command_audit(args, path)


def _command_build(args: argparse.Namespace) -> int:
    target = Path(args.target)
    if not target.is_dir():
        print(f"No existe el directorio: {target}", file=sys.stderr)
        return 2
    bom = build_bom(target, args.now)
    if not bom["components"]:
        print("No se encontraron manifiestos legibles (package.json, requirements.txt, "
              "pyproject.toml, go.mod)", file=sys.stderr)
        return 1
    text = json.dumps(bom, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"SBOM escrito en {args.output} ({len(bom['components'])} componente(s))")
    else:
        print(text, end="")
    return 0


def _command_validate(args: argparse.Namespace, path: Path) -> int:
    try:
        bom = load_json(path)
    except (json.JSONDecodeError, OSError, ValueError, TypeError, AttributeError) as error:
        print(f"SBOM ilegible: {error}", file=sys.stderr)
        return 2
    errors = validate_bom(bom)
    if args.json:
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    elif errors:
        print(f"INVÁLIDO: {len(errors)} problema(s)")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"OK: {len(bom.get('components', []))} componente(s) CycloneDX {bom.get('specVersion')}")
    return 0 if not errors else 1


def _command_audit(args: argparse.Namespace, path: Path) -> int:
    try:
        bom = load_json(path)
        advisories = load_advisories(Path(args.advisories))
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"No se pudo leer la entrada: {error}", file=sys.stderr)
        return 2

    repo = Path(args.repo) if args.repo else None
    if repo is not None and not repo.is_dir():
        print(f"No existe el repositorio: {repo}", file=sys.stderr)
        return 2

    report = audit(bom, advisories, repo)
    report["sbom"] = str(path)
    report["gate"] = {"fail_on": args.fail_on, "blocked": report["gate"]["blocked"] and args.fail_on == "reachable"}
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

    if args.json:
        print(text, end="")
    else:
        _print_audit(report, args)

    return 1 if report["gate"]["blocked"] else 0


def _print_audit(report: dict, args: argparse.Namespace) -> None:
    counts = report["counts"]
    print(f"{counts['components']} componente(s) · {counts['vulnerable_components']} vulnerable(s) · "
          f"reachable {counts['reachable']} · test-only {counts['test_only']} · "
          f"not-imported {counts['not_imported']}")
    for group in report["vulnerable"]:
        for entry in group["advisories"]:
            print(f"  {entry['id']} {group['name']}@{group['version']} "
                  f"({entry['severity']}, {entry['reachability']})")
    for item in report["unresolved"]:
        print(f"  ? {item['component']}: {item['advisory']} ({item['reason']})")
    if report["gate"]["blocked"]:
        print("BLOQUEADO: hay avisos reachable de severidad alta o crítica")
    if args.output:
        print(f"Informe escrito en {args.output}")


if __name__ == "__main__":
    sys.exit(main())
