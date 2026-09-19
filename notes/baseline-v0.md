# Step 48 — Baseline and Model V0

## Target

Predict vegetation-stress proxy at month t+1.

## Baseline A — Persistence

Predict next month's stress using the current month's
stress state.

## Baseline B — Seasonal climatology

Predict using the historical expected vegetation condition
for the same location and calendar month.

## ML Model V0

Random Forest

Predictors:
- precipitation
- soil moisture
- land-surface temperature
- evapotranspiration
- vegetation anomaly

Target:
future vegetation stress at t+1

## Evaluation

Primary:
- precision
- recall
- F1 score

Secondary:
- accuracy
- ROC-AUC

Stress-event recall is particularly important because
failure to detect genuine stress events reduces early-warning
usefulness.

## Temporal split

Train:
2018–2022

Validation:
2023

Test:
2024

Do not randomly shuffle observations across years.

## Scientific comparison

Persistence
vs
Seasonal climatology
vs
Random Forest

The ML model is useful only if it produces meaningful
improvement over simple baselines.
