import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_model_card(
    path: Path,
    metrics: dict[str, float],
    threshold: float,
    feature_names: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Fraud Risk Baseline Model",
                "",
                "## Intended Use",
                "Transaction-risk screening for analyst review. The model does not make final fraud determinations.",
                "",
                "## Data Note",
                "These metrics are from the committed sample scaffold dataset. Replace with IEEE-CIS or ULB data before treating scores as meaningful.",
                "",
                "## Headline Metrics",
                f"- PR-AUC: {metrics['pr_auc']:.4f}",
                f"- Precision: {metrics['precision']:.4f}",
                f"- Recall: {metrics['recall']:.4f}",
                "",
                "## Threshold",
                f"Decision threshold: {threshold:.4f}",
                "",
                "Threshold is selected by expected cost, weighing missed fraud higher than false positives.",
                "",
                "## Features",
                *[f"- {name}" for name in feature_names],
                "",
            ]
        ),
        encoding="utf-8",
    )
