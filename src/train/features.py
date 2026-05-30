from typing import Any

import pandas as pd

from src.features.pipeline import build_features


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    records: list[dict[str, Any]] = df.to_dict(orient="records")
    feature_rows = [build_features(record) for record in records]
    matrix = pd.DataFrame(feature_rows).fillna(0.0)
    feature_names = list(matrix.columns)
    return matrix, feature_names
