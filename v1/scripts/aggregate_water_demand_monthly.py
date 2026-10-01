import pandas as pd
from pathlib import Path

SRC = Path(
    "v1/data/processed_v1/"
    "water_demand_diagnostics_dekadal.csv"
)

OUT = Path(
    "v1/data/processed_v1/"
    "water_demand_diagnostics_monthly.csv"
)

df = pd.read_csv(SRC)

monthly = (
    df.groupby(
        ["year", "month"],
        as_index=False
    )
    .agg(
        agricultural_aeti_mm=(
            "agricultural_aeti_weighted_mm",
            "sum"
        ),
        ret_mm=(
            "ret_mean_mm_dekad",
            "sum"
        ),
        dekads=(
            "dekad",
            "count"
        )
    )
)

monthly["aeti_ret_ratio"] = (
    monthly["agricultural_aeti_mm"]
    /
    monthly["ret_mm"]
)

monthly["ret_minus_aeti_mm"] = (
    monthly["ret_mm"]
    -
    monthly["agricultural_aeti_mm"]
)

monthly["time"] = pd.to_datetime(
    dict(
        year=monthly["year"],
        month=monthly["month"],
        day=1
    )
)

monthly = monthly[
    [
        "time",
        "agricultural_aeti_mm",
        "ret_mm",
        "aeti_ret_ratio",
        "ret_minus_aeti_mm",
        "dekads"
    ]
]

monthly.to_csv(
    OUT,
    index=False
)

print(monthly.head(12))

print("\nRows:", len(monthly))

print(
    "Months with != 3 dekads:",
    int(
        (monthly["dekads"] != 3).sum()
    )
)

print("\nSaved:", OUT)
