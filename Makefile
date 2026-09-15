.PHONY: install format lint type test preflight validate-sampling-frame validate-pilot validate-raw audit diagnose benchmark paper security check

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

preflight:
	uv run league-ews preflight-collection \
		--record data/private/riot-authority.yaml \
		--region europe

validate-sampling-frame:
	uv run league-ews validate-sampling-frame \
		--frame configs/rifthazard-sampling-frame.yaml

validate-pilot:
	uv run league-ews validate-raw \
		--raw data/raw/pilot \
		--output data/private/pilot-validation.json \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--sampling-stage pilot \
		--min-routes 2 \
		--min-patches 6

validate-raw:
	uv run league-ews validate-raw \
		--raw data/raw \
		--output data/private/raw-validation.json \
		--min-routes 2 \
		--min-patches 6

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
