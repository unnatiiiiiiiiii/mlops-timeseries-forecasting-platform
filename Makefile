.PHONY: install test ingest train canary-check run-api

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	python -m pytest -q

ingest:
	python scripts/ingest_data.py

train:
	python scripts/train_pipeline.py

canary-check:
	python scripts/canary_decision.py

run-api:
	uvicorn mlops_forecasting.api.main:app --host 0.0.0.0 --port 8000 --app-dir src
