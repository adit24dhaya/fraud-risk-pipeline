import os
from pathlib import Path

from src.monitor.config import MonitorConfig
from src.monitor.drift import generate_drift_report


def main() -> None:
    config = MonitorConfig(
        reference_path=Path(
            os.getenv("DRIFT_REFERENCE_PATH", "data/monitoring_reference.csv")
        ),
        current_path=Path(
            os.getenv("DRIFT_CURRENT_PATH", "data/monitoring_current.csv")
        ),
        output_html=Path(os.getenv("DRIFT_REPORT_HTML", "docs/media/drift_report.html")),
        output_json=Path(os.getenv("DRIFT_REPORT_JSON", "docs/media/drift_summary.json")),
    )
    summary = generate_drift_report(config)
    print(
        "Drift report written: "
        f"{summary['report_html']} "
        f"(drift columns: {summary['drift_detected_columns']})"
    )


if __name__ == "__main__":
    main()
