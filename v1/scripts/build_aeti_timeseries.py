import calendar
import re
import time
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

SCALE_FACTOR = 0.1

MAPSET = "L2-AETI-D"

BASE = (
    "https://data.apps.fao.org/gismgr/api/v2/"
    "catalog/workspaces/WAPOR-3/mapsets/"
    f"{MAPSET}/rasters"
)

OUTDIR = Path(
    "v1/data/wapor/processed/aeti_dekad"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

SUMMARY = Path(
    "v1/data/wapor/processed/"
    "aeti_2018_2024_dekadal.csv"
)


def collect_catalog(url):
    data = {
        "links": [
            {"rel": "next", "href": url}
        ]
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

        print("Catalog:", next_url)

        r = requests.get(
            next_url,
            timeout=120
        )

        r.raise_for_status()

        data = r.json()["response"]

        items.extend(
            data["items"]
        )

    return items


def parse_period(code):
    match = re.search(
        r"\.(\d{4})-(\d{2})-D([123])$",
        code
    )

    if not match:
        return None

    year = int(match.group(1))
    month = int(match.group(2))
    dekad = int(match.group(3))

    if dekad == 1:
        days = 10
        start_day = 1

    elif dekad == 2:
        days = 10
        start_day = 11

    else:
        total_days = calendar.monthrange(
            year,
            month
        )[1]

        days = total_days - 20
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


print("Retrieving WaPOR catalog...")

items = collect_catalog(BASE)

selected = []

for item in items:

    code = item.get("code", "")

    period = parse_period(code)

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

print(
    "\nSelected rasters:",
    len(selected)
)

expected = (
    (END_YEAR - START_YEAR + 1)
    * 36
)

print(
    "Expected approximately:",
    expected
)


rows = []


for i, (item, period) in enumerate(
    selected,
    start=1
):

    code = item["code"]
    url = item.get("downloadUrl")

    if not url:
        print(
            "STOP: missing download URL:",
            code
        )
        break

    outfile = (
        OUTDIR
        / f"{code}_NJValley.tif"
    )

    print(
        f"\n[{i}/{len(selected)}]",
        code
    )

    try:

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

            transform = (
                src.window_transform(
                    window
                )
            )

            scaled_daily = (
                raw.astype("float32")
                * SCALE_FACTOR
            )

            dekad_total = (
                scaled_daily
                * period["days"]
            )

            valid = (
                dekad_total
                .compressed()
            )

            if len(valid) == 0:
                raise RuntimeError(
                    "No valid pixels"
                )

            # Save regional dekadal-total raster.
            if not outfile.exists():

                profile = (
                    src.profile.copy()
                )

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
                        dekad_total.filled(
                            -9999.0
                        ),
                        1
                    )

                    dst.update_tags(
                        variable=(
                            "Actual "
                            "Evapotranspiration "
                            "and Interception"
                        ),
                        units="mm/dekad",
                        source=(
                            "FAO WaPOR v3 "
                            "L2-AETI-D"
                        ),
                        original_scale="0.1",
                        dekad_days=str(
                            period["days"]
                        )
                    )

            rows.append({
                "date":
                    period["date"],

                "year":
                    period["year"],

                "month":
                    period["month"],

                "dekad":
                    period["dekad"],

                "days":
                    period["days"],

                "valid_pixels":
                    len(valid),

                "aeti_mean_mm_dekad":
                    float(
                        valid.mean()
                    ),

                "aeti_median_mm_dekad":
                    float(
                        np.median(valid)
                    ),

                "aeti_min_mm_dekad":
                    float(
                        valid.min()
                    ),

                "aeti_max_mm_dekad":
                    float(
                        valid.max()
                    ),

                "raster":
                    str(outfile)
            })

        print(
            "Mean:",
            round(
                rows[-1][
                    "aeti_mean_mm_dekad"
                ],
                3
            ),
            "mm/dekad"
        )

    except Exception as e:

        print(
            "ERROR:",
            code,
            e
        )

        print(
            "STOPPING so failure "
            "cannot be hidden."
        )

        break

    time.sleep(0.1)


df = pd.DataFrame(rows)

df.to_csv(
    SUMMARY,
    index=False
)

print("\nProcessed:", len(df))
print("Saved:", SUMMARY)

if len(df) == len(selected):
    print(
        "\nPASS: complete AETI "
        "dekadal series"
    )
else:
    print(
        "\nPARTIAL: inspect final "
        "successful raster before retry"
    )
