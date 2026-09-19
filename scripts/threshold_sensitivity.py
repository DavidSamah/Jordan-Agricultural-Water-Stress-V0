import pandas as pd

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score
)

df = pd.read_csv(
    "results/test_predictions_2024.csv"
)

y = df["target_stress_next_month"]

rows = []

for threshold in [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.60,
    0.70
]:

    pred = (
        df["rf_probability"]
        >= threshold
    ).astype(int)

    rows.append({
        "threshold": threshold,
        "accuracy":
            accuracy_score(y, pred),
        "precision":
            precision_score(
                y,
                pred,
                zero_division=0
            ),
        "recall":
            recall_score(
                y,
                pred,
                zero_division=0
            ),
        "f1":
            f1_score(
                y,
                pred,
                zero_division=0
            ),
        "predicted_stress":
            int(pred.sum())
    })

out = pd.DataFrame(rows)

print(out.to_string(index=False))

out.to_csv(
    "results/threshold_sensitivity.csv",
    index=False
)

print(
    "\nPASS: threshold sensitivity saved"
)
