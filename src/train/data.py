from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "transaction_id",
    "event_time",
    "amount",
    "merchant",
    "country",
    "hour",
    "is_fraud",
}


def load_transactions(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Training data missing columns: {sorted(missing)}")

    df = df.copy()
    df["event_time"] = pd.to_datetime(df["event_time"], utc=True)
    df["is_fraud"] = df["is_fraud"].astype(int)
    return df.sort_values("event_time").reset_index(drop=True)
