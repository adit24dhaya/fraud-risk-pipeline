# Real-Time Transaction Risk & Fraud Detection Pipeline

[![Live Demo](https://img.shields.io/badge/Live%20Demo-coming%20soon-lightgrey)](#)

A deployed real-time transaction-risk system: imbalanced-data fraud model with cost-based thresholding, SHAP explainability, Evidently drift monitoring, and an on-demand LLM analyst-summary layer built as a reusable explainability component shared with a healthcare risk console.

## What This Shows

This is a production-style fraud/risk service, not a notebook. A user sends a transaction to the API or demo UI and receives:

- fraud probability
- decision at a documented threshold
- top feature contributions
- plain-English analyst summary

The fast scoring path is intentionally separate from the LLM layer:

`transaction -> feature pipeline -> model -> probability`

The LLM summary is on-demand for human analyst review. It must never block the real-time scoring path.

## API

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"transaction":{"amount":250,"merchant":"new_merchant","card_id":"card_001","country":"US","hour":23}}'
```

Response shape:

```json
{
  "fraud_probability": 0.83,
  "decision": "flag_for_review",
  "threshold": 0.42,
  "top_features": [
    {
      "feature": "amount_log",
      "shap_value": 0.31,
      "direction": "increases_risk"
    }
  ],
  "analyst_summary": "Flagged for review: elevated risk signals include amount_log and night_transaction."
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
```

Then visit `http://localhost:8000/docs`.

## Full Training

The full IEEE-CIS run is executed on Kaggle with GPU enabled:

https://www.kaggle.com/code/aditya2402/fraud-risk-pipeline-ieee-cis-train

The reproducible kernel source lives in `kaggle_kernel/`. It writes the committed model and metric artifacts in `artifacts/`.

## Project Status

Current state: v1 scaffold with FastAPI, reusable explainer contract, deterministic feature/model stubs, smoke tests, and deployment-ready structure. Next block is data loading plus a baseline LightGBM/XGBoost training run logged to MLflow.

## V2 Roadmap

- streaming ingestion
- Airflow/dbt/warehouse
- feature store
- auth/API tokens
- fine-tuned or self-hosted LLM
