from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent
REPO_ROOT = SKILL_ROOT.parent

MASTER_MAX_LINES = 200
MASTER_MAX_COMMANDS = 6
SUB_SKILLS = ("eval-design", "eval-run", "eval-report")

PHRASES = REPO_ROOT / "tests" / "phrases.json"
ROOT_INDEX = REPO_ROOT / "skills.json"

REQUIRED_FILES = [
    "SKILL.md",
    "skills.json",
    "eval-design/SKILL.md",
    "eval-run/SKILL.md",
    "eval-report/SKILL.md",
    "references/competitors.md",
    "references/metrics.md",
    "templates/eval-cases.json",
    "templates/report.md",
    "scripts/evalkit.py",
    "scripts/design.py",
    "scripts/run.py",
    "scripts/report.py",
]


def read_file(name: str) -> str:
    return (SKILL_ROOT / name).read_text(encoding="utf-8")
