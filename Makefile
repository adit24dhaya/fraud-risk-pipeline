PYTHON ?= .venv/bin/python

.PHONY: install test lint format serve ui train monitor

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

lint:
	ruff check src tests ui

format:
	ruff format src tests ui

serve:
	uvicorn src.api.main:app --reload

ui:
	streamlit run ui/app.py

train:
	$(PYTHON) -m src.train.train

monitor:
	$(PYTHON) -m src.monitor.generate_drift_report
