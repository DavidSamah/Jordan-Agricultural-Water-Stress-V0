from pathlib import Path

import pandas as pd
from pystac_client import Client

BBOX = [35.3, 32.0, 35.8, 33.3]

START = "2018-01-01"
END = "2024-12-31"

OUT = Path(
    "v1/data/sentinel2/"
    "sentinel2_observation_ledger.csv"
)

catalog = Client.open(
    "https://earth-search.aws.element84.com/v1"
)

print("Searching Sentinel-2 archive...")

items = list(
    catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=BBOX,
        datetime=f"{START}/{END}"
    ).items()
)

print("Scenes found:", len(items))

rows = []

for item in items:

    dt = pd.Timestamp(
        item.datetime
    )

    day = dt.day

    if day <= 10:
        dekad = 1
    elif day <= 20:
        dekad = 2
    else:
        dekad = 3

    rows.append({
        "scene_id": item.id,
        "datetime": dt,
        "date": dt.date(),
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "dekad": dekad,
        "cloud_cover": (
            item.properties.get(
                "eo:cloud_cover"
            )
        ),
        "has_red": (
            "red" in item.assets
        ),
        "has_nir": (
            "nir" in item.assets
        ),
        "has_scl": (
            "scl" in item.assets
        ),
    })

df = pd.DataFrame(rows)

df = df.sort_values(
    [
        "datetime",
        "scene_id"
    ]
).reset_index(drop=True)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUT,
    index=False
)

print("\nRows:", len(df))

print(
    "Unique dates:",
    df["date"].nunique()
)

print(
    "Unique dekads observed:",
    df[
        [
            "year",
            "month",
            "dekad"
        ]
    ]
    .drop_duplicates()
    .shape[0]
)

print(
    "Scenes missing required assets:",
    (
        ~(
            df["has_red"]
            &
            df["has_nir"]
            &
            df["has_scl"]
        )
    ).sum()
)

print("\nScenes per year:")

print(
    df.groupby("year")
    .size()
)

print("\nSaved:", OUT)

print(
    "\nPASS: Sentinel-2 observation ledger created"
)
