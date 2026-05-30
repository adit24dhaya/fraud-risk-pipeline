import json
from pathlib import Path

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from src.monitor.config import MonitorConfig

DRIFT_COLUMNS = ("amount", "hour", "country", "merchant")


def load_monitoring_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    columns = [column for column in DRIFT_COLUMNS if column in frame.columns]
    if not columns:
        raise ValueError(f"No monitoring columns found in {path}")
    return frame[columns]


def generate_drift_report(config: MonitorConfig) -> dict[str, object]:
    reference = load_monitoring_frame(config.reference_path)
    current = load_monitoring_frame(config.current_path)

    report = Report([DataDriftPreset()])
    snapshot = report.run(current, reference)

    config.output_html.parent.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(str(config.output_html))

    summary = _build_summary(
        snapshot=snapshot,
        columns=reference.columns.tolist(),
        reference_rows=len(reference),
        current_rows=len(current),
        output_html=config.output_html,
    )
    config.output_json.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def _build_summary(
    snapshot: object,
    columns: list[str],
    reference_rows: int,
    current_rows: int,
    output_html: Path,
) -> dict[str, object]:
    payload = snapshot.dict() if hasattr(snapshot, "dict") else {}
    drifted: list[str] = []
    drifted_count = 0.0
    for metric in payload.get("metrics", []):
        name = str(metric.get("metric_name", ""))
        value = metric.get("value")
        if name.startswith("DriftedColumnsCount") and isinstance(value, dict):
            drifted_count = float(value.get("count", 0.0))
        config = metric.get("config", {})
        column = config.get("column")
        method = str(config.get("method", ""))
        if column and "p_value" in method and isinstance(value, (int, float)) and value < 0.05:
            drifted.append(column)
        if column and "drift" in method.lower() and isinstance(value, (int, float)) and value >= 0.95:
            drifted.append(column)

    drifted = sorted(set(drifted))
    return {
        "reference_rows": reference_rows,
        "current_rows": current_rows,
        "columns_checked": columns,
        "drift_detected_columns": drifted,
        "dataset_drift": bool(drifted) or drifted_count > 0,
        "report_html": str(output_html),
    }
