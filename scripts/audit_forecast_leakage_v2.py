from pathlib import Path
import pandas as pd


INPUT = Path(
    "v1/data/processed_v2/"
    "forecast_features_lagged.csv"
)


df = pd.read_csv(INPUT)


print("=" * 72)
print("FORECAST LEAKAGE AUDIT")
print("=" * 72)


# ---------------------------------------------------------
# Columns that are forbidden as model inputs
# ---------------------------------------------------------

forbidden = [
    c
    for c in df.columns
    if (
        "target_" in c
        or "t_plus_1" in c
    )
]


print()
print("TARGET/FUTURE COLUMNS:")
for c in forbidden:
    print(" -", c)


# ---------------------------------------------------------
# Candidate safe predictors
# ---------------------------------------------------------

metadata = {
    "date",
    "year",
    "month",
    "dekad",
    "time_index",
}


safe_candidates = [
    c
    for c in df.columns
    if (
        c not in forbidden
        and c not in metadata
    )
]


print()
print(
    "Candidate non-future columns:",
    len(safe_candidates)
)


# ---------------------------------------------------------
# Shift sanity check
# ---------------------------------------------------------

check = df[
    [
        "ndvi_weighted",
        "ndvi_lag_1",
    ]
].copy()


expected_lag = (
    df["ndvi_weighted"]
    .shift(1)
)


lag_ok = (
    check[
        "ndvi_lag_1"
    ]
    .equals(
        expected_lag
    )
)


expected_target = (
    df["ndvi_weighted"]
    .shift(-1)
)


target_ok = (
    df[
        "target_ndvi_t_plus_1"
    ]
    .equals(
        expected_target
    )
)


print()
print(
    "Lag direction correct:",
    lag_ok
)

print(
    "Target direction correct:",
    target_ok
)


if not lag_ok:
    raise RuntimeError(
        "NDVI lag construction failed."
    )


if not target_ok:
    raise RuntimeError(
        "Target shift construction failed."
    )


print()
print("=" * 72)
print(
    "PASS: temporal direction "
    "verified"
)
print("=" * 72)
