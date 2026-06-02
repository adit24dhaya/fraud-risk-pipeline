import os
import secrets
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException

from src.api.schemas import (
    ExplainLlmRequest,
    ExplainLlmResponse,
    FeatureReason,
    PredictRequest,
    PredictResponse,
)
from src.explain.domain import FRAUD_DOMAIN
from src.explain.llm import (
    HfInferenceError,
    build_analyst_prompt,
    generate_hf_summary,
    load_hf_settings,
)
from src.explain.summary import explain
from src.model.risk_model import RiskModel

load_dotenv()

app = FastAPI(
    title="Fraud Risk Pipeline",
    version="0.1.0",
    description="Real-time transaction risk scoring with explainability.",
)

model = RiskModel.load_default()


def require_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    expected_key = os.getenv("API_KEY", "").strip()
    if not expected_key:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


REQUIRE_API_KEY = Depends(require_api_key)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse, dependencies=[REQUIRE_API_KEY])
def predict(payload: PredictRequest) -> PredictResponse:
    prediction = model.predict(payload.transaction)
    summary = explain(
        prediction=prediction.probability,
        shap_features=prediction.top_features,
        domain=FRAUD_DOMAIN,
        threshold=prediction.threshold,
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


@app.post("/explain/llm", response_model=ExplainLlmResponse, dependencies=[REQUIRE_API_KEY])
def explain_llm(payload: ExplainLlmRequest) -> ExplainLlmResponse:
    """On-demand LLM analyst summary via Hugging Face serverless inference."""
    prediction = model.predict(payload.transaction)
    template_summary = explain(
        prediction=prediction.probability,
        shap_features=prediction.top_features,
        domain=FRAUD_DOMAIN,
        threshold=prediction.threshold,
    )

    settings = load_hf_settings()
    if not settings.is_configured:
        raise HTTPException(
            status_code=503,
            detail="HF_API_TOKEN is not configured. Set it in the environment to use this route.",
        )

    prompt = build_analyst_prompt(
        prediction=prediction.probability,
        decision=prediction.decision,
        threshold=prediction.threshold,
        shap_features=prediction.top_features,
        domain=FRAUD_DOMAIN,
    )
    try:
        llm_summary = generate_hf_summary(prompt, settings)
    except HfInferenceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ExplainLlmResponse(
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
        template_summary=template_summary,
        llm_summary=llm_summary,
        model_id=settings.model_id,
    )
