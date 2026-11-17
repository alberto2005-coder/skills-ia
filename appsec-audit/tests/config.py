from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent
FIXTURES = TEST_DIR / "fixtures"

MASTER_MAX_LINES = 200

# Descubiertas del sistema de ficheros: una sub-skill nueva entra sola en los
# tests de gate/handoff, índice del maestro, prosa duplicada y ficheros
# obligatorios.
SUB_SKILLS = sorted(path.parent.name for path in SKILL_ROOT.glob("*/SKILL.md"))

# Assets que no son skills; las sub-skills se añaden desde SUB_SKILLS.
REQUIRED_ASSETS = [
    "references/benchmark.md",
    "references/sources-sinks.md",
    "references/owasp-cwe.md",
    "references/cloud-iac.md",
    "references/llm-agents-mcp.md",
    "references/prompt-injection-defense.md",
    "templates/report.md",
    "templates/finding.md",
    "templates/tribunal.md",
    "templates/verification.md",
    "templates/threat-model.md",
    "templates/pr-comment.md",
    "scripts/scan_secrets.py",
    "scripts/map_flows.py",
    "scripts/grade.py",
    "scripts/init_audit.py",
    "scripts/validate_findings.py",
    "scripts/ledger.py",
    "scripts/export_sarif.py",
    "scripts/diff_scope.py",
    "scripts/diff_reports.py",
    "schemas/sbom.schema.json",
    "scripts/sbom.py",
    "scripts/detect_tools.py",
    "scripts/normalize_sarif.py",
    "scripts/apply_patch.py",
    "scripts/scale_report.py",
    "schemas/findings.schema.json",
    "schemas/coverage-ledger.schema.json",
    "references/artifacts.md",
    "references/threat-model.md",
    "references/attack-classes.md",
    "references/deps-reachability.md",
    "references/agent-hardening.md",
    "references/remediation.md",
    "references/scale.md",
    "skills.json",
]

REQUIRED_FILES = ["SKILL.md"] + [f"{name}/SKILL.md" for name in SUB_SKILLS] + REQUIRED_ASSETS


def read_file(relative: str) -> str:
    path = SKILL_ROOT / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""
