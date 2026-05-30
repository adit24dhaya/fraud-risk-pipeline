# Architecture

```text
Transaction input (UI / API / curl)
        |
        v
FastAPI -> Feature pipeline -> model -> probability + threshold decision
        |
        v
SHAP/top feature reasons -> reusable explainer -> on-demand analyst summary
```

The analyst summary is template-based from SHAP drivers and the cost-based threshold. It is not part of the real-time model scoring path.

Drift monitoring (`make monitor`) compares reference vs current tabular slices with Evidently and writes `docs/media/drift_report.html`.
