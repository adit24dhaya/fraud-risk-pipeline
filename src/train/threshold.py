from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdResult:
    threshold: float
    expected_cost: float
    false_positive_cost: float
    false_negative_cost: float


def choose_cost_based_threshold(
    y_true: list[int],
    probabilities: list[float],
    false_positive_cost: float,
    false_negative_cost: float,
) -> ThresholdResult:
    if len(y_true) != len(probabilities):
        raise ValueError("y_true and probabilities must have the same length")
    if not y_true:
        raise ValueError("Cannot choose a threshold without labels")

    candidates = sorted({0.01, 0.99, *[round(p, 4) for p in probabilities]})
    best: ThresholdResult | None = None
    for threshold in candidates:
        predicted = [int(prob >= threshold) for prob in probabilities]
        false_positives = sum(
            1 for y, pred in zip(y_true, predicted) if y == 0 and pred == 1
        )
        false_negatives = sum(
            1 for y, pred in zip(y_true, predicted) if y == 1 and pred == 0
        )
        expected_cost = (
            false_positives * false_positive_cost
            + false_negatives * false_negative_cost
        )
        result = ThresholdResult(
            threshold=threshold,
            expected_cost=expected_cost,
            false_positive_cost=false_positive_cost,
            false_negative_cost=false_negative_cost,
        )
        if best is None or result.expected_cost < best.expected_cost:
            best = result

    if best is None:
        raise RuntimeError("Threshold search failed")
    return best
