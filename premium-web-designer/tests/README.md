
# Automated Test Suite

## Requirements

- Python 3.9 or newer.
- The shared test environment is managed from the repository root with `uv`.
- The tests use the Python standard library; shared test and quality tools are declared in the root `pyproject.toml`.

## Run all tests

From the repository root:

```powershell
uv sync
uv run python run_tests.py
```

To run only this suite:

```powershell
uv run python premium-web-designer/tests/run_tests.py
```

## Generated reports

The runner creates:

reports/test-report.json
reports/test-report.txt

## Run individual tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Run a specific module:

```bash
python -m unittest discover -s tests -p "test_agents.py" -v
```

## Test categories

- Structure.
- Frontmatter.
- References.
- Agents.
- Workflows.
- Templates.
- Content quality.
- Portability.
- Security.

## Important

These tests validate documentation and
structural consistency.

They do not execute AI agents,
generate websites or guarantee visual quality.
