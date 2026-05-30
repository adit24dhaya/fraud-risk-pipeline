from src.model.risk_model import RiskModel


def test_default_model_uses_committed_xgboost_artifact() -> None:
    model = RiskModel.load_default()

    prediction = model.predict(
        {
            "TransactionAmt": 420.0,
            "TransactionDT": 7_500_000,
            "ProductCD": "W",
            "card1": 12_345,
        }
    )

    assert prediction.threshold == 0.722727
    assert 0.0 <= prediction.probability <= 1.0
    assert prediction.top_features
