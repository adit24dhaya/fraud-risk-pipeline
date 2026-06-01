import httpx
import pytest

from src.explain.domain import FRAUD_DOMAIN
from src.explain.llm import (
    HfInferenceError,
    HfLlmSettings,
    build_analyst_prompt,
    generate_hf_summary,
    _parse_hf_response,
)
from src.explain.types import FeatureContribution


def test_build_analyst_prompt_includes_guardrails_and_drivers() -> None:
    features = [
        FeatureContribution(
            feature="TransactionAmt",
            shap_value=0.31,
            direction="increases_risk",
        )
    ]
    prompt = build_analyst_prompt(
        prediction=0.83,
        decision="flag_for_review",
        threshold=0.722727,
        shap_features=features,
        domain=FRAUD_DOMAIN,
    )

    assert "fraud analyst" in prompt
    assert "TransactionAmt" in prompt
    assert "0.723" in prompt
    assert "definitively fraudulent" in prompt


def test_parse_hf_response_generated_text() -> None:
    assert _parse_hf_response([{"generated_text": "  Review note.  "}]) == "Review note."


def test_generate_hf_summary_requires_token() -> None:
    settings = HfLlmSettings(
        api_token="",
        model_id="test-model",
        timeout_seconds=5.0,
        max_new_tokens=64,
    )
    with pytest.raises(HfInferenceError, match="HF_API_TOKEN"):
        generate_hf_summary("prompt", settings)


def test_generate_hf_summary_uses_http_client() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "Authorization" in request.headers
        assert request.url.path.endswith("/models/test-model")
        return httpx.Response(
            200,
            json=[{"generated_text": "Elevated risk due to amount and hour."}],
        )

    settings = HfLlmSettings(
        api_token="hf_test",
        model_id="test-model",
        timeout_seconds=5.0,
        max_new_tokens=64,
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    summary = generate_hf_summary("prompt", settings, client=client)
    assert "Elevated risk" in summary
