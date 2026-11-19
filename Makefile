# Empaquetado local: `make dist` (todos) o `make dist PACKAGE=replica` (uno).
UV ?= uv run --locked

.PHONY: dist clean-dist

dist:
	$(UV) python scripts/build_package.py $(if $(PACKAGE),$(PACKAGE),--all)

clean-dist:
	rm -rf dist
