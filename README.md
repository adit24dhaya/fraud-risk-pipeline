# Real-Time Transaction Risk & Fraud Detection Pipeline

[![Live Demo](https://img.shields.io/badge/Live%20Demo-coming%20soon-lightgrey)](#)

A real-time transaction-risk system: imbalanced-data fraud model with cost-based thresholding, Tree SHAP explainability, Evidently drift monitoring, and a reusable template-based analyst summary (same framing as a healthcare risk console; optional LLM on-demand in V2).

## What This Shows

This is a production-style fraud/risk service, not a notebook. A user sends a transaction to the API or demo UI and receives:

- fraud probability from the committed XGBoost model artifact
- decision at a documented threshold
- top feature contributions using XGBoost Tree SHAP values
- plain-English analyst summary

Scoring path:

`transaction -> feature alignment -> XGBoost -> probability + threshold decision -> Tree SHAP -> analyst summary`

The analyst summary is template-based from SHAP drivers and uses the same cost-based threshold as the API decision (not a fixed 0.5 cutoff).

## API

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"transaction":{"TransactionAmt":250,"TransactionDT":7500000,"ProductCD":"W","card1":12345}}'
```

Response shape:

```json
{
  "fraud_probability": 0.83,
  "decision": "flag_for_review",
  "threshold": 0.722727,
  "top_features": [
    {
      "feature": "TransactionAmt",
      "shap_value": 0.31,
      "direction": "increases_risk"
    }
  ],
  "analyst_summary": "Flagged for review: elevated risk signals include TransactionAmt and transaction_hour."
}
```

## Metrics

| Model | Split | PR-AUC | Precision | Recall | Threshold |
| --- | --- | ---: | ---: | ---: | ---: |
| XGBoost v1 | IEEE-CIS time-based final 20% | 0.440 | 0.306 | 0.541 | 0.723 |

Accuracy is intentionally not used as the headline metric because fraud data is highly imbalanced.

The committed `data/sample.csv` remains tiny so the repo can run without the full Kaggle download. Full training metrics above come from the IEEE-CIS Kaggle dataset.

## Local Development

```bash
make install
make test
make serve
make monitor   # Evidently drift HTML + JSON under docs/media/
```

Then visit `http://localhost:8000/docs`.

Streamlit UI (API must be running):

```bash
make ui
```

## Deploy (Fly.io)

Requires [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) and a Fly account.

```bash
fly apps create fraud-risk-pipeline   # once
fly deploy
fly open /docs
```

The `Dockerfile` bundles `artifacts/xgboost_model.json` and serves FastAPI on port 8000. Override `RISK_THRESHOLD` or `MODEL_ARTIFACT_PATH` with `fly secrets set` if needed.

## Drift monitoring

`make monitor` compares `data/monitoring_reference.csv` (reference) to `data/monitoring_current.csv` (current) on `amount`, `hour`, `merchant`, and `country`, then writes:

- `docs/media/drift_report.html` — interactive Evidently report
- `docs/media/drift_summary.json` — compact drift summary for CI or dashboards

## Full Training

The full IEEE-CIS run is executed on Kaggle with GPU enabled:

https://www.kaggle.com/code/aditya2402/fraud-risk-pipeline-ieee-cis-train

The reproducible kernel source lives in `kaggle_kernel/`. It writes the committed model and metric artifacts in `artifacts/`.

## Project Status

Current state: FastAPI serves the committed IEEE-CIS XGBoost model with Tree SHAP reasons, cost-aligned analyst summaries, Evidently drift reports, Fly.io deploy config, and smoke tests.

## Agent tooling (Serena)

Python LSP is enabled in `.serena/project.yml` (`languages: [python]`, Pyright via `.venv/bin/python`). After changing Serena config, restart the Serena MCP server in Cursor so symbol navigation works.

## V2 Roadmap

- streaming ingestion
- Airflow/dbt/warehouse
- feature store
- auth/API tokens
- fine-tuned or self-hosted LLM
