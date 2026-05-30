from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingConfig:
    data_path: Path = Path("data/sample.csv")
    artifact_dir: Path = Path("artifacts")
    timestamp_column: str = "event_time"
    target_column: str = "is_fraud"
    test_fraction: float = 0.33
    false_positive_cost: float = 1.0
    false_negative_cost: float = 8.0
    experiment_name: str = "fraud-risk-baseline"
    random_state: int = 42
