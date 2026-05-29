import os
from dataclasses import dataclass
from typing import Literal

from src.explain.types import FeatureContribution


Decision = Literal["approve", "flag_for_review"]


@dataclass(frozen=True)
class RiskPrediction:
    probability: float
    decision: Decision
    threshold: float
    top_features: list[FeatureContribution]


class RiskModel:
    def __init__(self, threshold: float = 0.42) -> None:
        self.threshold = threshold

    @classmethod
    def load_default(cls) -> "RiskModel":
        threshold = float(os.getenv("RISK_THRESHOLD", "0.42"))
        return cls(threshold=threshold)

    def predict(self, features: dict[str, float]) -> RiskPrediction:
        probability = self._heuristic_probability(features)
        contributions = self._heuristic_contributions(features)
        decision: Decision = (
            "flag_for_review" if probability >= self.threshold else "approve"
        )
        return RiskPrediction(
            probability=probability,
            decision=decision,
            threshold=self.threshold,
            top_features=contributions[:5],
        )

    def _heuristic_probability(self, features: dict[str, float]) -> float:
        score = 0.08
        score += min(features.get("amount_log", 0.0) / 12.0, 0.35)
        score += 0.18 * features.get("night_transaction", 0.0)
        score += 0.16 * features.get("new_merchant_hint", 0.0)
        score += 0.14 * features.get("cross_border_hint", 0.0)
        return round(min(max(score, 0.01), 0.99), 4)

    def _heuristic_contributions(
        self, features: dict[str, float]
    ) -> list[FeatureContribution]:
        weighted = [
            ("amount_log", features.get("amount_log", 0.0) / 12.0),
            ("night_transaction", 0.18 * features.get("night_transaction", 0.0)),
            ("new_merchant_hint", 0.16 * features.get("new_merchant_hint", 0.0)),
            ("cross_border_hint", 0.14 * features.get("cross_border_hint", 0.0)),
        ]
        return [
            FeatureContribution(
                feature=name,
                shap_value=round(value, 4),
                direction="increases_risk" if value >= 0 else "decreases_risk",
            )
            for name, value in sorted(weighted, key=lambda item: abs(item[1]), reverse=True)
            if abs(value) > 0.0
        ]
