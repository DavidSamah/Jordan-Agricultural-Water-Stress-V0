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


INPUT = Path(
    "v1/data/processed_v2/"
    "forecast_dataset_split.csv"
)

OUT = Path(
    "v1/results/models_v2"
)

OUT.mkdir(
    parents=True,
    exist_ok=True
)


TARGET = "target_ndvi_t_plus_1"


HYDRO = [
    "precipitation_mean_mm",
    "soil_moisture_0_7cm_mean",
    "soil_moisture_7_28cm_mean",
    "soil_moisture_28_100cm_mean",
    "temperature_2m_mean_c",
    "agricultural_aeti_weighted_mm",
    "ret_mean_mm_dekad",
    "water_balance_ret_minus_rain",
    "water_balance_aeti_minus_rain",
    "aeti_ret_ratio",
    "rainfall_sum_3dekad",
    "rainfall_sum_6dekad",
    "soil_moisture_0_7cm_mean_3dekad",
    "aeti_mean_3dekad",
    "ret_mean_3dekad",
    "season_sin",
    "season_cos",
]


STATE = HYDRO + [
    "ndvi_t",
    "ndvi_lag_1",
    "ndvi_lag_2",
    "ndvi_lag_3",
]


def make_models():

    return {

        "ridge": Pipeline([
            (
                "scale",
                StandardScaler()
            ),
            (
                "model",
                Ridge(alpha=1.0)
            ),
        ]),

        "random_forest":
            RandomForestRegressor(
                n_estimators=500,
                max_depth=8,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            ),

        "hist_gradient_boosting":
            HistGradientBoostingRegressor(
                max_iter=300,
                learning_rate=0.05,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=42,
            ),
    }


def calculate_metrics(
    y_true,
    y_pred
):

    error = (
        np.asarray(y_pred)
        -
        np.asarray(y_true)
    )

    return {
        "n": len(y_true),

        "mae":
            mean_absolute_error(
                y_true,
                y_pred
            ),

        "rmse":
            np.sqrt(
                mean_squared_error(
                    y_true,
                    y_pred
                )
            ),

        "bias":
            float(
                np.mean(error)
            ),
    }


df = pd.read_csv(INPUT)


results = []

selection = {}


for family, features in [
    (
        "hydro_climate",
        HYDRO
    ),
    (
        "state_aware",
        STATE
    ),
]:

    train = df[
        (df["split"] == "train")
        &
        (
            df[
                "valid_primary_target"
            ]
        )
    ].copy()


    validation = df[
        (df["split"] == "validation")
        &
        (
            df[
                "valid_primary_target"
            ]
        )
    ].copy()


    train = train.dropna(
        subset=features + [TARGET]
    )

    validation = validation.dropna(
        subset=features + [TARGET]
    )


    print()
    print("=" * 72)
    print(family.upper())
    print("=" * 72)

    print(
        "Train:",
        len(train)
    )

    print(
        "Validation:",
        len(validation)
    )


    if len(train) == 0:
        raise RuntimeError(
            f"No training rows for {family}"
        )


    if len(validation) == 0:
        raise RuntimeError(
            f"No validation rows for {family}"
        )


    model_results = []


    for model_name, model in (
        make_models().items()
    ):

        model.fit(
            train[features],
            train[TARGET]
        )


        prediction = model.predict(
            validation[features]
        )


        m = calculate_metrics(
            validation[TARGET],
            prediction
        )


        record = {
            "family": family,
            "model": model_name,
            **m,
        }


        results.append(record)
        model_results.append(record)


        print()
        print(
            model_name,
            m
        )


    best = min(
        model_results,
        key=lambda x: x["rmse"]
    )


    selection[family] = {
        "model":
            best["model"],

        "validation_mae":
            best["mae"],

        "validation_rmse":
            best["rmse"],

        "features":
            features,
    }


metrics = pd.DataFrame(results)


metrics.to_csv(
    OUT
    / "candidate_validation_metrics.csv",
    index=False
)


with open(
    OUT
    / "selected_models_v2.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        selection,
        f,
        indent=2
    )


print()
print("=" * 72)
print("VALIDATION-ONLY MODEL SELECTION")
print("=" * 72)

print(
    metrics.to_string(
        index=False
    )
)

print()

print(
    json.dumps(
        selection,
        indent=2
    )
)

print()
print(
    "2024 TEST DATA NOT USED"
)
