import pandas as pd


def time_based_split(
    df: pd.DataFrame,
    timestamp_column: str,
    test_fraction: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1")
    if df.empty:
        raise ValueError("Cannot split an empty dataframe")

    ordered = df.sort_values(timestamp_column).reset_index(drop=True)
    split_index = max(1, int(len(ordered) * (1.0 - test_fraction)))
    split_index = min(split_index, len(ordered) - 1)
    return ordered.iloc[:split_index].copy(), ordered.iloc[split_index:].copy()
