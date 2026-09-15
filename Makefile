.PHONY: install format lint type test preflight preflight-discovery validate-sampling-frame validate-discovery-plan discover-candidates validate-candidate-pool preflight-pilot-selection select-pilot validate-pilot validate-raw audit diagnose benchmark paper security check

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

validate-discovery-plan:
	uv run league-ews validate-discovery-plan \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--plan configs/rifthazard-discovery-plan.yaml

preflight-discovery:
	uv run league-ews preflight-discovery \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml

discover-candidates:
	uv run league-ews discover-candidates \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--output data/private/pilot-discovery

validate-candidate-pool:
	uv run league-ews validate-candidate-pool \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery

preflight-pilot-selection:
	uv run league-ews preflight-pilot-selection \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery

select-pilot:
	uv run league-ews select-pilot \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery \
		--output data/private/pilot-selection

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
