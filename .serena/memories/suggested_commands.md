# Suggested Commands

- Install deps: `make install` (`.venv/bin/python -m pip install -r requirements.txt`).
- Run tests: `make test` (`.venv/bin/python -m pytest -q`).
- Lint: `make lint` (`.venv/bin/ruff check src tests ui`).
- Format: `make format` (`.venv/bin/ruff format src tests ui`).
- Serve API: `make serve` or `.venv/bin/uvicorn src.api.main:app --reload`.
- Run Streamlit UI: `make ui` or `.venv/bin/streamlit run ui/app.py` while API is available.
- Local sample train: `make train`.
- Drift report: `make monitor`, generating `docs/media/drift_report.html` and `docs/media/drift_summary.json`.
- Git state checks: `git status --short --branch`, `git log --oneline -5`.
- Prefer `rg`/`rg --files` for local search; avoid generated/heavy paths unless needed: `.venv/`, `mlruns/`, `docs/media/*.html`, `graphify-out/`, `data/raw/`, `data/ieee/`, `*.parquet`, heavy artifact formats.