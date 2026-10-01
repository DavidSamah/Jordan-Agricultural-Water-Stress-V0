from pathlib import Path

import pandas as pd


SRC = Path(
    "v1/data/processed_v1/"
    "water_vegetation_state_dekadal.csv"
)

OUT = Path(
    "v1/data/processed_v1/"
    "forecast_dataset_dekadal.csv"
)


df = pd.read_csv(SRC)

df = (
    df
    .sort_values(
        [
            "year",
            "month",
            "dekad"
        ]
    )
    .reset_index(drop=True)
)


# ------------------------------------------------------------
# FUTURE VEGETATION TARGET
# ------------------------------------------------------------
#
# Predictor row:
#
#     information available at t
#
# Target:
#
#     NDVI observed at t+1
#
# shift(-1) means:
#
# current row receives next row's NDVI.
# ------------------------------------------------------------

df[
    "target_ndvi_t_plus_1"
] = (
    df[
        "ndvi_weighted"
    ]
    .shift(-1)
)


df[
    "target_has_observation_t_plus_1"
] = (
    df[
        "has_ndvi_observation"
    ]
    .shift(-1)
    .fillna(False)
    .astype(bool)
)


# ------------------------------------------------------------
# CURRENT VEGETATION STATE
# ------------------------------------------------------------
#
# Current NDVI can later be tested as a predictor,
# but must remain clearly distinct from future NDVI.
# ------------------------------------------------------------

df[
    "ndvi_t"
] = df[
    "ndvi_weighted"
]


# ------------------------------------------------------------
# CHANGE TARGET
# ------------------------------------------------------------
#
# This measures deterioration/improvement between observed
# vegetation state at t and t+1.
#
# Only meaningful where both observations exist.
# ------------------------------------------------------------

df[
    "target_ndvi_change_t_plus_1"
] = (
    df[
        "target_ndvi_t_plus_1"
    ]
    -
    df[
        "ndvi_t"
    ]
)


# ------------------------------------------------------------
# VALID TARGET FLAG
# ------------------------------------------------------------

df[
    "valid_future_ndvi_target"
] = (
    df[
        "target_ndvi_t_plus_1"
    ]
    .notna()
)


print(
    "Total rows:",
    len(df)
)

print(
    "Future NDVI targets available:",
    int(
        df[
            "valid_future_ndvi_target"
        ].sum()
    )
)

print(
    "Future targets missing:",
    int(
        (
            ~df[
                "valid_future_ndvi_target"
            ]
        ).sum()
    )
)


# ------------------------------------------------------------
# IMPORTANT:
# NO ROWS ARE DROPPED HERE.
#
# Dataset construction and model selection remain separate.
# ------------------------------------------------------------

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUT,
    index=False
)


print(
    "\nSaved:",
    OUT
)

print(
    "\nPASS: leakage-aware t → t+1 "
    "target constructed"
)
