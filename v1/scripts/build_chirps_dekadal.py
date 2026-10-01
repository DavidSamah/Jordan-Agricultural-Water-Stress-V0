import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds

START_YEAR = 2018
END_YEAR = 2024

WEST = 35.3
SOUTH = 32.0
EAST = 35.8
NORTH = 33.3

BASE = (
    "https://data.chc.ucsb.edu/products/"
    "CHIRPS/v3.0/dekads/global/tifs"
)

OUTDIR = Path(
    "v1/data/chirps_dekad/processed/rasters"
)

OUTCSV = Path(
    "v1/data/chirps_dekad/processed/"
    "chirps_2018_2024_dekadal.csv"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

rows = []

for year in range(
    START_YEAR,
    END_YEAR + 1
):

    for month in range(1, 13):

        month_days = calendar.monthrange(
            year,
            month
        )[1]

        for dekad in [1, 2, 3]:

            if dekad == 1:
                days = 10
                start_day = 1

            elif dekad == 2:
                days = 10
                start_day = 11

            else:
                days = month_days - 20
                start_day = 21

            url = (
                f"{BASE}/"
                f"chirps-v3.0."
                f"{year}."
                f"{month:02d}."
                f"{dekad}.tif"
            )

            print(
                f"{year}-{month:02d}-D{dekad}"
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

                data = src.read(
                    1,
                    window=window,
                    masked=True
                )

                valid = (
                    data
                    .compressed()
                    .astype(float)
                )

                if len(valid) == 0:
                    raise RuntimeError(
                        f"No CHIRPS data: {url}"
                    )

                transform = (
                    src.window_transform(
                        window
                    )
                )

                outfile = (
                    OUTDIR
                    /
                    (
                        f"chirps-v3.0."
                        f"{year}."
                        f"{month:02d}."
                        f"{dekad}_NJValley.tif"
                    )
                )

                profile = src.profile.copy()

                profile.update(
                    width=data.shape[1],
                    height=data.shape[0],
                    transform=transform,
                    compress="deflate"
                )

                with rasterio.open(
                    outfile,
                    "w",
                    **profile
                ) as dst:

                    dst.write(
                        data.filled(
                            src.nodata
                        ),
                        1
                    )

            rows.append({
                "date":
                    pd.Timestamp(
                        year=year,
                        month=month,
                        day=start_day
                    ),

                "year":
                    year,

                "month":
                    month,

                "dekad":
                    dekad,

                "days":
                    days,

                "precipitation_mean_mm":
                    float(
                        valid.mean()
                    ),

                "precipitation_median_mm":
                    float(
                        np.median(valid)
                    ),

                "precipitation_min_mm":
                    float(
                        valid.min()
                    ),

                "precipitation_max_mm":
                    float(
                        valid.max()
                    ),

                "valid_pixels":
                    len(valid)
            })

            print(
                "Mean rain:",
                round(
                    valid.mean(),
                    3
                ),
                "mm"
            )

df = pd.DataFrame(rows)

df.to_csv(
    OUTCSV,
    index=False
)

print("\nRows:", len(df))

print(
    "Null rainfall:",
    df[
        "precipitation_mean_mm"
    ].isna().sum()
)

print("\nSaved:", OUTCSV)

if len(df) == 252:
    print(
        "\nPASS: complete CHIRPS "
        "dekadal series"
    )
else:
    print(
        "\nCHECK: expected 252 periods"
    )
