from typing import Any, Literal

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    transaction: dict[str, Any] = Field(..., description="Raw transaction payload")


class FeatureReason(BaseModel):
    feature: str
    shap_value: float
    direction: Literal["increases_risk", "decreases_risk"]


class PredictResponse(BaseModel):
    fraud_probability: float
    decision: Literal["approve", "flag_for_review"]
    threshold: float
    top_features: list[FeatureReason]
    analyst_summary: str
