from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# STEP 6
# Join dekadal water state with Sentinel-2 vegetation response.
# ============================================================

WATER = Path(
    "v1/data/processed_v1/"
    "water_state_dekadal.csv"
)

NDVI = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_dekadal.csv"
)

OUT = Path(
    "v1/data/processed_v1/"
    "water_vegetation_state_dekadal.csv"
)


# ------------------------------------------------------------
# 1. LOAD
# ------------------------------------------------------------

water = pd.read_csv(WATER)

ndvi = pd.read_csv(
    NDVI
)


print(
    "Water-state rows:",
    len(water)
)

print(
    "NDVI dekads:",
    len(ndvi)
)


# ------------------------------------------------------------
# 2. VALIDATE JOIN KEYS
# ------------------------------------------------------------

KEYS = [
    "year",
    "month",
    "dekad"
]


for name, df in [
    ("water", water),
    ("ndvi", ndvi),
]:

    missing = [
        col
        for col in KEYS
        if col not in df.columns
    ]

    if missing:

        raise RuntimeError(
            f"{name} missing join keys: "
            f"{missing}"
        )


    duplicates = (
        df[KEYS]
        .duplicated()
        .sum()
    )

    if duplicates:

        raise RuntimeError(
            f"{name} contains "
            f"{duplicates} duplicate dekads"
        )


# ------------------------------------------------------------
# 3. VERIFY EXPECTED WATER TIMELINE
# ------------------------------------------------------------

if len(water) != 252:

    print(
        "WARNING: expected 252 water-state "
        "dekads for 2018–2024, found:",
        len(water)
    )


# ------------------------------------------------------------
# 4. SELECT VEGETATION VARIABLES
# ------------------------------------------------------------

ndvi_columns = [
    "year",
    "month",
    "dekad",
    "ndvi_weighted",
    "ndvi_mean",
    "ndvi_median",
    "ndvi_min",
    "ndvi_max",
    "ndvi_std",
    "acquisition_count",
    "mean_coverage_fraction",
    "max_coverage_fraction",
    "mean_agricultural_pixels",
    "total_quality_weight",
]

missing_ndvi_columns = [
    col
    for col in ndvi_columns
    if col not in ndvi.columns
]

if missing_ndvi_columns:

    raise RuntimeError(
        "NDVI table missing columns: "
        f"{missing_ndvi_columns}"
    )


# ------------------------------------------------------------
# 5. LEFT JOIN
# ------------------------------------------------------------
#
# Water state is the temporal backbone.
#
# LEFT JOIN is deliberate:
#
# a missing Sentinel observation remains missing.
#
# We do NOT remove that dekad.
# We do NOT replace NDVI with zero.
# We do NOT interpolate here.
# ------------------------------------------------------------

merged = water.merge(
    ndvi[
        ndvi_columns
    ],
    on=KEYS,
    how="left",
    validate="one_to_one"
)


# ------------------------------------------------------------
# 6. VEGETATION OBSERVATION FLAG
# ------------------------------------------------------------

merged[
    "has_ndvi_observation"
] = (
    merged[
        "ndvi_weighted"
    ]
    .notna()
)


# ------------------------------------------------------------
# 7. TEMPORAL ORDER
# ------------------------------------------------------------

merged = (
    merged
    .sort_values(KEYS)
    .reset_index(drop=True)
)


# ------------------------------------------------------------
# 8. BUILD SEQUENTIAL DEKAD INDEX
# ------------------------------------------------------------

merged[
    "time_index"
] = np.arange(
    len(merged)
)


# ------------------------------------------------------------
# 9. VALIDATE MERGE
# ------------------------------------------------------------

if len(merged) != len(water):

    raise RuntimeError(
        "Join changed water-state row count"
    )


if merged[
    KEYS
].duplicated().any():

    raise RuntimeError(
        "Duplicate dekads after join"
    )


observed = int(
    merged[
        "has_ndvi_observation"
    ].sum()
)

missing = int(
    (
        ~merged[
            "has_ndvi_observation"
        ]
    ).sum()
)


print()
print(
    "Joined rows:",
    len(merged)
)

print(
    "Dekads with NDVI:",
    observed
)

print(
    "Dekads without NDVI:",
    missing
)

print(
    "Vegetation coverage:",
    round(
        observed
        /
        len(merged),
        4
    )
)


# ------------------------------------------------------------
# 10. CHECK PHYSICAL RANGE
# ------------------------------------------------------------

observed_ndvi = merged.loc[
    merged[
        "has_ndvi_observation"
    ],
    "ndvi_weighted"
]


if not observed_ndvi.between(
    -1,
    1
).all():

    raise RuntimeError(
        "Observed NDVI outside [-1, 1]"
    )


# ------------------------------------------------------------
# 11. SAVE
# ------------------------------------------------------------

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

merged.to_csv(
    OUT,
    index=False
)


print(
    "\nSaved:",
    OUT
)

print(
    "\nPASS: water-state and vegetation "
    "response joined without filling "
    "missing Sentinel observations"
)
