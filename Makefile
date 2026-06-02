PYTHON ?= .venv/bin/python
RUFF ?= .venv/bin/ruff

HEROKU_API_URL ?= https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com
HEROKU_UI_APP ?= adit-txn-risk-pipeline-ui

.PHONY: install test lint format serve ui train monitor deploy-ui

install:
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt

test:
	$(PYTHON) -m pytest -q

lint:
	$(RUFF) check src tests ui

format:
	$(RUFF) format src tests ui

serve:
	uvicorn src.api.main:app --reload

ui:
	FRAUD_API_URL=$(HEROKU_API_URL) streamlit run ui/app.py

deploy-ui:
	heroku config:set FRAUD_API_URL=$(HEROKU_API_URL) -a $(HEROKU_UI_APP)
	git push heroku-ui main

train:
	$(PYTHON) -m src.train.train

monitor:
	$(PYTHON) -m src.monitor.generate_drift_report
