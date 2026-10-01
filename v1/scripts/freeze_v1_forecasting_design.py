from pathlib import Path
import pandas as pd

SRC = Path(
    "v1/data/processed_v1/"
    "forecast_dataset_dekadal.csv"
)

OUT = Path(
    "v1/data/processed_v1/"
    "forecast_dataset_frozen.csv"
)

TARGET = "target_ndvi_t_plus_1"

if not SRC.exists():
    raise SystemExit(
        f"STOP: missing source dataset: {SRC}"
    )

df = pd.read_csv(SRC)

required = [
    "year",
    "month",
    "dekad",
    TARGET,
]

missing = [
    c for c in required
    if c not in df.columns
]

if missing:
    raise RuntimeError(
        f"STOP: missing columns: {missing}"
    )

df = (
    df
    .sort_values(
        ["year", "month", "dekad"]
    )
    .reset_index(drop=True)
)

if (
    df[
        ["year", "month", "dekad"]
    ]
    .duplicated()
    .any()
):
    raise RuntimeError(
        "STOP: duplicate dekads detected"
    )


def assign_split(year):
    year = int(year)

    if 2018 <= year <= 2022:
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

df["valid_primary_target"] = (
    df[TARGET]
    .notna()
)

outside = (
    df["split"]
    .eq("outside")
    .sum()
)

if outside:
    raise RuntimeError(
        f"STOP: {outside} rows outside "
        "2018–2024"
    )

print("Rows:", len(df))

print("\nRows per split:")
print(
    df.groupby("split")
    .size()
)

print("\nTarget availability:")
print(
    df.groupby("split")[
        "valid_primary_target"
    ]
    .agg(
        available="sum",
        total="count"
    )
)

print("\nTarget summary:")
print(
    df.loc[
        df["valid_primary_target"]
    ]
    .groupby("split")[
        TARGET
    ]
    .describe()
)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUT,
    index=False
)

print("\nSaved:", OUT)

print(
    "\nPASS: forecasting design frozen"
)

print(
    "\nTRAIN      = 2018–2022"
)

print(
    "VALIDATION = 2023"
)

print(
    "TEST       = 2024"
)
