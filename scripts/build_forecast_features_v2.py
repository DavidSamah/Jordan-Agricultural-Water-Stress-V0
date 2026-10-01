from pathlib import Path

import numpy as np
import pandas as pd


INPUT = Path(
    "v1/data/processed_v2/"
    "predictor_alignment_dekadal.csv"
)

OUTPUT = Path(
    "v1/data/processed_v2/"
    "forecast_features_lagged.csv"
)


df = pd.read_csv(INPUT)

df = df.sort_values(
    [
        "year",
        "month",
        "dekad",
    ]
).reset_index(drop=True)


# ---------------------------------------------------------
# 1. Structural validation
# ---------------------------------------------------------

if len(df) != 252:
    raise RuntimeError(
        f"Expected 252 rows, "
        f"found {len(df)}"
    )


if df.duplicated(
    ["year", "month", "dekad"]
).any():

    raise RuntimeError(
        "Duplicate dekadal keys."
    )


# ---------------------------------------------------------
# 2. Current-state variables
# ---------------------------------------------------------

current_features = [
    "precipitation_mean_mm",
    "soil_moisture_0_7cm_mean",
    "soil_moisture_7_28cm_mean",
    "soil_moisture_28_100cm_mean",
    "temperature_2m_mean_c",
    "agricultural_aeti_weighted_mm",
    "ret_mean_mm_dekad",
]


for col in current_features:

    if col not in df.columns:
        raise RuntimeError(
            f"Required predictor missing: {col}"
        )


# ---------------------------------------------------------
# 3. Hydrological derived variables
# ---------------------------------------------------------

df["water_balance_ret_minus_rain"] = (
    df["ret_mean_mm_dekad"]
    -
    df["precipitation_mean_mm"]
)

df["water_balance_aeti_minus_rain"] = (
    df["agricultural_aeti_weighted_mm"]
    -
    df["precipitation_mean_mm"]
)


df["aeti_ret_ratio"] = np.where(
    df["ret_mean_mm_dekad"] != 0,

    (
        df[
            "agricultural_aeti_weighted_mm"
        ]
        /
        df["ret_mean_mm_dekad"]
    ),

    np.nan,
)


# ---------------------------------------------------------
# 4. Explicit current NDVI state
# ---------------------------------------------------------

df["ndvi_t"] = (
    df["ndvi_weighted"]
)


df[
    "has_ndvi_t"
] = (
    df["ndvi_t"].notna()
)


# ---------------------------------------------------------
# 5. Past NDVI lags
#
# IMPORTANT:
# shift(+1) = previous dekad.
# These contain only past information.
# ---------------------------------------------------------

for lag in [1, 2, 3]:

    df[
        f"ndvi_lag_{lag}"
    ] = (
        df["ndvi_weighted"]
        .shift(lag)
    )


# ---------------------------------------------------------
# 6. Hydrological lags
# ---------------------------------------------------------

lag_variables = [
    "precipitation_mean_mm",
    "soil_moisture_0_7cm_mean",
    "soil_moisture_7_28cm_mean",
    "soil_moisture_28_100cm_mean",
    "temperature_2m_mean_c",
    "agricultural_aeti_weighted_mm",
    "ret_mean_mm_dekad",
]


for variable in lag_variables:

    for lag in [1, 2, 3]:

        df[
            f"{variable}_lag_{lag}"
        ] = (
            df[variable]
            .shift(lag)
        )


# ---------------------------------------------------------
# 7. Rolling PAST climate/hydrology features
#
# Current row may be used because forecasting occurs
# after current-dekad observations become available.
# ---------------------------------------------------------

df[
    "rainfall_sum_3dekad"
] = (
    df[
        "precipitation_mean_mm"
    ]
    .rolling(
        window=3,
        min_periods=3
    )
    .sum()
)


df[
    "rainfall_sum_6dekad"
] = (
    df[
        "precipitation_mean_mm"
    ]
    .rolling(
        window=6,
        min_periods=6
    )
    .sum()
)


df[
    "soil_moisture_0_7cm_mean_3dekad"
] = (
    df[
        "soil_moisture_0_7cm_mean"
    ]
    .rolling(
        window=3,
        min_periods=3
    )
    .mean()
)


df[
    "aeti_mean_3dekad"
] = (
    df[
        "agricultural_aeti_weighted_mm"
    ]
    .rolling(
        window=3,
        min_periods=3
    )
    .mean()
)


df[
    "ret_mean_3dekad"
] = (
    df[
        "ret_mean_mm_dekad"
    ]
    .rolling(
        window=3,
        min_periods=3
    )
    .mean()
)


# ---------------------------------------------------------
# 8. Seasonal state
#
# No future information here:
# month/dekad are known calendar information.
# ---------------------------------------------------------

df[
    "season_step"
] = (
    (df["month"] - 1) * 3
    +
    (df["dekad"] - 1)
)


df[
    "season_sin"
] = np.sin(
    2
    * np.pi
    * df["season_step"]
    / 36
)


df[
    "season_cos"
] = np.cos(
    2
    * np.pi
    * df["season_step"]
    / 36
)


# ---------------------------------------------------------
# 9. NEXT-DEKAD TARGET
#
# shift(-1) intentionally accesses the next row.
# This is TARGET construction only.
#
# It must never become a model input.
# ---------------------------------------------------------

df[
    "target_ndvi_t_plus_1"
] = (
    df["ndvi_weighted"]
    .shift(-1)
)


df[
    "target_has_observation_t_plus_1"
] = (
    df[
        "target_ndvi_t_plus_1"
    ]
    .notna()
)


# ---------------------------------------------------------
# 10. NDVI change target
# ---------------------------------------------------------

df[
    "target_ndvi_change_t_plus_1"
] = (
    df[
        "target_ndvi_t_plus_1"
    ]
    -
    df["ndvi_t"]
)


# ---------------------------------------------------------
# 11. Primary target validity
#
# Primary next-dekad NDVI target only requires
# the future NDVI itself to be genuinely observed.
# ---------------------------------------------------------

df[
    "valid_primary_target"
] = (
    df[
        "target_has_observation_t_plus_1"
    ]
)


# Change target additionally requires NDVI_t.
df[
    "valid_change_target"
] = (
    df[
        "target_has_observation_t_plus_1"
    ]
    &
    df[
        "has_ndvi_t"
    ]
)


# ---------------------------------------------------------
# 12. Last row cannot have t+1
# ---------------------------------------------------------

assert pd.isna(
    df.iloc[-1][
        "target_ndvi_t_plus_1"
    ]
)


# ---------------------------------------------------------
# 13. Leakage audit
# ---------------------------------------------------------

future_columns = [
    c
    for c in df.columns
    if "t_plus_1" in c
]


print("=" * 72)
print("FORECAST FEATURE CONSTRUCTION V2")
print("=" * 72)

print()
print("Rows:", len(df))

print(
    "Observed current NDVI:",
    int(df["has_ndvi_t"].sum())
)

print(
    "Valid next-dekad NDVI targets:",
    int(
        df[
            "valid_primary_target"
        ].sum()
    )
)

print(
    "Valid NDVI-change targets:",
    int(
        df[
            "valid_change_target"
        ].sum()
    )
)


print()
print("Future/target columns:")
for c in future_columns:
    print(" -", c)


print()
print(
    "Target NDVI range:"
)

print(
    df.loc[
        df[
            "valid_primary_target"
        ],
        "target_ndvi_t_plus_1"
    ].agg(
        ["min", "max", "mean", "median"]
    )
)


# ---------------------------------------------------------
# 14. Save
# ---------------------------------------------------------

df.to_csv(
    OUTPUT,
    index=False
)


print()
print("Saved:")
print(OUTPUT)

print()
print(
    "PASS: lagged forecasting "
    "features created"
)
