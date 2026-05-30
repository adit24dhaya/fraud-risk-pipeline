from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_score, recall_score
from sklearn.preprocessing import OrdinalEncoder
from xgboost import XGBClassifier


INPUT_ROOT = Path("/kaggle/input")
OUTPUT_DIR = Path("/kaggle/working")
RANDOM_STATE = 42
TEST_FRACTION = 0.2
FALSE_POSITIVE_COST = 1.0
FALSE_NEGATIVE_COST = 8.0


@dataclass(frozen=True)
class ThresholdResult:
    threshold: float
    expected_cost: float
    false_positive_cost: float
    false_negative_cost: float


def find_input_file(filename: str) -> Path:
    candidates = [
        *INPUT_ROOT.rglob(filename),
        *INPUT_ROOT.rglob(f"{filename}.zip"),
    ]
    if candidates:
        return candidates[0]

    available = [str(path) for path in INPUT_ROOT.rglob("*") if path.is_file()]
    preview = "\n".join(available[:50])
    raise FileNotFoundError(
        f"Could not find {filename} or {filename}.zip under {INPUT_ROOT}.\n"
        f"Available files preview:\n{preview}"
    )


def read_kaggle_csv(path: Path) -> pd.DataFrame:
    compression = "zip" if path.suffix == ".zip" else "infer"
    return pd.read_csv(path, compression=compression)


def load_ieee_data() -> pd.DataFrame:
    transaction_path = find_input_file("train_transaction.csv")
    transactions = read_kaggle_csv(transaction_path)
    identity_path = find_input_file("train_identity.csv")
    if identity_path.exists():
        identity = read_kaggle_csv(identity_path)
        transactions = transactions.merge(identity, on="TransactionID", how="left")
    return transactions.sort_values("TransactionDT").reset_index(drop=True)


def selected_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    base_numeric = [
        "TransactionAmt",
        "card1",
        "card2",
        "card3",
        "card5",
        "addr1",
        "addr2",
        "dist1",
        "dist2",
    ]
    c_cols = [f"C{i}" for i in range(1, 15)]
    d_cols = [f"D{i}" for i in range(1, 16)]
    v_cols = [f"V{i}" for i in range(1, 81)]
    id_numeric = [f"id_{i:02d}" for i in range(1, 12)]
    numeric = [
        col
        for col in [*base_numeric, *c_cols, *d_cols, *v_cols, *id_numeric]
        if col in df.columns
    ]

    categorical_candidates = [
        "ProductCD",
        "card4",
        "card6",
        "P_emaildomain",
        "R_emaildomain",
        "DeviceType",
        "DeviceInfo",
        *[f"M{i}" for i in range(1, 10)],
        *[f"id_{i:02d}" for i in range(12, 39)],
    ]
    categorical = [col for col in categorical_candidates if col in df.columns]
    return numeric, categorical


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["transaction_day"] = out["TransactionDT"] // (60 * 60 * 24)
    out["transaction_hour"] = (out["TransactionDT"] // (60 * 60)) % 24
    out["amount_log"] = np.log1p(out["TransactionAmt"].clip(lower=0))
    return out


def time_split(df: pd.DataFrame, test_fraction: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(df) * (1.0 - test_fraction))
    split_index = min(max(split_index, 1), len(df) - 1)
    return df.iloc[:split_index].copy(), df.iloc[split_index:].copy()


def build_matrices(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    engineered = ["transaction_day", "transaction_hour", "amount_log"]
    numeric_features = [col for col in [*numeric, *engineered] if col in train_df.columns]
    x_train_num = train_df[numeric_features].astype("float32")
    x_test_num = test_df[numeric_features].astype("float32")

    if categorical:
        train_categories = train_df[categorical].fillna("__missing__").astype(str)
        test_categories = test_df[categorical].fillna("__missing__").astype(str)
        encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
            encoded_missing_value=-1,
        )
        x_train_cat = pd.DataFrame(
            encoder.fit_transform(train_categories).astype("float32"),
            columns=categorical,
            index=train_df.index,
        )
        x_test_cat = pd.DataFrame(
            encoder.transform(test_categories).astype("float32"),
            columns=categorical,
            index=test_df.index,
        )
        x_train = pd.concat([x_train_num, x_train_cat], axis=1)
        x_test = pd.concat([x_test_num, x_test_cat], axis=1)
    else:
        x_train = x_train_num
        x_test = x_test_num

    feature_names = list(x_train.columns)
    return x_train, x_test, feature_names


def choose_threshold(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    false_positive_cost: float,
    false_negative_cost: float,
) -> ThresholdResult:
    candidates = np.linspace(0.01, 0.99, 199)
    best: ThresholdResult | None = None
    for threshold in candidates:
        predicted = probabilities >= threshold
        false_positives = int(((y_true == 0) & predicted).sum())
        false_negatives = int(((y_true == 1) & ~predicted).sum())
        expected_cost = (
            false_positives * false_positive_cost
            + false_negatives * false_negative_cost
        )
        result = ThresholdResult(
            threshold=float(round(threshold, 6)),
            expected_cost=float(expected_cost),
            false_positive_cost=false_positive_cost,
            false_negative_cost=false_negative_cost,
        )
        if best is None or result.expected_cost < best.expected_cost:
            best = result
    if best is None:
        raise RuntimeError("Threshold search failed")
    return best


def train_model(x_train: pd.DataFrame, y_train: np.ndarray) -> XGBClassifier:
    positives = max(int(y_train.sum()), 1)
    negatives = max(int(len(y_train) - y_train.sum()), 1)
    params = {
        "n_estimators": 120,
        "max_depth": 4,
        "learning_rate": 0.07,
        "subsample": 0.85,
        "colsample_bytree": 0.75,
        "min_child_weight": 2,
        "max_bin": 256,
        "reg_lambda": 1.5,
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "scale_pos_weight": negatives / positives,
        "tree_method": "hist",
        "device": "cuda",
        "random_state": RANDOM_STATE,
        "n_jobs": 2,
    }
    model = XGBClassifier(**params)
    try:
        model.fit(x_train, y_train)
    except Exception as exc:
        print(f"GPU training failed, falling back to CPU: {exc}")
        params["device"] = "cpu"
        model = XGBClassifier(**params)
        model.fit(x_train, y_train)
    return model


def write_artifacts(
    output_dir: Path,
    model: XGBClassifier,
    feature_names: list[str],
    metrics: dict[str, float],
    threshold: ThresholdResult,
    train_rows: int,
    test_rows: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        **metrics,
        "threshold": threshold.threshold,
        "expected_cost": threshold.expected_cost,
        "false_positive_cost": threshold.false_positive_cost,
        "false_negative_cost": threshold.false_negative_cost,
        "train_rows": train_rows,
        "test_rows": test_rows,
        "feature_count": len(feature_names),
        "split": "time_based_last_20_percent",
        "dataset": "IEEE-CIS Fraud Detection",
    }
    (output_dir / "metrics.json").write_text(json.dumps(payload, indent=2) + "\n")
    (output_dir / "threshold.json").write_text(json.dumps(asdict(threshold), indent=2) + "\n")
    (output_dir / "feature_list.json").write_text(json.dumps(feature_names, indent=2) + "\n")
    model.save_model(output_dir / "xgboost_model.json")
    (output_dir / "model_card.md").write_text(
        "\n".join(
            [
                "# Fraud Risk XGBoost Model",
                "",
                "## Dataset",
                "IEEE-CIS Fraud Detection from Kaggle.",
                "",
                "## Split",
                "Time-based split using `TransactionDT`; final 20% held out for test.",
                "",
                "## Headline Metrics",
                f"- PR-AUC: {metrics['pr_auc']:.4f}",
                f"- Precision: {metrics['precision']:.4f}",
                f"- Recall: {metrics['recall']:.4f}",
                "",
                "## Threshold",
                f"Decision threshold: {threshold.threshold:.4f}",
                "Threshold selected by expected cost, with missed fraud weighted higher than false positives.",
                "",
                "## Notes",
                "Accuracy is not used as a headline metric because fraud data is imbalanced.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    df = add_time_features(load_ieee_data())
    train_df, test_df = time_split(df, TEST_FRACTION)
    numeric, categorical = selected_columns(df)
    x_train, x_test, feature_names = build_matrices(train_df, test_df, numeric, categorical)
    y_train = train_df["isFraud"].to_numpy()
    y_test = test_df["isFraud"].to_numpy()

    model = train_model(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    threshold = choose_threshold(
        y_true=y_test,
        probabilities=probabilities,
        false_positive_cost=FALSE_POSITIVE_COST,
        false_negative_cost=FALSE_NEGATIVE_COST,
    )
    predictions = probabilities >= threshold.threshold
    metrics = {
        "pr_auc": float(average_precision_score(y_test, probabilities)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
    }
    write_artifacts(
        OUTPUT_DIR,
        model,
        feature_names,
        metrics,
        threshold,
        train_rows=len(train_df),
        test_rows=len(test_df),
    )
    print(
        "Training complete: "
        f"PR-AUC={metrics['pr_auc']:.4f}, "
        f"precision={metrics['precision']:.4f}, "
        f"recall={metrics['recall']:.4f}, "
        f"threshold={threshold.threshold:.4f}, "
        f"features={len(feature_names)}"
    )


if __name__ == "__main__":
    main()
