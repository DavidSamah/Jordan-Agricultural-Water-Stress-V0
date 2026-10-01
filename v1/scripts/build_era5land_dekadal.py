import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import requests

LAT = 32.65
LON = 35.55

START = "2018-01-01"
END = "2024-12-31"

URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

HOURLY = [
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
    "temperature_2m"
]

params = {
    "latitude": LAT,
    "longitude": LON,
    "start_date": START,
    "end_date": END,
    "hourly": ",".join(HOURLY),
    "models": "era5_land",
    "timezone": "UTC"
}

print(
    "Requesting ERA5-Land..."
)

r = requests.get(
    URL,
    params=params,
    timeout=180
)

print(
    "HTTP:",
    r.status_code
)

r.raise_for_status()

obj = r.json()

actual_lat = obj.get(
    "latitude"
)

actual_lon = obj.get(
    "longitude"
)

print(
    "Returned coordinate:",
    actual_lat,
    actual_lon
)

hourly = obj["hourly"]

df = pd.DataFrame({
    "time":
        pd.to_datetime(
            hourly["time"]
        ),

    "soil_0_7":
        hourly[
            "soil_moisture_0_to_7cm"
        ],

    "soil_7_28":
        hourly[
            "soil_moisture_7_to_28cm"
        ],

    "soil_28_100":
        hourly[
            "soil_moisture_28_to_100cm"
        ],

    "temperature_2m_c":
        hourly[
            "temperature_2m"
        ]
})

print(
    "Hourly rows:",
    len(df)
)

print(
    "\nNull counts:"
)

print(
    df.isna().sum()
)

if (
    df[
        [
            "soil_0_7",
            "soil_7_28",
            "soil_28_100"
        ]
    ].isna().all().any()
):
    raise RuntimeError(
        "One soil layer entirely missing"
    )


def dekad_number(day):

    if day <= 10:
        return 1

    if day <= 20:
        return 2

    return 3


df["year"] = (
    df["time"].dt.year
)

df["month"] = (
    df["time"].dt.month
)

df["dekad"] = (
    df["time"]
    .dt.day
    .apply(dekad_number)
)


agg = (
    df.groupby(
        [
            "year",
            "month",
            "dekad"
        ],
        as_index=False
    )
    .agg(
        soil_moisture_0_7cm_mean=(
            "soil_0_7",
            "mean"
        ),

        soil_moisture_7_28cm_mean=(
            "soil_7_28",
            "mean"
        ),

        soil_moisture_28_100cm_mean=(
            "soil_28_100",
            "mean"
        ),

        temperature_2m_mean_c=(
            "temperature_2m_c",
            "mean"
        ),

        observations=(
            "time",
            "count"
        )
    )
)

def start_date(row):

    if row["dekad"] == 1:
        day = 1

    elif row["dekad"] == 2:
        day = 11

    else:
        day = 21

    return pd.Timestamp(
        year=int(row["year"]),
        month=int(row["month"]),
        day=day
    )


agg["date"] = agg.apply(
    start_date,
    axis=1
)

agg["source_lat"] = actual_lat
agg["source_lon"] = actual_lon

out = Path(
    "v1/data/era5land/processed/"
    "era5land_2018_2024_dekadal.csv"
)

out.parent.mkdir(
    parents=True,
    exist_ok=True
)

agg.to_csv(
    out,
    index=False
)

print("\nDekadal rows:", len(agg))

print(
    "\nNulls:"
)

print(
    agg.isna().sum()
)

print(
    "\nFirst rows:"
)

print(
    agg.head(10).to_string(
        index=False
    )
)

print("\nSaved:", out)

if len(agg) == 252:
    print(
        "\nPASS: complete ERA5-Land "
        "dekadal series"
    )
else:
    print(
        "\nCHECK: expected 252 dekads"
    )
