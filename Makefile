.PHONY: install format lint type test preflight preflight-discovery validate-sampling-frame validate-discovery-plan validate-duration-rule validate-final-discovery-plan preflight-final-discovery discover-final-candidates validate-final-candidate-pool validate-final-selection-plan preflight-final-selection select-final validate-final-selection preflight-final-collection collect-selected-final validate-final process-final validate-final-processed prepare-final-event-review validate-final-g2 discover-candidates validate-candidate-pool preflight-pilot-selection select-pilot validate-pilot-selection preflight-pilot-collection collect-selected-pilot validate-pilot process-pilot analyze-pilot-duration validate-raw audit diagnose benchmark paper security check

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

validate-pilot-selection:
	uv run league-ews validate-pilot-selection \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery \
		--selection-root data/private/pilot-selection

preflight-pilot-collection:
	uv run league-ews preflight-pilot-collection \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery \
		--selection-root data/private/pilot-selection

collect-selected-pilot:
	uv run league-ews collect-selected-pilot \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery \
		--selection-root data/private/pilot-selection \
		--output data/raw/registered-pilot

validate-pilot:
	uv run league-ews validate-raw \
		--raw data/raw/registered-pilot \
		--output data/private/pilot-validation.json \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--sampling-stage pilot \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery \
		--selection-root data/private/pilot-selection \
		--min-routes 2 \
		--min-patches 6

process-pilot:
	uv run league-ews process \
		--raw data/raw/registered-pilot \
		--output data/processed/registered-pilot \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--sampling-stage pilot \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery \
		--selection-root data/private/pilot-selection \
		--min-routes 2 \
		--min-patches 6

analyze-pilot-duration:
	uv run league-ews analyze-pilot-duration \
		--raw data/raw/registered-pilot \
		--processed data/processed/registered-pilot \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--discovery-plan configs/rifthazard-discovery-plan.yaml \
		--discovery-root data/private/pilot-discovery \
		--selection-root data/private/pilot-selection \
		--output data/private/pilot-duration-analysis.json

validate-duration-rule:
	uv run league-ews validate-duration-rule \
		--rule configs/rifthazard-duration-rule.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--analysis data/private/pilot-duration-analysis.json \
		--output data/private/duration-rule-validation.json

validate-final-discovery-plan:
	uv run league-ews validate-final-discovery-plan \
		--plan configs/rifthazard-final-discovery-plan.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml

preflight-final-discovery:
	uv run league-ews preflight-final-discovery \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--output data/private/final-discovery-preflight.json

discover-final-candidates:
	uv run league-ews discover-final-candidates \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--output data/private/final-discovery

validate-final-candidate-pool:
	uv run league-ews validate-final-candidate-pool \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--output data/private/final-candidate-pool-validation.json

validate-final-selection-plan:
	uv run league-ews validate-final-selection-plan \
		--plan configs/rifthazard-final-selection-plan.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml

preflight-final-selection:
	uv run league-ews preflight-final-selection \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--output data/private/final-selection-preflight.json

select-final:
	uv run league-ews select-final \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--output data/private/final-selection

validate-final-selection:
	uv run league-ews validate-final-selection \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--final-selection-root data/private/final-selection \
		--output data/private/final-selection-validation.json

preflight-final-collection:
	uv run league-ews preflight-final-collection \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--final-selection-root data/private/final-selection \
		--output data/private/final-collection-preflight.json

collect-selected-final:
	uv run league-ews collect-selected-final \
		--authority-record data/private/riot-authority.yaml \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--final-selection-root data/private/final-selection \
		--output data/raw/registered-final

validate-final:
	uv run league-ews validate-raw \
		--raw data/raw/registered-final \
		--output data/private/final-validation.json \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--sampling-stage final \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--final-selection-root data/private/final-selection \
		--min-routes 2 \
		--min-patches 6

process-final:
	uv run league-ews process \
		--raw data/raw/registered-final \
		--output data/processed/registered-final \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--sampling-stage final \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--final-selection-root data/private/final-selection \
		--min-routes 2 \
		--min-patches 6 \
		--max-new-matches 2000

validate-final-processed:
	uv run league-ews validate-processed \
		--raw data/raw/registered-final \
		--processed data/processed/registered-final \
		--raw-validation data/private/final-validation.json \
		--output data/private/final-processed-validation.json

prepare-final-event-review:
	uv run league-ews prepare-final-event-review \
		--raw data/raw/registered-final \
		--processed data/processed/registered-final \
		--processed-audit data/private/final-processed-validation.json \
		--output data/private/final-event-review-packet.json

validate-final-g2:
	uv run league-ews validate-raw \
		--raw data/raw/registered-final \
		--processed data/processed/registered-final \
		--event-spot-check data/private/final-event-spot-check.json \
		--output data/private/final-g2-validation.json \
		--sampling-frame configs/rifthazard-sampling-frame.yaml \
		--sampling-stage final \
		--duration-rule configs/rifthazard-duration-rule.yaml \
		--duration-analysis data/private/pilot-duration-analysis.json \
		--final-selection-plan configs/rifthazard-final-selection-plan.yaml \
		--final-discovery-plan configs/rifthazard-final-discovery-plan.yaml \
		--pilot-discovery-plan configs/rifthazard-discovery-plan.yaml \
		--pilot-discovery-root data/private/pilot-discovery \
		--pilot-selection-root data/private/pilot-selection \
		--final-discovery-root data/private/final-discovery \
		--final-selection-root data/private/final-selection \
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
