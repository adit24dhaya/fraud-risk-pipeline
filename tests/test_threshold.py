from src.train.threshold import choose_cost_based_threshold


def test_choose_cost_based_threshold_prefers_catching_fraud() -> None:
    result = choose_cost_based_threshold(
        y_true=[0, 0, 1, 1],
        probabilities=[0.05, 0.30, 0.40, 0.90],
        false_positive_cost=1.0,
        false_negative_cost=8.0,
    )

    assert 0.0 < result.threshold < 1.0
    assert result.false_negative_cost > result.false_positive_cost
