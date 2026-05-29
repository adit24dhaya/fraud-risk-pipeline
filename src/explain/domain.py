from src.explain.types import DomainConfig


FRAUD_DOMAIN = DomainConfig(
    name="fraud",
    signal_label="risk signals",
    reviewer_role="fraud analyst",
    positive_decision_phrase="Flagged for review",
    negative_decision_phrase="Not flagged",
    guardrails=(
        "Use analyst framing.",
        "Do not claim the transaction is definitively fraudulent.",
    ),
)

HEALTHCARE_DOMAIN = DomainConfig(
    name="healthcare",
    signal_label="clinical risk factors",
    reviewer_role="clinical reviewer",
    positive_decision_phrase="Elevated risk for review",
    negative_decision_phrase="No elevated risk flag",
    guardrails=(
        "Use cautious clinical framing.",
        "State that this is not medical advice.",
    ),
)
