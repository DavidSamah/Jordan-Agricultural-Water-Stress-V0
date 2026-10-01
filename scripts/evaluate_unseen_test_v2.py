from pathlib import Path
import json
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import (
    RandomForestRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)


DATA = Path(
    "v1/data/processed_v2/"
    "forecast_dataset_split.csv"
)

SELECTION = Path(
    "v1/results/models_v2/"
    "selected_models_v2.json"
)

OUT = Path(
    "v1/results/final_v2"
)

OUT.mkdir(
    parents=True,
    exist_ok=True
)


TARGET = "target_ndvi_t_plus_1"


def make_model(name):

    if name == "ridge":

        return Pipeline([
            (
                "scale",
                StandardScaler()
            ),
            (
                "model",
                Ridge(alpha=1.0)
            ),
        ])


    if name == "random_forest":

        return (
            RandomForestRegressor(
                n_estimators=500,
                max_depth=8,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            )
        )


    if (
        name
        ==
        "hist_gradient_boosting"
    ):

        return (
            HistGradientBoostingRegressor(
                max_iter=300,
                learning_rate=0.05,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=42,
            )
        )


    raise ValueError(
        f"Unknown model: {name}"
    )


def metrics(y, p):

    y = np.asarray(y)
    p = np.asarray(p)

    error = p - y

    return {
        "n": len(y),

        "mae":
            mean_absolute_error(
                y,
                p
            ),

        "rmse":
            np.sqrt(
                mean_squared_error(
                    y,
                    p
                )
            ),

        "bias":
            float(
                np.mean(error)
            ),
    }


df = pd.read_csv(DATA)


with open(
    SELECTION,
    encoding="utf-8"
) as f:

    selected = json.load(f)


records = []

prediction_frames = []


for family, config in (
    selected.items()
):

    features = config[
        "features"
    ]

    model_name = config[
        "model"
    ]


    development = df[
        (
            df["split"].isin([
                "train",
                "validation"
            ])
        )
        &
        (
            df[
                "valid_primary_target"
            ]
        )
    ].copy()


    test = df[
        (df["split"] == "test")
        &
        (
            df[
                "valid_primary_target"
            ]
        )
    ].copy()


    development = (
        development.dropna(
            subset=
                features
                +
                [TARGET]
        )
    )


    test = (
        test.dropna(
            subset=
                features
                +
                [TARGET]
        )
    )


    model = make_model(
        model_name
    )


    model.fit(
        development[features],
        development[TARGET]
    )


    prediction = model.predict(
        test[features]
    )


    m = metrics(
        test[TARGET],
        prediction
    )


    records.append({
        "family": family,
        "model": model_name,
        **m,
    })


    pred = test[
        [
            "year",
            "month",
            "dekad",
            TARGET,
        ]
    ].copy()


    pred["prediction"] = (
        prediction
    )

    pred["error"] = (
        pred["prediction"]
        -
        pred[TARGET]
    )

    pred["family"] = family

    pred["model"] = model_name


    prediction_frames.append(
        pred
    )


metrics_df = pd.DataFrame(
    records
)


predictions = pd.concat(
    prediction_frames,
    ignore_index=True
)


metrics_df.to_csv(
    OUT
    / "unseen_2024_metrics.csv",
    index=False
)


predictions.to_csv(
    OUT
    / "unseen_2024_predictions.csv",
    index=False
)


print("=" * 72)
print("UNSEEN 2024 TEST")
print("=" * 72)

print()

print(
    metrics_df.to_string(
        index=False
    )
)

print()

print(
    "PASS: FINAL TEST COMPLETE"
)
