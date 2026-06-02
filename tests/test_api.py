from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from src.api.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_contract() -> None:
    response = client.post(
        "/predict",
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
    assert payload["threshold"] == 0.722727
    assert payload["top_features"]
    assert payload["analyst_summary"]


def test_predict_requires_api_key_when_configured(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret")

    response = client.post(
        "/predict",
        json={"transaction": {"TransactionAmt": 250.0, "hour": 23}},
    )

    assert response.status_code == 401


def test_predict_accepts_valid_api_key(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret")

    response = client.post(
        "/predict",
        headers={"X-API-Key": "test-secret"},
        json={"transaction": {"TransactionAmt": 250.0, "hour": 23}},
    )

    assert response.status_code == 200
