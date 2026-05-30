from src.features.ieee import build_serving_frame


def test_build_serving_frame_maps_demo_aliases() -> None:
    feature_names = [
        "TransactionAmt",
        "amount_log",
        "transaction_hour",
        "ProductCD",
    ]

    frame = build_serving_frame(
        {
            "amount": 250.0,
            "hour": 23,
            "ProductCD": "W",
        },
        feature_names,
    )

    row = frame.iloc[0]
    assert row["TransactionAmt"] == 250.0
    assert row["amount_log"] > 0
    assert row["transaction_hour"] == 23.0
    assert row["ProductCD"] == 4.0
