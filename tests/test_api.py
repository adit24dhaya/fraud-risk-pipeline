from fastapi.testclient import TestClient

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
    assert payload["threshold"] == 0.42
    assert payload["top_features"]
    assert payload["analyst_summary"]
