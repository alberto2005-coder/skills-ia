from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent
FIXTURES = TEST_DIR / "fixtures"

MASTER_MAX_LINES = 200

REQUIRED_FILES = [
    "SKILL.md",
    "appsec-recon/SKILL.md",
    "appsec-code/SKILL.md",
    "appsec-infra/SKILL.md",
    "appsec-llm/SKILL.md",
    "appsec-report/SKILL.md",
    "references/benchmark.md",
    "references/sources-sinks.md",
    "references/owasp-cwe.md",
    "references/cloud-iac.md",
    "references/llm-agents-mcp.md",
    "references/prompt-injection-defense.md",
    "templates/report.md",
    "templates/finding.md",
    "templates/tribunal.md",
    "scripts/scan_secrets.py",
    "scripts/map_flows.py",
    "scripts/grade.py",
    "scripts/init_audit.py",
    "scripts/validate_findings.py",
    "scripts/ledger.py",
    "schemas/findings.schema.json",
    "schemas/coverage-ledger.schema.json",
    "references/artifacts.md",
    "skills.json",
]

SUB_SKILLS = ["appsec-recon", "appsec-code", "appsec-infra", "appsec-llm", "appsec-report"]


def read_file(relative: str) -> str:
    path = SKILL_ROOT / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""
