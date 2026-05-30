import json
from pathlib import Path

from src.monitor.config import MonitorConfig
from src.monitor.drift import generate_drift_report


def test_generate_drift_report_writes_outputs(tmp_path: Path) -> None:
    config = MonitorConfig(
        reference_path=Path("data/monitoring_reference.csv"),
        current_path=Path("data/monitoring_current.csv"),
        output_html=tmp_path / "drift_report.html",
        output_json=tmp_path / "drift_summary.json",
    )
    summary = generate_drift_report(config)

    assert config.output_html.exists()
    assert config.output_json.exists()
    payload = json.loads(config.output_json.read_text(encoding="utf-8"))
    assert payload["reference_rows"] > 0
    assert payload["current_rows"] > 0
    assert "columns_checked" in payload
    assert summary["dataset_drift"] is True
