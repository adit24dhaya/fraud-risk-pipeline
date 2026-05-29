from math import log1p
from typing import Any


def build_features(transaction: dict[str, Any]) -> dict[str, float]:
    amount = float(transaction.get("amount", 0.0) or 0.0)
    hour = int(transaction.get("hour", 12) or 12)
    merchant = str(transaction.get("merchant", "")).lower()
    country = str(transaction.get("country", "US")).upper()

    return {
        "amount": amount,
        "amount_log": log1p(max(amount, 0.0)),
        "night_transaction": float(hour >= 22 or hour <= 5),
        "new_merchant_hint": float("new" in merchant),
        "cross_border_hint": float(country != "US"),
    }
