import pandas as pd

src = (
    "v1/data/wapor/processed/"
    "aeti_2018_2024_dekadal.csv"
)

out = (
    "v1/data/wapor/processed/"
    "aeti_2018_2024_monthly.csv"
)

df = pd.read_csv(
    src,
    parse_dates=["date"]
)

monthly = (
    df.groupby(
        ["year", "month"],
        as_index=False
    )
    .agg(
        aeti_mm=(
            "aeti_mean_mm_dekad",
            "sum"
        ),
        dekads=(
            "dekad",
            "count"
        ),
        mean_valid_pixels=(
            "valid_pixels",
            "mean"
        )
    )
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
        "aeti_mm",
        "dekads",
        "mean_valid_pixels"
    ]
]

monthly.to_csv(
    out,
    index=False
)

print(monthly.head(12))

print(
    "\nRows:",
    len(monthly)
)

print(
    "Months with !=3 dekads:",
    (monthly["dekads"] != 3).sum()
)

print(
    "Null AETI:",
    monthly["aeti_mm"]
    .isna()
    .sum()
)

print("\nSaved:", out)
