from pathlib import Path
import pandas as pd


INPUT = Path(
    "v1/data/processed_v2/"
    "predictor_alignment_dekadal.csv"
)


df = pd.read_csv(INPUT)

KEY = [
    "year",
    "month",
    "dekad",
]


print("=" * 72)
print("DEKADAL ALIGNMENT QA")
print("=" * 72)

print("Rows:", len(df))
print(
    "Unique keys:",
    df[KEY].drop_duplicates().shape[0]
)

print(
    "Duplicate keys:",
    df.duplicated(KEY).sum()
)


# ---------------------------------------------------------
# 1. Build the expected canonical 2018–2024 grid
# ---------------------------------------------------------

expected = []

for year in range(2018, 2025):

    for month in range(1, 13):

        for dekad in [1, 2, 3]:

            expected.append(
                {
                    "year": year,
                    "month": month,
                    "dekad": dekad,
                }
            )


expected = pd.DataFrame(expected)


# ---------------------------------------------------------
# 2. Compare actual vs expected
# ---------------------------------------------------------

check = expected.merge(
    df[KEY],
    on=KEY,
    how="outer",
    indicator=True,
)


missing = check[
    check["_merge"] == "left_only"
]

extra = check[
    check["_merge"] == "right_only"
]


print()
print("Expected dekads:", len(expected))

print(
    "Missing calendar dekads:",
    len(missing)
)

print(
    "Unexpected calendar keys:",
    len(extra)
)


if len(missing):

    print()
    print("MISSING:")
    print(
        missing[KEY].to_string(
            index=False
        )
    )


if len(extra):

    print()
    print("EXTRA:")
    print(
        extra[KEY].to_string(
            index=False
        )
    )


# ---------------------------------------------------------
# 3. Verify ordering
# ---------------------------------------------------------

ordered = df.sort_values(
    KEY
).reset_index(drop=True)

same_order = (
    df[KEY]
    .reset_index(drop=True)
    .equals(
        ordered[KEY]
    )
)

print()
print(
    "Already chronologically ordered:",
    same_order
)


# ---------------------------------------------------------
# 4. Verify time index
# ---------------------------------------------------------

if "time_index" in df.columns:

    expected_index = list(
        range(len(df))
    )

    index_ok = (
        df["time_index"].tolist()
        == expected_index
    )

    print(
        "time_index continuous:",
        index_ok
    )

else:

    print(
        "time_index column missing"
    )

    index_ok = False


# ---------------------------------------------------------
# 5. Predictor missingness
# ---------------------------------------------------------

predictors = [
    "precipitation_mean_mm",
    "soil_moisture_0_7cm_mean",
    "soil_moisture_7_28cm_mean",
    "soil_moisture_28_100cm_mean",
    "temperature_2m_mean_c",
    "agricultural_aeti_weighted_mm",
    "ret_mean_mm_dekad",
]


print()
print("PREDICTOR MISSINGNESS")
print("-" * 72)

for col in predictors:

    if col in df.columns:

        print(
            f"{col}:",
            int(df[col].isna().sum())
        )

    else:

        print(
            f"{col}: COLUMN MISSING"
        )


# ---------------------------------------------------------
# 6. NDVI availability
# ---------------------------------------------------------

if "ndvi_weighted" in df.columns:

    observed = int(
        df["ndvi_weighted"]
        .notna()
        .sum()
    )

    missing_ndvi = int(
        df["ndvi_weighted"]
        .isna()
        .sum()
    )

    print()
    print(
        "Observed NDVI dekads:",
        observed
    )

    print(
        "Missing NDVI dekads:",
        missing_ndvi
    )


# ---------------------------------------------------------
# 7. Final decision
# ---------------------------------------------------------

calendar_pass = (
    len(df) == 252
    and df.duplicated(KEY).sum() == 0
    and len(missing) == 0
    and len(extra) == 0
    and same_order
    and index_ok
)


print()
print("=" * 72)

if calendar_pass:

    print(
        "RESULT: DEKADAL ALIGNMENT PASS"
    )

else:

    print(
        "RESULT: ALIGNMENT REVIEW REQUIRED"
    )

print("=" * 72)
