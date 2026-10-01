from pathlib import Path

import numpy as np
import pandas as pd


SRC = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_observations.csv"
)

OUT = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_dekadal.csv"
)


# --------------------------------------------------
# LOAD
# --------------------------------------------------

df = pd.read_csv(
    SRC,
    parse_dates=["date"]
)

print(
    "Acquisition observations:",
    len(df)
)


# --------------------------------------------------
# BASIC VALIDATION
# --------------------------------------------------

required = [
    "date",
    "year",
    "month",
    "dekad",
    "coverage_fraction",
    "agricultural_pixels",
    "crop_equivalent_weight",
    "agricultural_ndvi_weighted",
]

missing = [
    col
    for col in required
    if col not in df.columns
]

if missing:
    raise RuntimeError(
        f"Missing columns: {missing}"
    )


if df["date"].duplicated().any():
    raise RuntimeError(
        "Duplicate acquisition dates detected"
    )


if not df[
    "agricultural_ndvi_weighted"
].between(-1, 1).all():

    raise RuntimeError(
        "NDVI outside physical range"
    )


# --------------------------------------------------
# QUALITY WEIGHT
# --------------------------------------------------

# Each acquisition already has a cropland-weighted NDVI.
#
# For dekadal aggregation, we now weight acquisition dates
# by the amount of valid cropland support.
#
# This means an observation supported by more valid cropland
# contributes more than a heavily cloud-obscured observation.

df[
    "temporal_quality_weight"
] = (
    df[
        "crop_equivalent_weight"
    ]
)


if (
    df[
        "temporal_quality_weight"
    ] <= 0
).any():

    raise RuntimeError(
        "Non-positive temporal quality weight"
    )


# --------------------------------------------------
# AGGREGATION FUNCTION
# --------------------------------------------------

def summarize(group):

    values = (
        group[
            "agricultural_ndvi_weighted"
        ]
        .to_numpy(
            dtype=float
        )
    )

    weights = (
        group[
            "temporal_quality_weight"
        ]
        .to_numpy(
            dtype=float
        )
    )

    weighted = float(
        np.average(
            values,
            weights=weights
        )
    )

    return pd.Series({

        "ndvi_weighted":
            weighted,

        "ndvi_mean":
            float(
                np.mean(values)
            ),

        "ndvi_median":
            float(
                np.median(values)
            ),

        "ndvi_min":
            float(
                np.min(values)
            ),

        "ndvi_max":
            float(
                np.max(values)
            ),

        "ndvi_std":
            (
                float(
                    np.std(
                        values,
                        ddof=1
                    )
                )
                if len(values) > 1
                else np.nan
            ),

        "acquisition_count":
            len(group),

        "mean_coverage_fraction":
            float(
                group[
                    "coverage_fraction"
                ].mean()
            ),

        "max_coverage_fraction":
            float(
                group[
                    "coverage_fraction"
                ].max()
            ),

        "mean_agricultural_pixels":
            float(
                group[
                    "agricultural_pixels"
                ].mean()
            ),

        "total_quality_weight":
            float(
                weights.sum()
            ),
    })


# --------------------------------------------------
# AGGREGATE TO DEKADS
# --------------------------------------------------

dekadal = (
    df.groupby(
        [
            "year",
            "month",
            "dekad"
        ],
        as_index=False
    )
    .apply(
        summarize,
        include_groups=False
    )
    .reset_index(drop=True)
)


# --------------------------------------------------
# CREATE DEKAD START DATE
# --------------------------------------------------

def dekad_start(row):

    if row["dekad"] == 1:
        day = 1

    elif row["dekad"] == 2:
        day = 11

    else:
        day = 21

    return pd.Timestamp(
        year=int(row["year"]),
        month=int(row["month"]),
        day=day
    )


dekadal["date"] = (
    dekadal.apply(
        dekad_start,
        axis=1
    )
)


# --------------------------------------------------
# ORDER COLUMNS
# --------------------------------------------------

dekadal = dekadal[
    [
        "date",
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
]


# --------------------------------------------------
# VALIDATE
# --------------------------------------------------

if dekadal[
    ["year", "month", "dekad"]
].duplicated().any():

    raise RuntimeError(
        "Duplicate dekads after aggregation"
    )


if not dekadal[
    "ndvi_weighted"
].between(-1, 1).all():

    raise RuntimeError(
        "Aggregated NDVI outside "
        "physical range"
    )


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

dekadal.to_csv(
    OUT,
    index=False
)


print(
    "\nDekads with NDVI:",
    len(dekadal)
)

print(
    "Missing from complete 252-dekad grid:",
    252 - len(dekadal)
)

print(
    "\nAcquisitions per dekad:"
)

print(
    dekadal[
        "acquisition_count"
    ].value_counts()
    .sort_index()
)

print(
    "\nDekadal NDVI:"
)

print(
    dekadal[
        "ndvi_weighted"
    ].describe()
)

print(
    "\nSaved:",
    OUT
)

print(
    "\nPASS: Sentinel-2 agricultural "
    "NDVI aggregated to dekads"
)
