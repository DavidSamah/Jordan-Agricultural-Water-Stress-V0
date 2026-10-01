from pathlib import Path

import numpy as np
import pandas as pd


INPUT = Path(
    "v1/data/processed_v2/"
    "forecast_dataset_split.csv"
)

PREDICTIONS = Path(
    "v1/results/baselines_v2/"
    "baseline_predictions.csv"
)

METRICS = Path(
    "v1/results/baselines_v2/"
    "baseline_metrics.csv"
)

PREDICTIONS.parent.mkdir(
    parents=True,
    exist_ok=True
)


df = pd.read_csv(INPUT)


TARGET = (
    "target_ndvi_t_plus_1"
)


# ---------------------------------------------------------
# 1. Fit using TRAIN ONLY
# ---------------------------------------------------------

train = df[
    (df["split"] == "train")
    &
    (df["eligible_primary"])
].copy()


if train.empty:
    raise RuntimeError(
        "No eligible training targets."
    )


training_mean = (
    train[TARGET]
    .mean()
)

training_median = (
    train[TARGET]
    .median()
)


# ---------------------------------------------------------
# 2. Construct target seasonal position
#
# Current row predicts the NEXT dekad.
# Therefore climatology must correspond to t+1,
# not current t.
# ---------------------------------------------------------

def next_dekad_key(
    year,
    month,
    dekad,
):

    if dekad < 3:
        return (
            year,
            month,
            dekad + 1
        )

    if month < 12:
        return (
            year,
            month + 1,
            1
        )

    return (
        year + 1,
        1,
        1
    )


next_keys = df.apply(
    lambda r: next_dekad_key(
        int(r["year"]),
        int(r["month"]),
        int(r["dekad"]),
    ),
    axis=1,
)


df[
    "target_year"
] = [
    x[0]
    for x in next_keys
]

df[
    "target_month"
] = [
    x[1]
    for x in next_keys
]

df[
    "target_dekad"
] = [
    x[2]
    for x in next_keys
]


train_climatology = (
    train.assign(
        target_key=train.apply(
            lambda r: next_dekad_key(
                int(r["year"]),
                int(r["month"]),
                int(r["dekad"]),
            )[1:],
            axis=1,
        )
    )
    .groupby(
        "target_key"
    )[TARGET]
    .median()
)


# ---------------------------------------------------------
# 3. Predictions
# ---------------------------------------------------------

df[
    "baseline_training_mean"
] = training_mean


df[
    "baseline_training_median"
] = training_median


# Persistence can only be evaluated where NDVI_t exists.
df[
    "baseline_persistence"
] = df["ndvi_t"]


def climatology_prediction(row):

    key = (
        int(row["target_month"]),
        int(row["target_dekad"]),
    )

    return train_climatology.get(
        key,
        training_median
    )


df[
    "baseline_climatology"
] = df.apply(
    climatology_prediction,
    axis=1
)


# ---------------------------------------------------------
# 4. Metrics
# ---------------------------------------------------------

def metrics(
    y_true,
    y_pred
):

    mask = (
        y_true.notna()
        &
        y_pred.notna()
    )

    y = y_true[mask]
    p = y_pred[mask]

    if len(y) == 0:
        return {
            "n": 0,
            "mae": np.nan,
            "rmse": np.nan,
            "bias": np.nan,
        }

    error = p - y

    return {
        "n": len(y),

        "mae":
            np.mean(
                np.abs(error)
            ),

        "rmse":
            np.sqrt(
                np.mean(
                    error ** 2
                )
            ),

        "bias":
            np.mean(error),
    }


records = []


for split in [
    "train",
    "validation",
]:

    subset = df[
        (df["split"] == split)
        &
        (df["eligible_primary"])
    ]


    for baseline in [
        "baseline_training_mean",
        "baseline_training_median",
        "baseline_climatology",
        "baseline_persistence",
    ]:

        result = metrics(
            subset[TARGET],
            subset[baseline],
        )

        records.append({
            "split": split,
            "baseline": baseline,
            **result,
        })


metrics_df = pd.DataFrame(
    records
)


# ---------------------------------------------------------
# IMPORTANT:
# test metrics are intentionally not calculated yet.
# ---------------------------------------------------------

print("=" * 72)
print("BASELINES V2")
print("=" * 72)

print()
print("Training target mean:")
print(training_mean)

print()
print("Training target median:")
print(training_median)

print()
print(
    metrics_df.to_string(
        index=False
    )
)


df.to_csv(
    PREDICTIONS,
    index=False
)

metrics_df.to_csv(
    METRICS,
    index=False
)


print()
print("Saved predictions:")
print(PREDICTIONS)

print()
print("Saved metrics:")
print(METRICS)

print()
print(
    "TEST METRICS: intentionally hidden"
)

print()
print("=" * 72)
print("PASS: BASELINES ESTABLISHED")
print("=" * 72)
