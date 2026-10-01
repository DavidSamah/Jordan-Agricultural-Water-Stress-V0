from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

WEST = 35.3
SOUTH = 32.0
EAST = 35.8
NORTH = 33.3

url = Path(
    "v1/data/wapor_ret/logs/"
    "ret-test-url.txt"
).read_text().strip()

out = Path(
    "v1/data/wapor_ret/processed/"
    "ret_2018_01_D1_northern_jordan_valley.tif"
)

with rasterio.open(url) as src:

    window = from_bounds(
        WEST,
        SOUTH,
        EAST,
        NORTH,
        src.transform
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
            "STOP: no RET values in study area"
        )

    print("Shape:", data.shape)
    print("Valid pixels:", len(valid))

    print("\nRAW RET")
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

    with rasterio.open(
        out,
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

print("\nSaved:", out)
print("PASS: RET study-area subset")
