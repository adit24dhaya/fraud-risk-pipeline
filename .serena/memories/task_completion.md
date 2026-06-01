# Task Completion

- After code changes, run `make test` as the baseline check.
- Run `make lint` when touching `src/`, `tests/`, or `ui/`.
- If serving behavior changes, smoke API with `make serve` plus `/health` and `/predict` sample request.
- If Streamlit UI changes, run `make serve` and `make ui`, then verify the UI can submit different transaction values.
- If drift code/data changes, run `make monitor` and inspect that `docs/media/drift_report.html` plus `docs/media/drift_summary.json` are regenerated.
- For deploy docs, only update live badge/URL after an actual successful Fly deploy and endpoint verification.