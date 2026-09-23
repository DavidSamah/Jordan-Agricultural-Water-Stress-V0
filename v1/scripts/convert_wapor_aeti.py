import rasterio
import numpy as np
import pandas as pd
from pathlib import Path

SRC = Path(
    "v1/data/wapor/processed/"
    "aeti_2018_01_D1_northern_jordan_valley.tif"
)

OUT = Path(
    "v1/data/wapor/processed/"
    "aeti_2018_01_D1_northern_jordan_valley_scaled.tif"
)

CSV = Path(
    "v1/data/wapor/processed/"
    "aeti_2018_01_D1_statistics.csv"
)

SCALE_FACTOR = 0.1
DEKAD_DAYS = 10

with rasterio.open(SRC) as src:
    raw = src.read(1, masked=True)

    profile = src.profile.copy()

    scaled = raw.astype("float32") * SCALE_FACTOR

    profile.update(
        dtype="float32",
        nodata=-9999.0,
        compress="deflate"
    )

    with rasterio.open(OUT, "w", **profile) as dst:
        dst.write(
            scaled.filled(-9999.0),
            1
        )

        dst.update_tags(
            variable="Actual Evapotranspiration and Interception",
            units="mm/day",
            scale_applied="0.1",
            temporal_resolution="dekadal",
            dekad_days=str(DEKAD_DAYS),
            source="FAO WaPOR v3 L2-AETI-D"
        )

    valid = scaled.compressed()

    daily_mean = float(valid.mean())
    dekad_total_mean = daily_mean * DEKAD_DAYS

    stats = pd.DataFrame([{
        "period": "2018-01-D1",
        "valid_pixels": len(valid),
        "aeti_min_mm_day": float(valid.min()),
        "aeti_mean_mm_day": daily_mean,
        "aeti_median_mm_day": float(np.median(valid)),
        "aeti_max_mm_day": float(valid.max()),
        "regional_mean_dekad_total_mm": dekad_total_mean
    }])

    stats.to_csv(CSV, index=False)

    print(stats.to_string(index=False))

print("\nSaved scaled raster:")
print(OUT)

print("\nSaved statistics:")
print(CSV)

print("\nPASS: physical AETI conversion complete")
