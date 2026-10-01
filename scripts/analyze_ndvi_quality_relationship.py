from pathlib import Path
import pandas as pd
import numpy as np

INPUT = Path(
    "v1/results/ndvi_qa/agricultural_ndvi_qa.csv"
)

OUTPUT = Path(
    "v1/results/ndvi_qa/ndvi_quality_relationship.csv"
)

df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(df["date"])

ndvi = df["agricultural_ndvi_weighted"]
coverage = df["coverage_fraction"]
pixels = df["agricultural_pixels"]


# ---------------------------------------------------------
# Observation's deviation from its local temporal context
# ---------------------------------------------------------

local_reference = (
    ndvi
    .rolling(
        window=7,
        center=True,
        min_periods=3
    )
    .median()
)

df["local_ndvi_reference"] = local_reference

df["absolute_local_deviation"] = (
    ndvi - local_reference
).abs()


# ---------------------------------------------------------
# Coverage classes
# ---------------------------------------------------------

df["coverage_class"] = pd.cut(
    coverage,
    bins=[
        -np.inf,
        0.05,
        0.10,
        0.25,
        0.50,
        0.75,
        0.90,
        np.inf,
    ],
    labels=[
        "<0.05",
        "0.05-0.10",
        "0.10-0.25",
        "0.25-0.50",
        "0.50-0.75",
        "0.75-0.90",
        ">=0.90",
    ],
)


# ---------------------------------------------------------
# Summarise error by coverage
# ---------------------------------------------------------

summary = (
    df.groupby(
        "coverage_class",
        observed=True
    )
    .agg(
        observations=(
            "agricultural_ndvi_weighted",
            "size"
        ),
        median_coverage=(
            "coverage_fraction",
            "median"
        ),
        median_pixels=(
            "agricultural_pixels",
            "median"
        ),
        median_ndvi=(
            "agricultural_ndvi_weighted",
            "median"
        ),
        median_abs_local_deviation=(
            "absolute_local_deviation",
            "median"
        ),
        mean_abs_local_deviation=(
            "absolute_local_deviation",
            "mean"
        ),
    )
)


print("=" * 72)
print("NDVI QUALITY × COVERAGE")
print("=" * 72)

print()
print(summary.to_string())

print()


# ---------------------------------------------------------
# Correlations
# ---------------------------------------------------------

valid = df[
    [
        "coverage_fraction",
        "agricultural_pixels",
        "absolute_local_deviation",
    ]
].dropna()

print("Spearman correlations")
print("-" * 72)

print(
    "Coverage vs local deviation:",
    valid[
        "coverage_fraction"
    ].corr(
        valid["absolute_local_deviation"],
        method="spearman"
    )
)

print(
    "Agricultural pixels vs local deviation:",
    valid[
        "agricultural_pixels"
    ].corr(
        valid["absolute_local_deviation"],
        method="spearman"
    )
)


# ---------------------------------------------------------
# Identify strongest combinations of:
# poor spatial support + temporal disagreement
# ---------------------------------------------------------

df["qa_extreme_low_support"] = (
    (df["coverage_fraction"] < 0.05)
    |
    (df["agricultural_pixels"] < 1000)
)

df["qa_large_local_deviation"] = (
    df["absolute_local_deviation"] > 0.15
)

df["qa_strong_observation_anomaly"] = (
    df["qa_extreme_low_support"]
    &
    df["qa_large_local_deviation"]
)


suspects = df[
    df["qa_strong_observation_anomaly"]
].copy()

suspects = suspects.sort_values(
    "absolute_local_deviation",
    ascending=False
)


print()
print("=" * 72)
print("HIGH-PRIORITY OBSERVATION ANOMALIES")
print("=" * 72)

cols = [
    "date",
    "coverage_fraction",
    "agricultural_pixels",
    "agricultural_ndvi_weighted",
    "local_ndvi_reference",
    "absolute_local_deviation",
]

print(
    suspects[cols].to_string(
        index=False
    )
)


df.to_csv(
    OUTPUT,
    index=False
)

summary.to_csv(
    "v1/results/ndvi_qa/"
    "coverage_quality_summary.csv"
)

print()
print("Candidate anomalies:", len(suspects))
print("Saved:", OUTPUT)
