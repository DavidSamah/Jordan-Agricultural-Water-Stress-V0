from pathlib import Path

import numpy as np
import pandas as pd


INPUT = Path(
    "v1/results/ndvi_qa/"
    "ndvi_quality_relationship.csv"
)

OUT_ALL = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_qa_final.csv"
)

OUT_MODEL = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_model_candidate.csv"
)

OUT_ANOMALIES = Path(
    "v1/results/ndvi_qa/"
    "high_priority_anomalies.csv"
)


df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(df["date"])


# ---------------------------------------------------------
# 1. QUALITY TIERS
# ---------------------------------------------------------

conditions = [
    df["coverage_fraction"] >= 0.50,

    (
        (df["coverage_fraction"] >= 0.25)
        & (df["coverage_fraction"] < 0.50)
    ),

    (
        (df["coverage_fraction"] >= 0.10)
        & (df["coverage_fraction"] < 0.25)
    ),

    (
        (df["coverage_fraction"] >= 0.05)
        & (df["coverage_fraction"] < 0.10)
    ),

    df["coverage_fraction"] < 0.05,
]


labels = [
    "A_high",
    "B_moderate",
    "C_low",
    "D_very_low",
    "E_critical_support",
]


df["qa_quality_tier"] = np.select(
    conditions,
    labels,
    default="unknown",
)


# ---------------------------------------------------------
# 2. V1 HIGH-PRIORITY OBSERVATION ANOMALY
# ---------------------------------------------------------

df["qa_high_priority_anomaly_v1"] = (
    (df["coverage_fraction"] < 0.05)
    &
    (df["absolute_local_deviation"] > 0.15)
)


# ---------------------------------------------------------
# 3. MODEL ELIGIBILITY
# ---------------------------------------------------------

# Important:
# This does NOT permanently delete data.
#
# It defines the first V1 candidate series for downstream
# modelling while preserving the complete observation table.

df["model_candidate_v1"] = (
    ~df["qa_high_priority_anomaly_v1"]
)


# ---------------------------------------------------------
# 4. SAVE COMPLETE QA TABLE
# ---------------------------------------------------------

df.to_csv(
    OUT_ALL,
    index=False
)


# ---------------------------------------------------------
# 5. SAVE MODEL-CANDIDATE TABLE
# ---------------------------------------------------------

model_df = df[
    df["model_candidate_v1"]
].copy()

model_df.to_csv(
    OUT_MODEL,
    index=False
)


# ---------------------------------------------------------
# 6. SAVE THE ANOMALIES SEPARATELY
# ---------------------------------------------------------

anomalies = df[
    df["qa_high_priority_anomaly_v1"]
].copy()

anomalies.to_csv(
    OUT_ANOMALIES,
    index=False
)


# ---------------------------------------------------------
# 7. REPORT
# ---------------------------------------------------------

print("=" * 72)
print("FINAL SENTINEL-2 NDVI QA")
print("=" * 72)

print()
print("Total observations:", len(df))

print()
print("Quality tiers:")
print(
    df["qa_quality_tier"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print(
    "High-priority anomalies:",
    int(df["qa_high_priority_anomaly_v1"].sum())
)

print(
    "V1 model-candidate observations:",
    int(df["model_candidate_v1"].sum())
)

print()
print("Excluded from V1 candidate series:")

cols = [
    "date",
    "coverage_fraction",
    "agricultural_pixels",
    "agricultural_ndvi_weighted",
    "local_ndvi_reference",
    "absolute_local_deviation",
]

print(
    anomalies[cols]
    .sort_values(
        "absolute_local_deviation",
        ascending=False
    )
    .to_string(index=False)
)

print()
print("Saved complete QA dataset:")
print(OUT_ALL)

print()
print("Saved model-candidate dataset:")
print(OUT_MODEL)

print()
print("Saved anomaly audit table:")
print(OUT_ANOMALIES)

print()
print("=" * 72)
print("FINAL NDVI QA: PASS")
print("=" * 72)
