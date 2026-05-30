# Fraud Risk XGBoost Model

## Dataset
IEEE-CIS Fraud Detection from Kaggle.

## Split
Time-based split using `TransactionDT`; final 20% held out for test.

## Headline Metrics
- PR-AUC: 0.4402
- Precision: 0.3059
- Recall: 0.5413

## Threshold
Decision threshold: 0.7227
Threshold selected by expected cost, with missed fraud weighted higher than false positives.

## Notes
Accuracy is not used as a headline metric because fraud data is imbalanced.
