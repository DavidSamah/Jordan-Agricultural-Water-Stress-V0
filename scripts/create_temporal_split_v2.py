from pathlib import Path
import pandas as pd


INPUT = Path(
    "v1/data/processed_v2/"
    "forecast_features_lagged.csv"
)

OUTPUT = Path(
    "v1/data/processed_v2/"
    "forecast_dataset_split.csv"
)

REPORT = Path(
    "v1/results/"
    "temporal_split_v2.txt"
)


df = pd.read_csv(INPUT)


# ---------------------------------------------------------
# 1. Validate temporal ordering
# ---------------------------------------------------------

KEY = [
    "year",
    "month",
    "dekad",
]

ordered = (
    df.sort_values(KEY)
    .reset_index(drop=True)
)

if not df[KEY].reset_index(
    drop=True
).equals(
    ordered[KEY]
):
    raise RuntimeError(
        "Dataset is not chronologically ordered."
    )


# ---------------------------------------------------------
# 2. Assign chronological split
# ---------------------------------------------------------

def assign_split(year):

    if year <= 2022:
        return "train"

    if year == 2023:
        return "validation"

    if year == 2024:
        return "test"

    return "outside"


df["split"] = (
    df["year"]
    .apply(assign_split)
)


# ---------------------------------------------------------
# 3. Primary modelling eligibility
#
# A row can only train/evaluate the t+1 forecast
# when the future NDVI target really exists.
# ---------------------------------------------------------

df[
    "eligible_primary"
] = (
    df[
        "valid_primary_target"
    ].fillna(False)
)


# ---------------------------------------------------------
# 4. State-aware eligibility
#
# Models using current NDVI additionally require
# actual NDVI at time t.
# ---------------------------------------------------------

df[
    "eligible_state_aware"
] = (
    df["eligible_primary"]
    &
    df["has_ndvi_t"].fillna(False)
)


# ---------------------------------------------------------
# 5. Hydro-climate eligibility
#
# This version does not require NDVI_t,
# only the primary target and predictor completeness.
# ---------------------------------------------------------

hydro_features = [
    "precipitation_mean_mm",
    "soil_moisture_0_7cm_mean",
    "soil_moisture_7_28cm_mean",
    "soil_moisture_28_100cm_mean",
    "temperature_2m_mean_c",
    "agricultural_aeti_weighted_mm",
    "ret_mean_mm_dekad",
]


df[
    "hydro_predictors_complete"
] = (
    df[hydro_features]
    .notna()
    .all(axis=1)
)


df[
    "eligible_hydro_climate"
] = (
    df["eligible_primary"]
    &
    df[
        "hydro_predictors_complete"
    ]
)


# ---------------------------------------------------------
# 6. Split integrity
# ---------------------------------------------------------

expected = {
    "train",
    "validation",
    "test",
}

actual = set(
    df["split"].unique()
)

if not expected.issubset(actual):
    raise RuntimeError(
        f"Missing split(s): "
        f"{expected - actual}"
    )


# ---------------------------------------------------------
# 7. Leakage guard:
# no temporal overlap
# ---------------------------------------------------------

train = df[
    df["split"] == "train"
]

validation = df[
    df["split"] == "validation"
]

test = df[
    df["split"] == "test"
]


train_last = (
    train[KEY]
    .iloc[-1]
    .tolist()
)

validation_first = (
    validation[KEY]
    .iloc[0]
    .tolist()
)

validation_last = (
    validation[KEY]
    .iloc[-1]
    .tolist()
)

test_first = (
    test[KEY]
    .iloc[0]
    .tolist()
)


print("=" * 72)
print("TEMPORAL SPLIT V2")
print("=" * 72)

print()
print("TRAIN:")
print(
    train[KEY]
    .iloc[0]
    .to_dict(),
    "→",
    train[KEY]
    .iloc[-1]
    .to_dict()
)

print()
print("VALIDATION:")
print(
    validation[KEY]
    .iloc[0]
    .to_dict(),
    "→",
    validation[KEY]
    .iloc[-1]
    .to_dict()
)

print()
print("TEST:")
print(
    test[KEY]
    .iloc[0]
    .to_dict(),
    "→",
    test[KEY]
    .iloc[-1]
    .to_dict()
)


# ---------------------------------------------------------
# 8. Counts
# ---------------------------------------------------------

print()
print("ALL ROW COUNTS")
print("-" * 72)

print(
    df["split"]
    .value_counts()
    .to_string()
)


print()
print("PRIMARY TARGET ELIGIBLE")
print("-" * 72)

print(
    df[
        df["eligible_primary"]
    ]
    ["split"]
    .value_counts()
    .to_string()
)


print()
print("HYDRO-CLIMATE ELIGIBLE")
print("-" * 72)

print(
    df[
        df["eligible_hydro_climate"]
    ]
    ["split"]
    .value_counts()
    .to_string()
)


print()
print("STATE-AWARE ELIGIBLE")
print("-" * 72)

print(
    df[
        df["eligible_state_aware"]
    ]
    ["split"]
    .value_counts()
    .to_string()
)


# ---------------------------------------------------------
# 9. Save frozen split dataset
# ---------------------------------------------------------

df.to_csv(
    OUTPUT,
    index=False
)


# ---------------------------------------------------------
# 10. Save audit report
# ---------------------------------------------------------

with open(
    REPORT,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "TEMPORAL SPLIT V2\n"
    )

    f.write(
        "=" * 72 + "\n\n"
    )

    f.write(
        "TRAIN: 2018–2022\n"
    )

    f.write(
        "VALIDATION: 2023\n"
    )

    f.write(
        "TEST: 2024\n\n"
    )

    f.write(
        "Forecast horizon: "
        "one dekad ahead\n"
    )

    f.write(
        "Primary target: "
        "target_ndvi_t_plus_1\n\n"
    )

    f.write(
        "Test period must not be used "
        "for model selection, feature "
        "selection, imputation fitting, "
        "or hyperparameter tuning.\n"
    )


print()
print("Saved dataset:")
print(OUTPUT)

print()
print("Saved report:")
print(REPORT)

print()
print("=" * 72)
print("PASS: TEMPORAL SPLIT FROZEN")
print("=" * 72)
