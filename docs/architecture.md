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

The LLM analyst summary is for human review only. It is not part of the real-time model scoring path.
