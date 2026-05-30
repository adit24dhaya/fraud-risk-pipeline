import pandas as pd
from xgboost import DMatrix, XGBClassifier

from src.explain.types import FeatureContribution


def top_tree_shap_features(
    model: XGBClassifier,
    features: pd.DataFrame,
    feature_names: list[str],
    limit: int = 5,
) -> list[FeatureContribution]:
    booster = model.get_booster()
    contributions = booster.predict(
        DMatrix(features, feature_names=feature_names),
        pred_contribs=True,
    )[0]
    shap_values = contributions[:-1]
    ranked = sorted(
        zip(feature_names, shap_values, strict=True),
        key=lambda item: abs(float(item[1])),
        reverse=True,
    )
    return [
        FeatureContribution(
            feature=name,
            shap_value=round(float(value), 6),
            direction="increases_risk" if value >= 0 else "decreases_risk",
        )
        for name, value in ranked[:limit]
        if abs(float(value)) > 0.0
    ]
