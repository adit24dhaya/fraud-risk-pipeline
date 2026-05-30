from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MonitorConfig:
    reference_path: Path = Path("data/monitoring_reference.csv")
    current_path: Path = Path("data/monitoring_current.csv")
    output_html: Path = Path("docs/media/drift_report.html")
    output_json: Path = Path("docs/media/drift_summary.json")
