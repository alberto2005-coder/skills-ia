# Skills IA

A modular collection of agent skills for AI assistants. Each module is self-contained, relies strictly on the Python standard library, and follows a standardized architecture.

[Versión en Español](README.md)

---

## Included Modules

| Folder | Purpose |
| :--- | :--- |
| **`agent-red-team`** | Static security auditor and prompt injection detector for instructions. |
| **`humanizador-anti-ia`** | Stylistic rewriting to enhance sentence burstiness and vocabulary entropy. |
| **`replica`** | Clean-room functional reverse-engineering and specification of software. |
| **`seo-auditor`** | Technical, content, schema, and structural SEO audits for web and code. |

---

## Module Structure

Every skill folder follows the same layout:
- `SKILL.md`: Frontmatter activation triggers and execution guidelines.
- `references/`: Modular technical references and guides.
- `scripts/`: Deterministic utilities written in standard Python (zero dependencies).
- `templates/`: Markdown and CSV templates for structured output artifacts.

---

## Documentation

Comprehensive guides for every skill can be found in the [`docs/`](docs/) directory.
