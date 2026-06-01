# Core

- Fraud risk FastAPI project serving a committed IEEE-CIS XGBoost artifact from `artifacts/xgboost_model.json` with cost threshold from `artifacts/threshold.json`.
- Main serving flow: `src/api/main.py` owns FastAPI routes only; `RiskModel` in `src/model/risk_model.py` loads artifacts/predicts; `src/features/ieee.py` aligns sparse payloads to training features; `src/explain/` adds Tree SHAP drivers and template analyst summaries.
- `/predict` uses deterministic template summary; on-demand LLM path is separate `POST /explain/llm` and needs `HF_API_TOKEN`.
- Drift workflow lives in `src/monitor/`, comparing committed demo monitoring CSVs and writing generated files under `docs/media/`.
- Full production artifact is trained by `kaggle_kernel/train_ieee.py`; local `make train` is only a sample-data baseline.
- Deployment scaffold is Fly.io (`fly.toml`, `Dockerfile`) but live URL/README badge should only change after a successful deploy.
- Read tech/deps in `mem:tech_stack`; local commands in `mem:suggested_commands`; project style in `mem:conventions`; finish checks in `mem:task_completion`.