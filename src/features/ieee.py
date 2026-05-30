import json
from math import log1p
from pathlib import Path
from typing import Any

import pandas as pd


COMMON_CATEGORY_CODES = {
    "ProductCD": {"c": 0.0, "h": 1.0, "r": 2.0, "s": 3.0, "w": 4.0},
    "card4": {
        "american express": 0.0,
        "discover": 1.0,
        "mastercard": 2.0,
        "visa": 3.0,
    },
    "card6": {"charge card": 0.0, "credit": 1.0, "debit": 2.0},
    "DeviceType": {"desktop": 0.0, "mobile": 1.0},
}


def load_feature_names(path: Path) -> list[str]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_serving_frame(
    transaction: dict[str, Any],
    feature_names: list[str],
) -> pd.DataFrame:
    row = {feature: 0.0 for feature in feature_names}

    for feature in feature_names:
        value = _lookup_feature_value(transaction, feature)
        if value is not None:
            row[feature] = value

    amount = _lookup_numeric(transaction, "TransactionAmt", "amount")
    if amount is not None:
        _set_if_expected(row, "TransactionAmt", amount)
        _set_if_expected(row, "amount_log", log1p(max(amount, 0.0)))

    transaction_dt = _lookup_numeric(transaction, "TransactionDT")
    if transaction_dt is not None:
        _set_if_expected(row, "transaction_day", transaction_dt // (60 * 60 * 24))
        _set_if_expected(row, "transaction_hour", (transaction_dt // (60 * 60)) % 24)

    hour = _lookup_numeric(transaction, "transaction_hour", "hour")
    if hour is not None:
        _set_if_expected(row, "transaction_hour", hour)

    return pd.DataFrame([row], columns=feature_names, dtype="float32")


def _lookup_feature_value(transaction: dict[str, Any], feature: str) -> float | None:
    if feature in transaction:
        return _coerce_feature(feature, transaction[feature])
    return _coerce_feature(feature, _alias_value(transaction, feature))


def _alias_value(transaction: dict[str, Any], feature: str) -> Any:
    aliases = {
        "TransactionAmt": "amount",
        "transaction_hour": "hour",
    }
    alias = aliases.get(feature)
    return transaction.get(alias) if alias else None


def _lookup_numeric(transaction: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key not in transaction:
            continue
        value = _coerce_float(transaction[key])
        if value is not None:
            return value
    return None


def _coerce_feature(feature: str, value: Any) -> float | None:
    numeric = _coerce_float(value)
    if numeric is not None:
        return numeric

    category_map = COMMON_CATEGORY_CODES.get(feature)
    if category_map is None:
        return None
    return category_map.get(str(value).lower())


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _set_if_expected(row: dict[str, float], feature: str, value: float) -> None:
    if feature in row:
        row[feature] = float(value)
