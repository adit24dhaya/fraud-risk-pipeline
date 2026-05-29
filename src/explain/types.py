from dataclasses import dataclass
from typing import Literal


RiskDirection = Literal["increases_risk", "decreases_risk"]


@dataclass(frozen=True)
class FeatureContribution:
    feature: str
    shap_value: float
    direction: RiskDirection


@dataclass(frozen=True)
class DomainConfig:
    name: str
    signal_label: str
    reviewer_role: str
    positive_decision_phrase: str
    negative_decision_phrase: str
    guardrails: tuple[str, ...] = ()
