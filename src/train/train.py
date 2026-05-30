import os

import mlflow
import mlflow.xgboost
from xgboost import XGBClassifier

from src.train.artifacts import write_json, write_model_card
from src.train.config import TrainingConfig
from src.train.data import load_transactions
from src.train.features import build_feature_matrix
from src.train.metrics import evaluate_binary_classifier
from src.train.split import time_based_split
from src.train.threshold import choose_cost_based_threshold


def train(config: TrainingConfig) -> dict[str, float]:
    transactions = load_transactions(config.data_path)
    train_df, test_df = time_based_split(
        transactions,
        timestamp_column=config.timestamp_column,
        test_fraction=config.test_fraction,
    )
    x_train, feature_names = build_feature_matrix(train_df)
    x_test, _ = build_feature_matrix(test_df)
    y_train = train_df[config.target_column].tolist()
    y_test = test_df[config.target_column].tolist()

    positives = max(sum(y_train), 1)
    negatives = max(len(y_train) - sum(y_train), 1)
    scale_pos_weight = negatives / positives

    params = {
        "n_estimators": 80,
        "max_depth": 3,
        "learning_rate": 0.08,
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "scale_pos_weight": scale_pos_weight,
        "random_state": config.random_state,
        "n_jobs": 1,
    }
    model = XGBClassifier(**params)
    model.fit(x_train, y_train)

    probabilities = model.predict_proba(x_test)[:, 1].tolist()
    threshold_result = choose_cost_based_threshold(
        y_true=y_test,
        probabilities=probabilities,
        false_positive_cost=config.false_positive_cost,
        false_negative_cost=config.false_negative_cost,
    )
    metrics = evaluate_binary_classifier(
        y_true=y_test,
        probabilities=probabilities,
        threshold=threshold_result.threshold,
    )

    config.artifact_dir.mkdir(parents=True, exist_ok=True)
    metrics_payload = {
        **metrics,
        "threshold": threshold_result.threshold,
        "expected_cost": threshold_result.expected_cost,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
    }
    write_json(config.artifact_dir / "metrics.json", metrics_payload)
    write_json(config.artifact_dir / "feature_list.json", feature_names)
    write_json(config.artifact_dir / "threshold.json", threshold_result.__dict__)
    write_model_card(
        config.artifact_dir / "model_card.md",
        metrics=metrics,
        threshold=threshold_result.threshold,
        feature_names=feature_names,
    )

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "mlruns")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(config.experiment_name)
    with mlflow.start_run(run_name="xgboost-baseline"):
        mlflow.log_params(params)
        mlflow.log_metrics(metrics_payload)
        mlflow.log_artifact(str(config.artifact_dir / "metrics.json"))
        mlflow.log_artifact(str(config.artifact_dir / "feature_list.json"))
        mlflow.log_artifact(str(config.artifact_dir / "threshold.json"))
        mlflow.log_artifact(str(config.artifact_dir / "model_card.md"))
        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            input_example=x_test.head(1),
        )

    return metrics_payload


def main() -> None:
    metrics = train(TrainingConfig())
    print(
        "Training complete: "
        f"PR-AUC={metrics['pr_auc']:.4f}, "
        f"precision={metrics['precision']:.4f}, "
        f"recall={metrics['recall']:.4f}, "
        f"threshold={metrics['threshold']:.4f}"
    )


if __name__ == "__main__":
    main()
