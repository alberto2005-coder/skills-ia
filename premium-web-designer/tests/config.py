from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent
REPORT_DIR = TEST_DIR / "reports"

REQUIRED_FILES = [
    "SKILL.md",
    "AGENTS.md",

    "agents/orchestrator.md",
    "agents/art-director.md",
    "agents/ux-ui-designer.md",
    "agents/frontend-developer.md",
    "agents/backend-specialist.md",
    "agents/qa-visual-auditor.md",

    "workflows/discovery.md",
    "workflows/creative-direction.md",
    "workflows/development.md",
    "workflows/review-and-iteration.md",
    "workflows/delivery.md",
    "workflows/hybrid-orchestration.md",

    "references/design-principles.md",
    "references/visual-quality.md",
    "references/responsive-design.md",
    "references/accessibility.md",
    "references/performance-seo.md",
    "references/ecommerce.md",
    "references/project-types.md",
    "references/tech-stack.md",

    "templates/project-brief.md",
    "templates/design-system.md",
    "templates/task-handoff.md",
    "templates/qa-report.md",
]

SPECIALISTS = [
    "orchestrator",
    "art-director",
    "ux-ui-designer",
    "frontend-developer",
    "backend-specialist",
    "qa-visual-auditor",
]

WORKFLOWS = [
    "discovery",
    "creative-direction",
    "development",
    "review-and-iteration",
    "delivery",
    "hybrid-orchestration",
]

def read_file(relative_path):
    path = SKILL_ROOT / relative_path

    if not path.is_file():
        return ""

    return path.read_text(encoding="utf-8")


def all_markdown_files():
    return list(SKILL_ROOT.rglob("*.md"))


def ensure_report_directory():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)