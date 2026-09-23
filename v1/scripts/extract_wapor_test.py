import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import array_bounds
import numpy as np
from pathlib import Path

url = Path(
    "v1/data/wapor/logs/aeti-test-url.txt"
).read_text().strip()

# Provisional Northern Jordan Valley box
WEST = 35.3
SOUTH = 32.0
EAST = 35.8
NORTH = 33.3

out = Path(
    "v1/data/wapor/processed/"
    "aeti_2018_01_D1_northern_jordan_valley.tif"
)

with rasterio.open(url) as src:

    print("SOURCE CRS:", src.crs)
    print("SOURCE NODATA:", src.nodata)
    print("SOURCE DTYPES:", src.dtypes)
    print("SOURCE TAGS:")
    print(src.tags())

    window = from_bounds(
        WEST,
        SOUTH,
        EAST,
        NORTH,
        transform=src.transform
    )

    window = window.round_offsets().round_lengths()

    data = src.read(
        1,
        window=window,
        masked=True
    )

    transform = src.window_transform(window)

    profile = src.profile.copy()

    profile.update(
        width=data.shape[1],
        height=data.shape[0],
        transform=transform,
        compress="deflate"
    )

    with rasterio.open(out, "w", **profile) as dst:
        dst.write(data.filled(src.nodata), 1)

        # Preserve metadata
        dst.update_tags(**src.tags())

    valid = data.compressed().astype(float)

    print("\nWINDOW SHAPE:", data.shape)
    print("VALID PIXELS:", len(valid))
    print("MASKED PIXELS:", int(data.mask.sum()))

    if len(valid) == 0:
        raise SystemExit(
            "STOP: no valid AETI pixels in study area"
        )

    print("\nRAW AETI STATISTICS")
    print("Min:", valid.min())
    print("Mean:", valid.mean())
    print("Median:", np.median(valid))
    print("Max:", valid.max())

    print("\nOUTPUT BOUNDS:")
    print(array_bounds(
        data.shape[0],
        data.shape[1],
        transform
    ))

print("\nSaved:", out)
print("PASS: WaPOR study-area subset created")
