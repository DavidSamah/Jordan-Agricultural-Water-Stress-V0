import json
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

PATH = "data/processed_v0/model_dataset_lagged.csv"

df = pd.read_csv(PATH, parse_dates=["time"])

FEATURES = [
    "precipitation_mm",
    "soil_moisture_m3_m3",
    "temperature_2m_c",
    "precipitation_mm_lag1",
    "soil_moisture_m3_m3_lag1",
    "temperature_2m_c_lag1",
    "month_sin",
    "month_cos"
]

TARGET = "target_stress_next_month"

train = df[df.time.dt.year <= 2022].copy()
val = df[df.time.dt.year == 2023].copy()
test = df[df.time.dt.year == 2024].copy()

X_train = train[FEATURES]
y_train = train[TARGET]

X_val = val[FEATURES]
y_val = val[TARGET]

X_test = test[FEATURES]
y_test = test[TARGET]

def metrics(y, pred, prob=None):
    out = {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(
            precision_score(y, pred, zero_division=0)
        ),
        "recall": float(
            recall_score(y, pred, zero_division=0)
        ),
        "f1": float(
            f1_score(y, pred, zero_division=0)
        ),
        "confusion_matrix":
            confusion_matrix(y, pred).tolist()
    }

    if prob is not None and len(set(y)) == 2:
        out["roc_auc"] = float(
            roc_auc_score(y, prob)
        )

    return out


# Baseline 1: persistence
val_persistence = val["current_stress"].astype(int)
test_persistence = test["current_stress"].astype(int)

# Baseline 2: seasonal climatology learned from training data only
monthly_rate = (
    train.groupby("month")[TARGET]
         .mean()
)

val_clim_prob = val["month"].map(monthly_rate).fillna(
    y_train.mean()
)

test_clim_prob = test["month"].map(monthly_rate).fillna(
    y_train.mean()
)

val_clim = (val_clim_prob >= 0.5).astype(int)
test_clim = (test_clim_prob >= 0.5).astype(int)

model = RandomForestClassifier(
    n_estimators=500,
    max_depth=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)

val_prob = model.predict_proba(X_val)[:, 1]
test_prob = model.predict_proba(X_test)[:, 1]

best_threshold = 0.5
best_f1 = -1

for i in range(10, 91):
    threshold = i / 100

    pred = (
        val_prob >= threshold
    ).astype(int)

    score = f1_score(
        y_val,
        pred,
        zero_division=0
    )

    if score > best_f1:
        best_f1 = score
        best_threshold = threshold

val_pred = (
    val_prob >= best_threshold
).astype(int)

test_pred = (
    test_prob >= best_threshold
).astype(int)

results = {
    "threshold_selected_on_validation":
        best_threshold,

    "validation": {
        "persistence":
            metrics(y_val, val_persistence),

        "climatology":
            metrics(
                y_val,
                val_clim,
                val_clim_prob
            ),

        "random_forest":
            metrics(
                y_val,
                val_pred,
                val_prob
            )
    },

    "test_2024": {
        "persistence":
            metrics(y_test, test_persistence),

        "climatology":
            metrics(
                y_test,
                test_clim,
                test_clim_prob
            ),

        "random_forest":
            metrics(
                y_test,
                test_pred,
                test_prob
            )
    }
}

with open(
    "results/metrics_v0.json",
    "w"
) as f:
    json.dump(results, f, indent=2)

joblib.dump(
    model,
    "models/random_forest_v0.joblib"
)

predictions = test[
    [
        "time",
        TARGET,
        "current_stress"
    ]
].copy()

predictions["rf_probability"] = test_prob
predictions["rf_prediction"] = test_pred
predictions["climatology_probability"] = test_clim_prob.values
predictions["climatology_prediction"] = test_clim.values

predictions.to_csv(
    "results/test_predictions_2024.csv",
    index=False
)

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance":
        model.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

importance.to_csv(
    "results/feature_importance.csv",
    index=False
)

print(json.dumps(results, indent=2))

print("\nFeature importance:")
print(importance)
