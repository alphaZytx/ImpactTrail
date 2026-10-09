PYTHON ?= python3.11
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: setup models seed doctor demo live api dashboard test coverage quality evaluate release submission clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -r requirements-dev.txt

models:
	$(BIN)/python -m pip install -r requirements-ml.txt
	$(BIN)/python scripts/download_models.py

seed:
	$(BIN)/python scripts/generate_portfolio.py
	$(BIN)/python scripts/update_data_manifest.py
	$(BIN)/python scripts/validate_data.py

doctor:
	$(BIN)/python -m riskpulse.cli doctor

demo:
	$(BIN)/python -m riskpulse.cli reset --yes
	$(BIN)/python -m riskpulse.cli replay --fixture data/demo/mixed_source_events.jsonl
	@echo "Data is ready. Run 'make api' and 'make dashboard' in separate terminals."

live:
	$(BIN)/python -m riskpulse.cli watch --query 'financial markets'

api:
	$(BIN)/uvicorn riskpulse.api.app:create_app --factory --host 127.0.0.1 --port 8000

dashboard:
	$(BIN)/streamlit run dashboard/app.py --server.port 8501

test:
	$(BIN)/pytest

coverage:
	$(BIN)/pytest --cov=riskpulse --cov-report=term-missing --cov-report=html

quality:
	$(BIN)/ruff format --check .
	$(BIN)/ruff check .
	$(BIN)/mypy src/riskpulse
	$(BIN)/python scripts/validate_data.py

evaluate:
	$(BIN)/python scripts/evaluate_models.py

release: quality coverage evaluate
	$(BIN)/python scripts/release_check.py

submission: release
	$(BIN)/python scripts/release_check.py --submission

clean:
	$(BIN)/python -m riskpulse.cli reset --yes
