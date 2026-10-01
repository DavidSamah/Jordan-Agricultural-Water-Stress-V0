from pathlib import Path

import numpy as np
import pandas as pd


INPUT = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_model_candidate.csv"
)

OUTPUT = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_dekadal_final.csv"
)


df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(
    df["date"],
    errors="raise"
)


# ---------------------------------------------------------
# 1. Validate source
# ---------------------------------------------------------

assert len(df) == 481, (
    f"Expected 481 QA-screened observations, "
    f"found {len(df)}"
)

assert df["model_candidate_v1"].all(), (
    "Input contains observations that are not "
    "V1 model candidates."
)

assert df[
    "agricultural_ndvi_weighted"
].notna().all()

assert df[
    "crop_equivalent_weight"
].notna().all()


print("=" * 72)
print("FINAL DEKADAL NDVI CONSTRUCTION")
print("=" * 72)

print("Input observations:", len(df))
print(
    "Date range:",
    df["date"].min().date(),
    "to",
    df["date"].max().date()
)


# ---------------------------------------------------------
# 2. Quality-weighted aggregation helper
# ---------------------------------------------------------

def weighted_mean(values, weights):

    values = np.asarray(
        values,
        dtype=float
    )

    weights = np.asarray(
        weights,
        dtype=float
    )

    valid = (
        np.isfinite(values)
        &
        np.isfinite(weights)
        &
        (weights > 0)
    )

    if not valid.any():
        return np.nan

    return np.average(
        values[valid],
        weights=weights[valid]
    )


# ---------------------------------------------------------
# 3. Group acquisition dates into dekads
# ---------------------------------------------------------

records = []


for (
    year,
    month,
    dekad
), g in df.groupby(
    ["year", "month", "dekad"],
    sort=True
):

    weights = g[
        "crop_equivalent_weight"
    ]

    ndvi = g[
        "agricultural_ndvi_weighted"
    ]


    record = {

        "year": int(year),

        "month": int(month),

        "dekad": int(dekad),

        "ndvi_weighted": weighted_mean(
            ndvi,
            weights
        ),

        "ndvi_mean": ndvi.mean(),

        "ndvi_median": ndvi.median(),

        "ndvi_min": ndvi.min(),

        "ndvi_max": ndvi.max(),

        "ndvi_std": (
            ndvi.std(ddof=0)
            if len(g) > 1
            else 0.0
        ),

        "acquisition_count": len(g),

        "mean_coverage_fraction":
            g["coverage_fraction"].mean(),

        "max_coverage_fraction":
            g["coverage_fraction"].max(),

        "min_coverage_fraction":
            g["coverage_fraction"].min(),

        "mean_agricultural_pixels":
            g["agricultural_pixels"].mean(),

        "total_quality_weight":
            weights.sum(),

        "quality_tier_A_count":
            (g["qa_quality_tier"] == "A_high").sum(),

        "quality_tier_B_count":
            (g["qa_quality_tier"] == "B_moderate").sum(),

        "quality_tier_C_count":
            (g["qa_quality_tier"] == "C_low").sum(),

        "quality_tier_D_count":
            (g["qa_quality_tier"] == "D_very_low").sum(),

        "quality_tier_E_count":
            (
                g["qa_quality_tier"]
                == "E_critical_support"
            ).sum(),
    }

    records.append(record)


out = pd.DataFrame(records)


# ---------------------------------------------------------
# 4. Canonical dekad date
# ---------------------------------------------------------

dekad_day = {
    1: 1,
    2: 11,
    3: 21,
}


out.insert(
    0,
    "date",
    pd.to_datetime({
        "year": out["year"],
        "month": out["month"],
        "day": out["dekad"].map(
            dekad_day
        ),
    })
)


# ---------------------------------------------------------
# 5. Validate output
# ---------------------------------------------------------

duplicates = out.duplicated(
    ["year", "month", "dekad"]
).sum()


print()
print("Observed dekads:", len(out))
print(
    "Duplicate dekad keys:",
    duplicates
)

print(
    "NDVI missing:",
    out["ndvi_weighted"].isna().sum()
)

print(
    "Acquisitions per observed dekad:"
)

print(
    out["acquisition_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


if duplicates:
    raise RuntimeError(
        "Duplicate dekadal keys detected."
    )


out.to_csv(
    OUTPUT,
    index=False
)


print()
print("Saved:")
print(OUTPUT)

print()
print("PASS: fresh dekadal NDVI created")
