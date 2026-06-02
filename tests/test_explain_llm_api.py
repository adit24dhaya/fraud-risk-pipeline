import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main
from src.api.main import app
from src.explain import llm as llm_module

client = TestClient(app)


def test_explain_llm_requires_hf_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HF_API_TOKEN", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("HF_API_TOKEN", "")

    response = client.post(
        "/explain/llm",
        json={
            "transaction": {
                "amount": 250.0,
                "merchant": "new_electronics",
                "country": "US",
                "hour": 23,
            }
        },
    )

    assert response.status_code == 503
    assert "HF_API_TOKEN" in response.json()["detail"]


def test_explain_llm_requires_api_key_before_hf_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_KEY", "test-secret")
    monkeypatch.delenv("HF_API_TOKEN", raising=False)

    response = client.post(
        "/explain/llm",
        json={"transaction": {"TransactionAmt": 250.0, "hour": 23}},
    )

    assert response.status_code == 401


def test_explain_llm_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("HF_API_TOKEN", "hf_test")
    monkeypatch.setenv("HF_MODEL_ID", "test-model")

    def fake_generate(
        prompt: str,
        settings: llm_module.HfLlmSettings,
        *,
        client=None,
    ) -> str:
        assert "fraud analyst" in prompt
        return "LLM: flagged for manual review based on amount and timing."

    monkeypatch.setattr(api_main, "generate_hf_summary", fake_generate)

    response = client.post(
        "/explain/llm",
        json={
            "transaction": {
                "amount": 250.0,
                "merchant": "new_electronics",
                "country": "US",
                "hour": 23,
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert 0.0 <= payload["fraud_probability"] <= 1.0
    assert payload["decision"] in {"approve", "flag_for_review"}
    assert payload["template_summary"]
    assert payload["llm_summary"].startswith("LLM:")
    assert payload["model_id"] == "test-model"
    assert payload["top_features"]
