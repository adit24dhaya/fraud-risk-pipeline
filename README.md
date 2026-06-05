# Real-Time Transaction Risk & Fraud Detection Pipeline

[![Live UI](https://img.shields.io/badge/Live%20UI-Heroku-430098)](https://adit-txn-risk-pipeline-ui-e2c4483417ee.herokuapp.com/)
[![Live API](https://img.shields.io/badge/Live%20API-Heroku-6762A6)](https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com/docs)
[![CI](https://github.com/adit24dhaya/fraud-risk-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/adit24dhaya/fraud-risk-pipeline/actions/workflows/ci.yml)

Production-style fraud scoring on the [IEEE-CIS Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection) dataset: XGBoost inference, cost-based thresholding, Tree SHAP explainability, Evidently drift monitoring, and a portfolio Streamlit workbench backed by a FastAPI service.

## Live demo

| Surface | URL |
| --- | --- |
| **Streamlit workbench** | https://adit-txn-risk-pipeline-ui-e2c4483417ee.herokuapp.com/ |
| **FastAPI docs (Swagger)** | https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com/docs |
| **Health check** | https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com/health |

Try a live prediction:

```bash
curl -X POST https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com/predict \
  -H "Content-Type: application/json" \
  -d '{"transaction":{"TransactionAmt":250,"TransactionDT":7500000,"ProductCD":"W","card1":12345,"hour":23}}'
```

The UI auto-runs the **Review edge** scenario on first load, then lets you switch presets and re-score. JSON request/response details are tucked under **Technical details**.

## What this shows

This is an end-to-end ML service, not a notebook. A transaction flows through:

`sparse JSON → IEEE feature alignment → XGBoost → cost-based decision → Tree SHAP → analyst summary`

Each response includes:

- fraud probability from the committed model artifact
- `approve` or `flag_for_review` at threshold `0.722727`
- top Tree SHAP drivers with risk direction
- plain-English analyst summary (template on `/predict`; optional LLM on `/explain/llm`)

## Feature surface

| Area | What is implemented |
| --- | --- |
| Real-time API | `GET /health`, `POST /predict`, optional `POST /explain/llm` |
| Model serving | Committed IEEE-CIS XGBoost artifact (`artifacts/xgboost_model.json`) |
| Thresholding | Cost-based threshold from `artifacts/threshold.json` (`0.722727`) |
| Feature alignment | Sparse payloads aligned to 175 IEEE features with zero-fill fallback |
| Explanations | Tree SHAP top features with `increases_risk` / `decreases_risk` labels |
| Analyst summary | Deterministic template on `/predict`; HF LLM summary on `/explain/llm` |
| UI | Streamlit portfolio demo — scenario presets, decision card, SHAP driver cards |
| Monitoring | Evidently drift report (`make monitor`) on committed monitoring CSVs |
| Access control | Optional `X-API-Key` when `API_KEY` is set (open by default for demo) |
| Deploy | **Heroku** — separate API + UI apps; **Fly.io** scaffold as alternative |
| CI | GitHub Actions — `ruff` + `pytest` on `main` |

## Demo screenshots

Repo screenshots (local captures; the [live UI](https://adit-txn-risk-pipeline-ui-e2c4483417ee.herokuapp.com/) has the latest portfolio layout):

![Prediction examples with different transaction values](docs/media/prediction-examples.png)

![Streamlit fraud risk UI](docs/media/streamlit-ui.png)

![FastAPI docs screenshot](docs/media/api-docs.png)

![Evidently drift report screenshot](docs/media/drift-report.png)

## API

`GET /health` is always public. `POST /predict` and `POST /explain/llm` are public when `API_KEY` is unset; set `API_KEY` in the environment to require `X-API-Key`.

**Response shape:**

```json
{
  "fraud_probability": 0.728981,
  "decision": "flag_for_review",
  "threshold": 0.722727,
  "top_features": [
    {
      "feature": "C14",
      "shap_value": 0.548235,
      "direction": "increases_risk"
    }
  ],
  "analyst_summary": "Flagged for review: model score is 73%. Main risk signals..."
}
```

### Example scenarios (committed model)

| Scenario | Amount | Hour | Product | card1 | Fraud prob. | Decision | Top risk drivers |
| --- | ---: | ---: | --- | ---: | ---: | --- | --- |
| Low friction | 24.50 | 1 | W | 1000 | 0.335 | `approve` | C14 |
| Review edge | 250.00 | 23 | W | 12345 | 0.729 | `flag_for_review` | C14, TransactionAmt, D2 |
| High value | 1250.00 | 3 | C | 17000 | 0.759 | `flag_for_review` | TransactionAmt, C14, card6 |

## Inference contract

Supported demo fields (aliases in parentheses):

- `TransactionAmt` (`amount`)
- `TransactionDT`
- `ProductCD`
- `card1`
- `hour`

`src/features/ieee.py` aligns sparse requests to the trained feature list. Missing columns are zero-filled — fine for API/SHAP/UI demos, but production should send the full engineered feature set or mirror Kaggle training features.

## Metrics

| Model | Split | PR-AUC | Precision | Recall | Threshold |
| --- | --- | ---: | ---: | ---: | ---: |
| XGBoost v1 | IEEE-CIS time-based final 20% | 0.440 | 0.306 | 0.541 | 0.723 |

Accuracy is not the headline metric — fraud data is highly imbalanced. Full training metrics live in `artifacts/metrics.json`.

## Local development

**Requirements:** Python 3.11+, macOS users may need `brew install libomp` for XGBoost.

```bash
make install    # requirements.txt + requirements-dev.txt
make test       # 17 pytest tests
make lint
make serve      # http://localhost:8000/docs
make ui         # Streamlit → uses HEROKU_API_URL by default in Makefile
make monitor    # docs/media/drift_report.html + drift_summary.json
make train      # local baseline on data/sample.csv
```

Copy `.env.example` to `.env` for local overrides (`MODEL_ARTIFACT_PATH`, `RISK_THRESHOLD`, optional `HF_API_TOKEN`, `API_KEY`).

**UI against local API:**

```bash
make serve
FRAUD_API_URL=http://127.0.0.1:8000 streamlit run ui/app.py
```

### Optional LLM summary (Hugging Face)

`/predict` stays fast with the template summary. For an on-demand LLM note via [Hugging Face serverless inference](https://huggingface.co/docs/api-inference/index), set `HF_API_TOKEN` (and optionally `HF_MODEL_ID`) in `.env`:

```bash
curl -X POST http://localhost:8000/explain/llm \
  -H "Content-Type: application/json" \
  -d '{"transaction":{"TransactionAmt":250,"TransactionDT":7500000,"ProductCD":"W","card1":12345,"hour":23}}'
```

## Deploy (Heroku)

Two apps from one repo: **API** (repo root) and **Streamlit UI** (`ui/` subtree).

| App | Heroku name | URL |
| --- | --- | --- |
| API | `adit-txn-risk-pipeline` | https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com/docs |
| UI | `adit-txn-risk-pipeline-ui` | https://adit-txn-risk-pipeline-ui-e2c4483417ee.herokuapp.com/ |

### API (first-time setup)

```bash
heroku create adit-txn-risk-pipeline
heroku buildpacks:add heroku-community/apt -a adit-txn-risk-pipeline
heroku buildpacks:add heroku/python -a adit-txn-risk-pipeline
heroku config:set \
  MODEL_ARTIFACT_PATH=artifacts/xgboost_model.json \
  RISK_THRESHOLD=0.722727 \
  -a adit-txn-risk-pipeline
git remote add heroku https://git.heroku.com/adit-txn-risk-pipeline.git
git push heroku main
```

The API uses `Procfile`, slim `requirements.txt`, `Aptfile` (`libgomp1` for XGBoost), and `.slugignore` to keep the slug small.

### UI (first-time setup)

```bash
heroku create adit-txn-risk-pipeline-ui
heroku buildpacks:add heroku/python -a adit-txn-risk-pipeline-ui
heroku config:set \
  FRAUD_API_URL=https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com \
  -a adit-txn-risk-pipeline-ui
git remote add heroku-ui https://git.heroku.com/adit-txn-risk-pipeline-ui.git
make deploy-ui
```

`make deploy-ui` splits `ui/` into a subtree branch and pushes to the UI remote. The UI reads `FRAUD_API_URL` from the environment — no connection sidebar in production.

**Optional API secrets on Heroku:**

- `HF_API_TOKEN` — enables `POST /explain/llm`
- `API_KEY` — requires `X-API-Key` on predict/LLM routes (leave unset for open demo)

## Deploy (Fly.io)

Alternative to Heroku. Requires [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/).

```bash
fly apps create fraud-risk-pipeline   # once
fly deploy
fly open /docs
```

The `Dockerfile` bundles the model artifact and serves FastAPI on port 8000. Override `RISK_THRESHOLD` or `MODEL_ARTIFACT_PATH` with `fly secrets set` if needed.

## Drift monitoring

`make monitor` compares `data/monitoring_reference.csv` to `data/monitoring_current.csv` and writes:

- `docs/media/drift_report.html` — interactive Evidently report
- `docs/media/drift_summary.json` — compact summary for CI or dashboards

## Full training

Full IEEE-CIS training runs on Kaggle with GPU:

https://www.kaggle.com/code/aditya2402/fraud-risk-pipeline-ieee-cis-train

Reproducible source: `kaggle_kernel/train_ieee.py` → committed artifacts in `artifacts/`.

`make train` is a separate local baseline on `data/sample.csv` only.

## Project structure

```
src/api/          FastAPI routes + schemas
src/model/        RiskModel — load artifact, predict
src/features/     IEEE serving alignment + local train features
src/explain/      Tree SHAP, template summary, optional HF LLM
src/monitor/      Evidently drift pipeline
src/train/        Local sample.csv training
ui/               Streamlit portfolio demo (separate Heroku app)
artifacts/        Model, threshold, metrics, feature list
kaggle_kernel/    Full IEEE-CIS training script
```

Architecture notes: `docs/architecture.md`

## Status

Verified June 2, 2026:

- `make test` — 17 passed
- `make lint` — clean
- GitHub Actions CI on `main`
- Heroku API + UI deployed and reachable
- Fly.io config present; Heroku is the primary live demo path

## V2 roadmap

- streaming ingestion
- Airflow/dbt/warehouse
- feature store
- richer serving features (full IEEE engineering parity)
- drift on real production traffic
- fine-tuned or self-hosted LLM
