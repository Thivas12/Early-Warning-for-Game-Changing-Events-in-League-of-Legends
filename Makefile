.PHONY: install format lint type test audit diagnose benchmark paper security check

install:
	uv sync --all-groups

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .

type:
	uv run mypy src

test:
	uv run pytest

audit:
	uv run league-ews audit --csv audit-data/final_dataset.csv --output reports/local/audit.json

diagnose:
	uv run league-ews diagnose-split --csv audit-data/final_dataset.csv --output reports/local/split-diagnostic.json

benchmark:
	uv run league-ews benchmark --csv audit-data/final_dataset.csv --output reports/local

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

security:
	uv run --group security pip-audit
	scripts/check-secrets.sh

check: lint type test
