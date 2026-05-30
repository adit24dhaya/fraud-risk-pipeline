from sklearn.metrics import average_precision_score, precision_score, recall_score


def evaluate_binary_classifier(
    y_true: list[int],
    probabilities: list[float],
    threshold: float,
) -> dict[str, float]:
    predictions = [int(prob >= threshold) for prob in probabilities]
    return {
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
    }
