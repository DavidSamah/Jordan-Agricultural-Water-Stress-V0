import re
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

AETI_DIR = Path(
    "v1/data/wapor/processed/"
    "aeti_dekad"
)

CROP_FILE = Path(
    "v1/data/worldcover/processed/"
    "cropland_fraction_on_wapor_grid.tif"
)

OUT = Path(
    "v1/data/wapor/processed/"
    "agricultural_aeti_2018_2024_dekadal.csv"
)

with rasterio.open(CROP_FILE) as src:
    crop = src.read(
        1,
        masked=True
    ).filled(0).astype("float64")

if crop.max() > 1.0001:
    raise RuntimeError(
        "Cropland fractions exceed 1"
    )

if crop.min() < 0:
    raise RuntimeError(
        "Negative cropland fractions"
    )

files = sorted(
    AETI_DIR.glob("*.tif")
)

if not files:
    raise SystemExit(
        "STOP: no AETI rasters"
    )

rows = []

pattern = re.compile(
    r"(\d{4})-(\d{2})-D([123])"
)

for i, path in enumerate(
    files,
    start=1
):

    match = pattern.search(
        path.name
    )

    if match is None:
        print(
            "SKIP:",
            path.name
        )
        continue

    year = int(match.group(1))
    month = int(match.group(2))
    dekad = int(match.group(3))

    with rasterio.open(path) as src:

        aeti = src.read(
            1,
            masked=True
        )

        if aeti.shape != crop.shape:
            raise RuntimeError(
                f"Grid mismatch: {path}"
            )

        values = aeti.filled(
            np.nan
        ).astype("float64")

    # Valid AETI and at least some cropland.
    valid = (
        np.isfinite(values)
        & (crop > 0)
    )

    if not valid.any():
        raise RuntimeError(
            f"No agricultural pixels: {path}"
        )

    weights = crop[valid]
    vals = values[valid]

    # Fractionally weighted agricultural mean.
    weighted_mean = (
        np.sum(
            vals * weights
        )
        /
        np.sum(weights)
    )

    # Diagnostic binary masks.
    crop50 = valid & (
        crop >= 0.50
    )

    crop90 = valid & (
        crop >= 0.90
    )

    mean50 = (
        float(
            np.nanmean(
                values[crop50]
            )
        )
        if crop50.any()
        else np.nan
    )

    mean90 = (
        float(
            np.nanmean(
                values[crop90]
            )
        )
        if crop90.any()
        else np.nan
    )

    rows.append({
        "year": year,
        "month": month,
        "dekad": dekad,

        "agricultural_aeti_weighted_mm":
            float(weighted_mean),

        "aeti_crop50_mm":
            mean50,

        "aeti_crop90_mm":
            mean90,

        "mixed_agricultural_pixels":
            int(valid.sum()),

        "crop_equivalent_pixel_weight":
            float(weights.sum())
    })

    print(
        f"[{i}/{len(files)}]",
        year,
        month,
        f"D{dekad}",
        "weighted AETI =",
        round(
            weighted_mean,
            3
        ),
        "mm"
    )

df = pd.DataFrame(rows)

df = df.sort_values(
    ["year", "month", "dekad"]
)

df.to_csv(
    OUT,
    index=False
)

print("\nRows:", len(df))

print(
    "Null weighted AETI:",
    df[
        "agricultural_aeti_weighted_mm"
    ].isna().sum()
)

print("\nSaved:", OUT)

print(
    "\nPASS: agricultural AETI "
    "time series created"
)
