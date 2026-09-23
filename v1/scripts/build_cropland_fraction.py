from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

WORLD = Path(
    "v1/data/worldcover/processed/"
    "worldcover_2021_northern_jordan_valley.tif"
)

AETI_DIR = Path(
    "v1/data/wapor/processed/aeti_dekad"
)

OUT = Path(
    "v1/data/worldcover/processed/"
    "cropland_fraction_on_wapor_grid.tif"
)

CROPLAND_CLASS = 40

# Use one WaPOR raster as the reference grid.
refs = sorted(AETI_DIR.glob("*.tif"))

if not refs:
    raise SystemExit(
        "STOP: no WaPOR dekadal rasters found"
    )

REFERENCE = refs[0]

print("WorldCover:", WORLD)
print("WaPOR reference:", REFERENCE)

with rasterio.open(WORLD) as wc:
    world = wc.read(1)

    # Official ESA WorldCover:
    # 40 = Cropland
    crop10 = (
        world == CROPLAND_CLASS
    ).astype("float32")

    print(
        "10 m cropland pixels:",
        int(crop10.sum())
    )

    print(
        "10 m total pixels:",
        crop10.size
    )

    print(
        "10 m cropland fraction:",
        float(crop10.mean())
    )

    with rasterio.open(REFERENCE) as ref:

        fraction = np.zeros(
            (ref.height, ref.width),
            dtype="float32"
        )

        reproject(
            source=crop10,
            destination=fraction,

            src_transform=wc.transform,
            src_crs=wc.crs,

            dst_transform=ref.transform,
            dst_crs=ref.crs,

            resampling=Resampling.average
        )

        profile = ref.profile.copy()

        profile.update(
            dtype="float32",
            count=1,
            nodata=-9999.0,
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
                fraction,
                1
            )

            dst.update_tags(
                source="ESA WorldCover 2021 v200",
                source_resolution="10 m",
                source_class="40 = Cropland",
                target_grid="FAO WaPOR L2 AETI",
                interpretation=(
                    "Fraction of each WaPOR pixel "
                    "classified as cropland"
                )
            )

valid = fraction[
    np.isfinite(fraction)
]

print("\n100 m CROPLAND FRACTION")

print("Min:", valid.min())
print("Mean:", valid.mean())
print("Median:", np.median(valid))
print("Max:", valid.max())

print(
    "Pixels > 0% cropland:",
    int((valid > 0).sum())
)

print(
    "Pixels >= 50% cropland:",
    int((valid >= 0.5).sum())
)

print(
    "Pixels >= 90% cropland:",
    int((valid >= 0.9).sum())
)

print("\nSaved:", OUT)
print("PASS: fractional cropland mask created")
