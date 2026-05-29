from fastapi import FastAPI

from src.api.schemas import FeatureReason, PredictRequest, PredictResponse
from src.explain.domain import FRAUD_DOMAIN
from src.explain.summary import explain
from src.features.pipeline import build_features
from src.model.risk_model import RiskModel

app = FastAPI(
    title="Fraud Risk Pipeline",
    version="0.1.0",
    description="Real-time transaction risk scoring with explainability.",
)

model = RiskModel.load_default()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    features = build_features(payload.transaction)
    prediction = model.predict(features)
    summary = explain(
        prediction=prediction.probability,
        shap_features=prediction.top_features,
        domain=FRAUD_DOMAIN,
    )
    return PredictResponse(
        fraud_probability=prediction.probability,
        decision=prediction.decision,
        threshold=prediction.threshold,
        top_features=[
            FeatureReason(
                feature=item.feature,
                shap_value=item.shap_value,
                direction=item.direction,
            )
            for item in prediction.top_features
        ],
        analyst_summary=summary,
    )
