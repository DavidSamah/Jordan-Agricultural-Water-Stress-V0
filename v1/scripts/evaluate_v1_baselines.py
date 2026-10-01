from pathlib import Path

import numpy as np
import pandas as pd


SRC = Path(
    "v1/data/processed_v1/"
    "forecast_dataset_frozen.csv"
)

OUT = Path(
    "v1/data/processed_v1/"
    "baseline_predictions.csv"
)


TARGET = (
    "target_ndvi_t_plus_1"
)


df = pd.read_csv(SRC)

df = (
    df
    .sort_values(
        ["year", "month", "dekad"]
    )
    .reset_index(drop=True)
)


# --------------------------------------------------
# HELPER METRICS
# --------------------------------------------------

def mae(y_true, y_pred):

    return float(
        np.mean(
            np.abs(
                y_true - y_pred
            )
        )
    )


def rmse(y_true, y_pred):

    return float(
        np.sqrt(
            np.mean(
                (
                    y_true - y_pred
                ) ** 2
            )
        )
    )


def correlation(y_true, y_pred):

    if len(y_true) < 2:
        return np.nan

    if (
        np.std(y_true) == 0
        or
        np.std(y_pred) == 0
    ):
        return np.nan

    return float(
        np.corrcoef(
            y_true,
            y_pred
        )[0, 1]
    )


# --------------------------------------------------
# BASELINE 1
# PERSISTENCE
# --------------------------------------------------
#
# Assume next-dekad vegetation condition
# is equal to current vegetation condition.
#
# NDVI(t+1) = NDVI(t)
#
# This is a strong baseline because vegetation
# usually changes gradually.
# --------------------------------------------------

df[
    "baseline_persistence"
] = df[
    "ndvi_t"
]


# --------------------------------------------------
# BASELINE 2
# TRAINING-SEASON CLIMATOLOGY
# --------------------------------------------------
#
# For each calendar month + dekad,
# estimate typical future NDVI using only
# training-period target values.
#
# Validation/test years do not contribute
# to climatology calculation.
# --------------------------------------------------

training = df[
    (
        df["split"] == "train"
    )
    &
    (
        df[TARGET]
        .notna()
    )
].copy()


climatology = (
    training
    .groupby(
        [
            "month",
            "dekad"
        ]
    )[TARGET]
    .mean()
    .rename(
        "baseline_climatology"
    )
    .reset_index()
)


df = df.merge(
    climatology,
    on=[
        "month",
        "dekad"
    ],
    how="left",
    validate="many_to_one"
)


# --------------------------------------------------
# BASELINE 3
# TRAINING GLOBAL MEAN
# --------------------------------------------------

training_mean = float(
    training[
        TARGET
    ].mean()
)

df[
    "baseline_training_mean"
] = training_mean


# --------------------------------------------------
# EVALUATE
# --------------------------------------------------

baseline_columns = [
    "baseline_persistence",
    "baseline_climatology",
    "baseline_training_mean",
]


results = []


for split in [
    "validation",
    "test",
]:

    subset = df[
        (
            df["split"] == split
        )
        &
        (
            df[TARGET]
            .notna()
        )
    ].copy()


    print()
    print("=" * 70)
    print(split.upper())
    print("Target rows:", len(subset))


    for baseline in baseline_columns:

        valid = subset[
            subset[baseline]
            .notna()
        ]

        if len(valid) == 0:

            print(
                baseline,
                "NO VALID ROWS"
            )

            continue


        y_true = (
            valid[
                TARGET
            ]
            .to_numpy(
                dtype=float
            )
        )

        y_pred = (
            valid[
                baseline
            ]
            .to_numpy(
                dtype=float
            )
        )


        metrics = {

            "split":
                split,

            "baseline":
                baseline,

            "n":
                len(valid),

            "mae":
                mae(
                    y_true,
                    y_pred
                ),

            "rmse":
                rmse(
                    y_true,
                    y_pred
                ),

            "correlation":
                correlation(
                    y_true,
                    y_pred
                ),
        }

        results.append(
            metrics
        )


        print()
        print(
            baseline
        )

        print(
            "N:",
            metrics["n"]
        )

        print(
            "MAE:",
            round(
                metrics["mae"],
                5
            )
        )

        print(
            "RMSE:",
            round(
                metrics["rmse"],
                5
            )
        )

        print(
            "Correlation:",
            (
                round(
                    metrics[
                        "correlation"
                    ],
                    5
                )
                if np.isfinite(
                    metrics[
                        "correlation"
                    ]
                )
                else "NA"
            )
        )


# --------------------------------------------------
# SAVE PREDICTIONS
# --------------------------------------------------

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUT,
    index=False
)


metrics_out = (
    OUT.parent
    /
    "baseline_metrics.csv"
)

pd.DataFrame(
    results
).to_csv(
    metrics_out,
    index=False
)


print()
print("=" * 70)

print(
    "Predictions saved:",
    OUT
)

print(
    "Metrics saved:",
    metrics_out
)

print(
    "\nPASS: temporal baselines evaluated"
)
