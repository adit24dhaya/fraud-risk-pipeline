# Tech Stack

- Python project, Darwin dev environment, `.venv` expected; `.serena/project.yml` uses `.venv/bin/python` for Python LSP.
- API: FastAPI `0.115.13`, Pydantic `2.11.7`, Uvicorn `0.34.3`; app import is `src.api.main:app`.
- Modeling/data: pandas `2.2.3`, numpy `2.2.6`, scikit-learn `1.6.1`, XGBoost `2.1.4`, SHAP `0.46.0`, MLflow `2.22.0`.
- Monitoring: Evidently `0.7.21`.
- UI: Streamlit `1.45.1` plus `requests`.
- Tests/lint: pytest `8.3.5`, httpx `0.28.1`, Ruff `0.11.11`.
- macOS XGBoost may require `brew install libomp` outside Python deps.
- Runtime/config env: `MODEL_ARTIFACT_PATH`, `RISK_THRESHOLD`, `MLFLOW_TRACKING_URI`; HF envs are optional and only for LLM endpoint.