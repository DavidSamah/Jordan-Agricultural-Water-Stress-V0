from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path(
    "v1/data/sentinel2/agricultural_ndvi_observations.csv"
)

OUT_DIR = Path("v1/results/ndvi_qa")
OUT_DIR.mkdir(parents=True, exist_ok=True)

QA_OUTPUT = OUT_DIR / "agricultural_ndvi_qa.csv"
SUMMARY_OUTPUT = OUT_DIR / "ndvi_qa_summary.txt"


# ---------------------------------------------------------
# 1. LOAD
# ---------------------------------------------------------

df = pd.read_csv(INPUT)

print("=" * 72)
print("SENTINEL-2 AGRICULTURAL NDVI QA")
print("=" * 72)
print("Rows:", len(df))
print("Columns:", list(df.columns))


# ---------------------------------------------------------
# 2. COLUMN DISCOVERY
# ---------------------------------------------------------

def find_column(candidates):
    lowered = {c.lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]

    for original in df.columns:
        name = original.lower()
        for candidate in candidates:
            if candidate.lower() in name:
                return original

    return None


date_col = find_column([
    "date",
    "acquisition_date",
    "datetime",
])

ndvi_col = find_column([
    "weighted_ndvi",
    "agricultural_ndvi",
    "mean_ndvi",
    "ndvi",
])

coverage_col = find_column([
    "coverage",
    "coverage_fraction",
])

pixels_col = find_column([
    "agricultural_pixels",
    "ag_pixels",
    "valid_agricultural_pixels",
])


required = {
    "date": date_col,
    "ndvi": ndvi_col,
}

missing = [
    name
    for name, column in required.items()
    if column is None
]

if missing:
    raise RuntimeError(
        f"Could not locate required columns: {missing}. "
        f"Available columns: {list(df.columns)}"
    )


print()
print("Detected:")
print("Date:", date_col)
print("NDVI:", ndvi_col)
print("Coverage:", coverage_col)
print("Agricultural pixels:", pixels_col)


# ---------------------------------------------------------
# 3. BASIC STRUCTURAL VALIDATION
# ---------------------------------------------------------

df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

invalid_dates = int(df[date_col].isna().sum())
duplicate_dates = int(df[date_col].duplicated().sum())
missing_ndvi = int(df[ndvi_col].isna().sum())

df = df.sort_values(date_col).reset_index(drop=True)

print()
print("STRUCTURAL QA")
print("-" * 72)
print("Invalid dates:", invalid_dates)
print("Duplicate dates:", duplicate_dates)
print("Missing NDVI:", missing_ndvi)


# ---------------------------------------------------------
# 4. NDVI RANGE QA
# ---------------------------------------------------------

ndvi = pd.to_numeric(df[ndvi_col], errors="coerce")

df["qa_ndvi_missing"] = ndvi.isna()

# Mathematical NDVI range.
df["qa_ndvi_outside_physical_range"] = (
    (ndvi < -1) | (ndvi > 1)
)

# Not necessarily bad — just scientifically worth inspecting.
df["qa_ndvi_negative"] = ndvi < 0

df["qa_ndvi_very_low"] = (
    (ndvi >= 0) & (ndvi < 0.10)
)

print()
print("NDVI QA")
print("-" * 72)
print("Minimum NDVI:", ndvi.min())
print("Maximum NDVI:", ndvi.max())
print("Mean NDVI:", ndvi.mean())
print("Median NDVI:", ndvi.median())
print(
    "Outside [-1, 1]:",
    int(df["qa_ndvi_outside_physical_range"].sum())
)
print(
    "Negative NDVI:",
    int(df["qa_ndvi_negative"].sum())
)


# ---------------------------------------------------------
# 5. COVERAGE QA
# ---------------------------------------------------------

if coverage_col is not None:

    coverage = pd.to_numeric(
        df[coverage_col],
        errors="coerce"
    )

    df["qa_coverage_missing"] = coverage.isna()

    # Diagnostic thresholds only.
    # We are NOT automatically deleting these observations.
    df["qa_coverage_lt_005"] = coverage < 0.05
    df["qa_coverage_lt_010"] = coverage < 0.10
    df["qa_coverage_lt_025"] = coverage < 0.25
    df["qa_coverage_lt_050"] = coverage < 0.50

    print()
    print("COVERAGE QA")
    print("-" * 72)
    print("Minimum:", coverage.min())
    print("Maximum:", coverage.max())
    print("Median:", coverage.median())

    for threshold in [0.05, 0.10, 0.25, 0.50]:
        count = int((coverage < threshold).sum())
        print(
            f"Coverage < {threshold:.2f}:",
            count
        )


# ---------------------------------------------------------
# 6. AGRICULTURAL PIXEL QA
# ---------------------------------------------------------

if pixels_col is not None:

    pixels = pd.to_numeric(
        df[pixels_col],
        errors="coerce"
    )

    df["qa_pixels_missing"] = pixels.isna()

    q01 = pixels.quantile(0.01)
    q05 = pixels.quantile(0.05)
    q50 = pixels.quantile(0.50)

    df["qa_pixels_bottom_1pct"] = pixels <= q01
    df["qa_pixels_bottom_5pct"] = pixels <= q05

    print()
    print("AGRICULTURAL PIXEL QA")
    print("-" * 72)
    print("Minimum:", pixels.min())
    print("1% quantile:", q01)
    print("5% quantile:", q05)
    print("Median:", q50)
    print("Maximum:", pixels.max())


# ---------------------------------------------------------
# 7. TEMPORAL GAPS
# ---------------------------------------------------------

df["days_since_previous"] = (
    df[date_col]
    .diff()
    .dt.days
)

gap_stats = df["days_since_previous"].dropna()

print()
print("TEMPORAL QA")
print("-" * 72)

if len(gap_stats):
    print(
        "Median interval:",
        gap_stats.median(),
        "days"
    )
    print(
        "Largest interval:",
        gap_stats.max(),
        "days"
    )


# ---------------------------------------------------------
# 8. ROBUST TEMPORAL OUTLIERS
# ---------------------------------------------------------

rolling_median = (
    ndvi
    .rolling(
        window=7,
        center=True,
        min_periods=3,
    )
    .median()
)

residual = ndvi - rolling_median

median_residual = residual.median()

mad = np.median(
    np.abs(
        residual.dropna()
        - median_residual
    )
)

if mad > 0:

    robust_z = (
        0.6745
        * (residual - median_residual)
        / mad
    )

else:
    robust_z = pd.Series(
        np.nan,
        index=df.index
    )


df["ndvi_rolling_median_7"] = rolling_median
df["ndvi_robust_z"] = robust_z

df["qa_temporal_outlier"] = (
    robust_z.abs() > 3.5
)


print(
    "Potential temporal NDVI outliers:",
    int(df["qa_temporal_outlier"].sum())
)


# ---------------------------------------------------------
# 9. COMBINED QA FLAGS
# ---------------------------------------------------------

flag_columns = [
    c
    for c in df.columns
    if c.startswith("qa_")
]

df["qa_flag_count"] = (
    df[flag_columns]
    .fillna(False)
    .astype(bool)
    .sum(axis=1)
)

df["qa_any_flag"] = (
    df["qa_flag_count"] > 0
)


# Severe means something structurally impossible or missing,
# NOT simply low coverage.
severe_columns = [
    "qa_ndvi_missing",
    "qa_ndvi_outside_physical_range",
]

df["qa_severe"] = (
    df[severe_columns]
    .fillna(False)
    .any(axis=1)
)


# ---------------------------------------------------------
# 10. SAVE QA TABLE
# ---------------------------------------------------------

df.to_csv(
    QA_OUTPUT,
    index=False,
)

print()
print("Saved QA table:")
print(QA_OUTPUT)


# ---------------------------------------------------------
# 11. PLOTS
# ---------------------------------------------------------

plt.figure(figsize=(14, 5))
plt.plot(
    df[date_col],
    ndvi,
    linewidth=1,
)
plt.xlabel("Date")
plt.ylabel("Weighted agricultural NDVI")
plt.title(
    "Sentinel-2 Agricultural NDVI Through Time"
)
plt.tight_layout()
plt.savefig(
    OUT_DIR / "01_ndvi_timeseries.png",
    dpi=180,
)
plt.close()


if coverage_col is not None:

    coverage = pd.to_numeric(
        df[coverage_col],
        errors="coerce"
    )

    plt.figure(figsize=(14, 5))
    plt.plot(
        df[date_col],
        coverage,
        linewidth=1,
    )
    plt.xlabel("Date")
    plt.ylabel("Coverage")
    plt.title(
        "Sentinel-2 Observation Coverage Through Time"
    )
    plt.tight_layout()
    plt.savefig(
        OUT_DIR / "02_coverage_timeseries.png",
        dpi=180,
    )
    plt.close()


    plt.figure(figsize=(7, 6))
    plt.scatter(
        coverage,
        ndvi,
        alpha=0.6,
    )
    plt.xlabel("Coverage")
    plt.ylabel("Weighted NDVI")
    plt.title(
        "NDVI vs Observation Coverage"
    )
    plt.tight_layout()
    plt.savefig(
        OUT_DIR / "03_ndvi_vs_coverage.png",
        dpi=180,
    )
    plt.close()


if pixels_col is not None:

    pixels = pd.to_numeric(
        df[pixels_col],
        errors="coerce"
    )

    plt.figure(figsize=(14, 5))
    plt.plot(
        df[date_col],
        pixels,
        linewidth=1,
    )
    plt.xlabel("Date")
    plt.ylabel("Agricultural pixels")
    plt.title(
        "Usable Agricultural Pixels Through Time"
    )
    plt.tight_layout()
    plt.savefig(
        OUT_DIR / "04_agricultural_pixels.png",
        dpi=180,
    )
    plt.close()


    plt.figure(figsize=(7, 6))
    plt.scatter(
        pixels,
        ndvi,
        alpha=0.6,
    )
    plt.xlabel("Agricultural pixels")
    plt.ylabel("Weighted NDVI")
    plt.title(
        "NDVI vs Agricultural Pixel Count"
    )
    plt.tight_layout()
    plt.savefig(
        OUT_DIR / "05_ndvi_vs_pixels.png",
        dpi=180,
    )
    plt.close()


# ---------------------------------------------------------
# 12. MONTHLY / SEASONAL BEHAVIOUR
# ---------------------------------------------------------

df["year"] = df[date_col].dt.year
df["month"] = df[date_col].dt.month

monthly = (
    df.groupby("month")[ndvi_col]
    .agg(
        count="count",
        mean="mean",
        median="median",
        std="std",
    )
)

monthly.to_csv(
    OUT_DIR / "monthly_ndvi_summary.csv"
)

plt.figure(figsize=(9, 5))
plt.plot(
    monthly.index,
    monthly["median"],
    marker="o",
)
plt.xticks(range(1, 13))
plt.xlabel("Month")
plt.ylabel("Median NDVI")
plt.title(
    "Median Agricultural NDVI by Month"
)
plt.tight_layout()
plt.savefig(
    OUT_DIR / "06_monthly_ndvi_cycle.png",
    dpi=180,
)
plt.close()


# ---------------------------------------------------------
# 13. WRITE HUMAN-READABLE SUMMARY
# ---------------------------------------------------------

with open(
    SUMMARY_OUTPUT,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "Sentinel-2 Agricultural NDVI QA\n"
    )
    f.write("=" * 60 + "\n\n")

    f.write(
        f"Observations: {len(df)}\n"
    )

    f.write(
        f"Date range: "
        f"{df[date_col].min()} "
        f"to "
        f"{df[date_col].max()}\n"
    )

    f.write(
        f"NDVI range: "
        f"{ndvi.min():.6f} "
        f"to "
        f"{ndvi.max():.6f}\n"
    )

    f.write(
        f"Median NDVI: "
        f"{ndvi.median():.6f}\n"
    )

    f.write(
        f"Invalid dates: "
        f"{invalid_dates}\n"
    )

    f.write(
        f"Duplicate dates: "
        f"{duplicate_dates}\n"
    )

    f.write(
        f"Missing NDVI: "
        f"{missing_ndvi}\n"
    )

    f.write(
        f"Physical-range failures: "
        f"{int(df['qa_ndvi_outside_physical_range'].sum())}\n"
    )

    f.write(
        f"Temporal outliers: "
        f"{int(df['qa_temporal_outlier'].sum())}\n"
    )

    f.write(
        f"Severe QA failures: "
        f"{int(df['qa_severe'].sum())}\n"
    )

    if coverage_col is not None:
        f.write(
            f"Coverage < 0.10: "
            f"{int((coverage < 0.10).sum())}\n"
        )

        f.write(
            f"Coverage < 0.25: "
            f"{int((coverage < 0.25).sum())}\n"
        )


print()
print("Saved summary:")
print(SUMMARY_OUTPUT)

print()
print("QA plots saved to:")
print(OUT_DIR)

print()
print("=" * 72)

if df["qa_severe"].any():
    print(
        "RESULT: REVIEW REQUIRED — "
        "severe structural/physical QA failures detected."
    )
else:
    print(
        "RESULT: STRUCTURAL QA PASS — "
        "proceed to inspect observational-quality flags."
    )

print("=" * 72)
