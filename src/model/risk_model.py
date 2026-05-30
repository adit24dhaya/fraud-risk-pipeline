import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from xgboost import XGBClassifier

from src.explain.types import FeatureContribution
from src.explain.tree_shap import top_tree_shap_features
from src.features.ieee import build_serving_frame, load_feature_names
from src.features.pipeline import build_features


Decision = Literal["approve", "flag_for_review"]


@dataclass(frozen=True)
class RiskPrediction:
    probability: float
    decision: Decision
    threshold: float
    top_features: list[FeatureContribution]


class RiskModel:
    def __init__(
        self,
        threshold: float = 0.42,
        model: XGBClassifier | None = None,
        feature_names: list[str] | None = None,
    ) -> None:
        self.threshold = threshold
        self.model = model
        self.feature_names = feature_names or []

    @classmethod
    def load_default(cls) -> "RiskModel":
        model_path = Path(
            os.getenv("MODEL_ARTIFACT_PATH", "artifacts/xgboost_model.json")
        )
        feature_path = Path(
            os.getenv("FEATURE_LIST_PATH", "artifacts/feature_list.json")
        )
        threshold = _load_threshold(Path("artifacts/threshold.json"))
        threshold = float(os.getenv("RISK_THRESHOLD", str(threshold)))

        if not model_path.exists() or not feature_path.exists():
            return cls(threshold=threshold)

        model = XGBClassifier()
        model.load_model(model_path)
        return cls(
            threshold=threshold,
            model=model,
            feature_names=load_feature_names(feature_path),
        )

    def predict(self, transaction: dict[str, object]) -> RiskPrediction:
        if self.model is None:
            return self._predict_with_heuristic(transaction)

        frame = build_serving_frame(transaction, self.feature_names)
        probability = round(float(self.model.predict_proba(frame)[0, 1]), 6)
        contributions = top_tree_shap_features(
            model=self.model,
            features=frame,
            feature_names=self.feature_names,
        )
        decision: Decision = (
            "flag_for_review" if probability >= self.threshold else "approve"
        )
        return RiskPrediction(
            probability=probability,
            decision=decision,
            threshold=self.threshold,
            top_features=contributions[:5],
        )

    def _predict_with_heuristic(self, transaction: dict[str, object]) -> RiskPrediction:
        features = build_features(transaction)
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
            for name, value in sorted(
                weighted, key=lambda item: abs(item[1]), reverse=True
            )
            if abs(value) > 0.0
        ]


def _load_threshold(path: Path) -> float:
    if not path.exists():
        return 0.42
    try:
        return float(json.loads(path.read_text(encoding="utf-8"))["threshold"])
    except (KeyError, TypeError, ValueError):
        return 0.42
