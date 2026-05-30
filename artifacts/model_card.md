# Fraud Risk Baseline Model

## Intended Use
Transaction-risk screening for analyst review. The model does not make final fraud determinations.

## Data Note
These metrics are from the committed sample scaffold dataset. Replace with IEEE-CIS or ULB data before treating scores as meaningful.

## Headline Metrics
- PR-AUC: 1.0000
- Precision: 1.0000
- Recall: 1.0000

## Threshold
Decision threshold: 0.2103

Threshold is selected by expected cost, weighing missed fraud higher than false positives.

## Features
- amount
- amount_log
- night_transaction
- new_merchant_hint
- cross_border_hint
