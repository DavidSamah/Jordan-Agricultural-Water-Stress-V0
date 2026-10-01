import calendar
import re
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.windows import from_bounds

START_YEAR = 2018
END_YEAR = 2024

WEST = 35.3
SOUTH = 32.0
EAST = 35.8
NORTH = 33.3

SCALE = 0.1
OFFSET = 0.0

MAPSET = "L1-RET-D"

BASE = (
    "https://data.apps.fao.org/gismgr/api/v2/"
    "catalog/workspaces/WAPOR-3/mapsets/"
    f"{MAPSET}/rasters"
)

OUTDIR = Path(
    "v1/data/wapor_ret/processed/ret_dekad"
)

SUMMARY = Path(
    "v1/data/wapor_ret/processed/"
    "ret_2018_2024_dekadal.csv"
)

OUTDIR.mkdir(parents=True, exist_ok=True)


def collect(url):
    data = {
        "links": [{"rel": "next", "href": url}]
    }

    items = []

    while "next" in [
        x["rel"] for x in data["links"]
    ]:
        next_url = [
            x["href"]
            for x in data["links"]
            if x["rel"] == "next"
        ][0]

        r = requests.get(
            next_url,
            timeout=120
        )

        r.raise_for_status()

        data = r.json()["response"]
        items.extend(data["items"])

    return items


def parse_period(code):
    m = re.search(
        r"\.(\d{4})-(\d{2})-D([123])$",
        code
    )

    if not m:
        return None

    year = int(m.group(1))
    month = int(m.group(2))
    dekad = int(m.group(3))

    if dekad == 1:
        days = 10
        start_day = 1

    elif dekad == 2:
        days = 10
        start_day = 11

    else:
        month_days = calendar.monthrange(
            year,
            month
        )[1]

        days = month_days - 20
        start_day = 21

    return {
        "year": year,
        "month": month,
        "dekad": dekad,
        "days": days,
        "date": pd.Timestamp(
            year=year,
            month=month,
            day=start_day
        )
    }


items = collect(BASE)

selected = []

for item in items:
    period = parse_period(
        item.get("code", "")
    )

    if period is None:
        continue

    if (
        START_YEAR
        <= period["year"]
        <= END_YEAR
    ):
        selected.append(
            (item, period)
        )

selected.sort(
    key=lambda x: x[1]["date"]
)

print("Selected:", len(selected))

rows = []

for i, (item, period) in enumerate(
    selected,
    start=1
):
    code = item["code"]
    url = item.get("downloadUrl")

    if not url:
        raise RuntimeError(
            f"No URL for {code}"
        )

    print(
        f"[{i}/{len(selected)}]",
        code
    )

    with rasterio.open(url) as src:

        window = from_bounds(
            WEST,
            SOUTH,
            EAST,
            NORTH,
            transform=src.transform
        )

        window = (
            window
            .round_offsets()
            .round_lengths()
        )

        raw = src.read(
            1,
            window=window,
            masked=True
        )

        daily = (
            raw.astype("float32")
            * SCALE
            + OFFSET
        )

        dekad_total = (
            daily
            * period["days"]
        )

        valid = dekad_total.compressed()

        if len(valid) == 0:
            raise RuntimeError(
                f"No RET values for {code}"
            )

        transform = src.window_transform(
            window
        )

        outfile = (
            OUTDIR
            / f"{code}_NJValley.tif"
        )

        profile = src.profile.copy()

        profile.update(
            width=raw.shape[1],
            height=raw.shape[0],
            transform=transform,
            dtype="float32",
            nodata=-9999.0,
            compress="deflate"
        )

        with rasterio.open(
            outfile,
            "w",
            **profile
        ) as dst:

            dst.write(
                dekad_total.filled(-9999.0),
                1
            )

            dst.update_tags(
                variable="Reference Evapotranspiration",
                units="mm/dekad",
                source="FAO WaPOR v3 L1-RET-D",
                original_units="mm/day",
                scale_factor=str(SCALE),
                offset=str(OFFSET),
                dekad_days=str(period["days"])
            )

        rows.append({
            "date": period["date"],
            "year": period["year"],
            "month": period["month"],
            "dekad": period["dekad"],
            "days": period["days"],
            "valid_pixels": len(valid),
            "ret_mean_mm_dekad":
                float(valid.mean()),
            "ret_median_mm_dekad":
                float(np.median(valid)),
            "ret_min_mm_dekad":
                float(valid.min()),
            "ret_max_mm_dekad":
                float(valid.max()),
            "raster":
                str(outfile)
        })

        print(
            "RET mean:",
            round(
                rows[-1][
                    "ret_mean_mm_dekad"
                ],
                3
            ),
            "mm/dekad"
        )


df = pd.DataFrame(rows)

df.to_csv(
    SUMMARY,
    index=False
)

print("\nRows:", len(df))
print("Null RET:", df["ret_mean_mm_dekad"].isna().sum())
print("Saved:", SUMMARY)

if len(df) == 252:
    print("\nPASS: complete 2018–2024 RET series")
else:
    print(
        "\nCHECK: expected 252 dekads, got",
        len(df)
    )
