# Agent Instructions — fraud-risk-pipeline

Handoff doc for new chats. Keep context lean: use Serena symbols first, then small targeted reads.

## Project summary

Real-time **fraud risk API** (FastAPI) with:

- Committed **IEEE-CIS** XGBoost model (`artifacts/xgboost_model.json`)
- **Cost-based threshold** `0.722727` (`artifacts/threshold.json`)
- **Tree SHAP** feature reasons (`src/explain/tree_shap.py`)
- **Template** analyst summary aligned to threshold (`src/explain/summary.py`) — not an LLM on `/predict`
- **Evidently** drift reports (`make monitor`)
- **Fly.io** deploy scaffold (`fly.toml`, `Dockerfile`) — **not deployed yet** (README badge still “coming soon”)

**Dataset:** IEEE-CIS Fraud Detection (Kaggle). Full train on Kaggle GPU; repo ships small CSVs for local smoke runs.

**Headline test metrics (IEEE-CIS, time-based last 20%):** PR-AUC 0.440, precision 0.306, recall 0.541.

## Git state (as of last handoff)

| Item | Value |
|------|--------|
| Branch | `main` |
| Latest commit | `75434f6` — drift monitoring, deploy config, gitignore, threshold fix |
| Remote | May be **1 commit ahead** of `origin/main` — run `git push` if not pushed |
| Prior commits | `2b212ef` model+SHAP serve, `c165906` Kaggle IEEE train, `4b3d008` local train scaffold |

**User runs git** unless explicitly asked to commit/push.

## Repo layout (modular — avoid mega-files)

| Path | Responsibility |
|------|----------------|
| `src/api/` | FastAPI routes + Pydantic schemas only (`main.py` orchestrates) |
| `src/model/` | `RiskModel` — load artifact, predict, heuristic fallback if artifacts missing |
| `src/features/` | `ieee.py` serving alignment; `pipeline.py` for sample/local train features |
| `src/explain/` | Tree SHAP, domain config, template `explain()` |
| `src/train/` | Local training on `data/sample.csv` (split, metrics, threshold, MLflow) |
| `src/monitor/` | Evidently drift (`config.py`, `drift.py`, `generate_drift_report.py`) |
| `kaggle_kernel/` | Full IEEE-CIS training (`train_ieee.py`) — source of committed artifacts |
| `ui/` | Streamlit client → POST `/predict` |
| `artifacts/` | Committed: `xgboost_model.json`, `metrics.json`, `threshold.json`, `feature_list.json`, `model_card.md` |
| `data/` | `sample.csv` (local train); `monitoring_*.csv` (drift demo) |
| `tests/` | API, model, IEEE features, explain, threshold, monitor |

**Entrypoints (`main()`):** each module uses `if __name__ == "__main__"` only — `src/train/train.py`, `src/monitor/generate_drift_report.py`, `kaggle_kernel/train_ieee.py`. API is `uvicorn src.api.main:app`, not a `main()` function.

## Commands

```bash
make install          # pip install -r requirements.txt
make test             # pytest (8 tests)
make lint             # .venv/bin/ruff check src tests ui
make serve            # uvicorn src.api.main:app --reload
make ui               # streamlit (API must be running)
make train            # local sample.csv baseline + mlruns/
make monitor          # docs/media/drift_report.html + drift_summary.json
```

**macOS:** XGBoost may need `brew install libomp`.

**Env (see `.env.example`):** `MODEL_ARTIFACT_PATH`, `RISK_THRESHOLD`, `MLFLOW_TRACKING_URI`, optional HF vars for future LLM.

## Context tools

- **Serena** — Python LSP enabled: `.serena/project.yml` → `languages: [python]`, `ls_path: .venv/bin/python`. `pyrightconfig.json` points at `.venv`. **Restart Serena MCP** after config changes if symbols fail.
- **Graphify** — only if `graphify-out/` exists; not built for this repo yet.
- **Context7** — library/API docs when implementing deps.
- **Repomix** — token audits only; do not pack whole repo by default.

## Generated / ignored paths (see `.gitignore`)

Do not read unless the task requires it:

- `.venv/`, `mlruns/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`
- `docs/media/*.html`, `docs/media/drift_summary.json` (regenerate with `make monitor`)
- `graphify-out/`, `repomix-output.*`, `.serena/cache/`
- `data/raw/`, `data/ieee/`, `*.parquet`, `kaggle_output/`
- Heavy model formats under `artifacts/` (`*.pkl`, `*.ubj`, etc.) — committed artifact is `xgboost_model.json`

## Known limitations

1. **Serving features:** API payloads are sparse; `build_serving_frame()` zero-fills ~175 IEEE columns. Demo fields: `TransactionAmt`, `TransactionDT`, `ProductCD`, `card1` (+ aliases `amount`, `hour`).
2. **Two train paths:** `make train` ≠ Kaggle IEEE pipeline. Production artifact comes from `kaggle_kernel/train_ieee.py` only.
3. **LLM:** `/predict` uses template `explain()`; optional `POST /explain/llm` calls HF serverless inference when `HF_API_TOKEN` is set.
4. **Deploy:** `fly.toml` ready; live URL and README badge not updated until `fly deploy` succeeds.

## Verification

After code changes:

1. `make test` (smallest check)
2. `make lint` if touching `src/`, `tests/`, `ui/`
3. Smoke: `make serve` + curl `/predict` or `make ui`
4. Drift: `make monitor` if touching `src/monitor/`

## Next tasks (priority order)

### P0 — Ship the demo

- [ ] **`git push`** `main` if commit `75434f6` is still local only
- [ ] **`fly deploy`** — create app if needed, deploy, verify `/health` and `/predict`
- [ ] Update README **Live Demo** badge + URL after deploy

### P1 — Portfolio polish

- [ ] **`make data` script** — download/prepare IEEE-CIS sample for local dev (document Kaggle rules acceptance)
- [ ] **CI** — GitHub Action: `make test` + `make lint` (+ optional `make monitor` with committed monitoring CSVs)
- [ ] **Streamlit** — show threshold, decision, SHAP table more clearly; link to drift report if hosted

### P2 — Production gaps

- [x] **On-demand LLM summary** — `POST /explain/llm` via HF serverless inference (`HF_API_TOKEN`); does not change `/predict`
- [ ] **Auth** — API keys or JWT for public deploy
- [ ] **Richer serving features** — align inference with Kaggle training feature engineering (or document required field set)
- [ ] **Drift on real traffic** — replace `monitoring_*.csv` with production logs reference/current slices

### P3 — V2 roadmap (README)

- Streaming ingestion, Airflow/dbt, feature store, fine-tuned LLM

## References

- Kaggle train: https://www.kaggle.com/code/aditya2402/fraud-risk-pipeline-ieee-cis-train
- Architecture: `docs/architecture.md`
- User-facing docs: `README.md`
