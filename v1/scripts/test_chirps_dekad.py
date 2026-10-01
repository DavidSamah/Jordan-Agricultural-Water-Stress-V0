from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

WEST = 35.3
SOUTH = 32.0
EAST = 35.8
NORTH = 33.3

URL = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/"
    "dekads/global/tifs/"
    "chirps-v3.0.2018.01.1.tif"
)

OUT = Path(
    "v1/data/chirps_dekad/processed/"
    "chirps_v3_2018_01_D1_northern_jordan_valley.tif"
)

print("Opening:")
print(URL)

with rasterio.open(URL) as src:

    print("\nSOURCE")
    print("Driver:", src.driver)
    print("CRS:", src.crs)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    print("Dtype:", src.dtypes)
    print("NoData:", src.nodata)
    print("Tags:", src.tags())

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

    transform = src.window_transform(
        window
    )

    valid = data.compressed().astype(float)

    if len(valid) == 0:
        raise SystemExit(
            "STOP: no CHIRPS precipitation pixels"
        )

    print("\nSTUDY AREA")
    print("Shape:", data.shape)
    print("Valid pixels:", len(valid))

    print("\nRAW PRECIPITATION")
    print("Min:", valid.min())
    print("Mean:", valid.mean())
    print("Median:", np.median(valid))
    print("Max:", valid.max())

    profile = src.profile.copy()

    profile.update(
        width=data.shape[1],
        height=data.shape[0],
        transform=transform,
        compress="deflate"
    )

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with rasterio.open(
        OUT,
        "w",
        **profile
    ) as dst:

        dst.write(
            data.filled(src.nodata),
            1
        )

        dst.update_tags(
            **src.tags()
        )

print("\nSaved:", OUT)
print("PASS: CHIRPS v3 dekadal test extraction")
