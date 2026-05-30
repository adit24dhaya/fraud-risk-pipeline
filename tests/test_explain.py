from src.explain.domain import FRAUD_DOMAIN, HEALTHCARE_DOMAIN
from src.explain.summary import explain
from src.explain.types import FeatureContribution


def test_explainer_uses_domain_framing() -> None:
    features = [
        FeatureContribution(
            feature="txn_velocity_1h",
            shap_value=0.31,
            direction="increases_risk",
        )
    ]

    fraud_summary = explain(0.83, features, FRAUD_DOMAIN, threshold=0.722727)
    healthcare_summary = explain(0.83, features, HEALTHCARE_DOMAIN, threshold=0.722727)

    assert "Flagged for review" in fraud_summary
    assert "risk signals" in fraud_summary
    assert "not medical advice" in healthcare_summary


def test_explainer_respects_cost_based_threshold() -> None:
    features = [
        FeatureContribution(
            feature="TransactionAmt",
            shap_value=0.2,
            direction="increases_risk",
        )
    ]
    threshold = 0.722727

    below = explain(0.60, features, FRAUD_DOMAIN, threshold=threshold)
    above = explain(0.80, features, FRAUD_DOMAIN, threshold=threshold)

    assert "Not flagged" in below
    assert "Flagged for review" in above
