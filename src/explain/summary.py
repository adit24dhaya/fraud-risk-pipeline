from src.explain.types import DomainConfig, FeatureContribution


def explain(
    prediction: float,
    shap_features: list[FeatureContribution],
    domain: DomainConfig,
) -> str:
    """Return a plain-English, auditable summary for a human reviewer."""
    decision_phrase = (
        domain.positive_decision_phrase
        if prediction >= 0.5
        else domain.negative_decision_phrase
    )
    if not shap_features:
        return (
            f"{decision_phrase}: model score is {prediction:.0%}. "
            f"No dominant {domain.signal_label} were available."
        )

    increasing = [
        item.feature for item in shap_features if item.direction == "increases_risk"
    ]
    decreasing = [
        item.feature for item in shap_features if item.direction == "decreases_risk"
    ]

    parts = [
        f"{decision_phrase}: model score is {prediction:.0%}.",
    ]
    if increasing:
        parts.append(
            f"Main {domain.signal_label} increasing risk: {', '.join(increasing[:3])}."
        )
    if decreasing:
        parts.append(f"Offsetting signals: {', '.join(decreasing[:2])}.")
    if domain.guardrails:
        parts.append(domain.guardrails[-1])
    return " ".join(parts)
