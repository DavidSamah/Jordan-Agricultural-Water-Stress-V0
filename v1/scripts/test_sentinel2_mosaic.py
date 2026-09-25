from pathlib import Path

import numpy as np
import rasterio
from pystac_client import Client
from rasterio.warp import reproject, Resampling

BBOX = [35.3, 32.0, 35.8, 33.3]
DATE = "2018-03-02"

AETI_DIR = Path(
    "v1/data/wapor/processed/aeti_dekad"
)

CROP = Path(
    "v1/data/worldcover/processed/"
    "cropland_fraction_on_wapor_grid.tif"
)

OUT = Path(
    "v1/data/sentinel2/processed/"
    "ndvi_2018_03_02_wapor_grid.tif"
)

refs = sorted(
    AETI_DIR.glob("*.tif")
)

if not refs:
    raise SystemExit(
        "STOP: no WaPOR reference raster"
    )

REFERENCE = refs[0]

catalog = Client.open(
    "https://earth-search.aws.element84.com/v1"
)

items = list(
    catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=BBOX,
        datetime=f"{DATE}/{DATE}"
    ).items()
)

if not items:
    raise SystemExit(
        "STOP: no Sentinel-2 scenes"
    )

print("Scenes found:", len(items))

with rasterio.open(REFERENCE) as ref:
    target_shape = (
        ref.height,
        ref.width
    )
    target_transform = ref.transform
    target_crs = ref.crs
    target_profile = ref.profile.copy()

print("Target CRS:", target_crs)
print("Target shape:", target_shape)

ndvi_sum = np.zeros(
    target_shape,
    dtype="float64"
)

ndvi_count = np.zeros(
    target_shape,
    dtype="uint16"
)

BAD_SCL = {
    0,
    1,
    3,
    8,
    9,
    10,
    11
}

for i, item in enumerate(
    items,
    start=1
):
    print(
        f"\n[{i}/{len(items)}]",
        item.id,
        "cloud=",
        item.properties.get(
            "eo:cloud_cover"
        )
    )

    if not all(
        k in item.assets
        for k in ["red", "nir", "scl"]
    ):
        print("SKIP: missing required assets")
        continue

    red_target = np.full(
        target_shape,
        np.nan,
        dtype="float32"
    )

    with rasterio.open(
        item.assets["red"].href
    ) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=red_target,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear
        )

    nir_target = np.full(
        target_shape,
        np.nan,
        dtype="float32"
    )

    with rasterio.open(
        item.assets["nir"].href
    ) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=nir_target,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear
        )

    scl_target = np.zeros(
        target_shape,
        dtype="uint8"
    )

    with rasterio.open(
        item.assets["scl"].href
    ) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=scl_target,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            dst_nodata=0,
            resampling=Resampling.nearest
        )

    bad = np.isin(
        scl_target,
        list(BAD_SCL)
    )

    denominator = (
        nir_target
        +
        red_target
    )

    valid = (
        ~bad
        &
        np.isfinite(red_target)
        &
        np.isfinite(nir_target)
        &
        (denominator != 0)
    )

    tile_ndvi = np.full(
        target_shape,
        np.nan,
        dtype="float32"
    )

    tile_ndvi[valid] = (
        (
            nir_target[valid]
            -
            red_target[valid]
        )
        /
        denominator[valid]
    )

    physical = (
        valid
        &
        (tile_ndvi >= -1.0)
        &
        (tile_ndvi <= 1.0)
    )

    print(
        "Valid target pixels:",
        int(physical.sum())
    )

    ndvi_sum[physical] += (
        tile_ndvi[physical]
    )

    ndvi_count[physical] += 1

mosaic = np.full(
    target_shape,
    np.nan,
    dtype="float32"
)

covered = ndvi_count > 0

mosaic[covered] = (
    ndvi_sum[covered]
    /
    ndvi_count[covered]
)

print("\nMOSAIC")
print(
    "Covered pixels:",
    int(covered.sum())
)

print(
    "Coverage fraction:",
    float(
        covered.sum()
        /
        mosaic.size
    )
)

if not covered.any():
    raise SystemExit(
        "STOP: mosaic contains no valid pixels"
    )

with rasterio.open(CROP) as src:
    crop = src.read(
        1,
        masked=True
    ).filled(0).astype("float64")

    if crop.shape != target_shape:
        raise RuntimeError(
            "STOP: cropland grid mismatch"
        )

ag_valid = (
    np.isfinite(mosaic)
    &
    (crop > 0)
)

if not ag_valid.any():
    raise SystemExit(
        "STOP: no valid agricultural NDVI"
    )

weights = crop[ag_valid]
values = mosaic[ag_valid]

weighted_ndvi = (
    np.sum(
        values * weights
    )
    /
    np.sum(weights)
)

print("\nAGRICULTURAL NDVI")
print(
    "Mixed cropland pixels:",
    int(ag_valid.sum())
)

print(
    "Crop-equivalent pixel weight:",
    float(weights.sum())
)

print(
    "Weighted NDVI:",
    float(weighted_ndvi)
)

print(
    "Unweighted agricultural mean:",
    float(
        np.mean(values)
    )
)

print(
    "Median:",
    float(
        np.median(values)
    )
)

target_profile.update(
    dtype="float32",
    nodata=-9999.0,
    count=1,
    compress="deflate"
)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

with rasterio.open(
    OUT,
    "w",
    **target_profile
) as dst:
    dst.write(
        np.where(
            np.isfinite(mosaic),
            mosaic,
            -9999.0
        ),
        1
    )

    dst.update_tags(
        variable="NDVI",
        source="Sentinel-2 L2A",
        observation_date=DATE,
        processing=(
            "all intersecting tiles; "
            "SCL masked; mosaicked to WaPOR grid"
        ),
        cropland_weighting=(
            "ESA WorldCover 2021 fractional cropland"
        )
    )

print("\nSaved:", OUT)
print(
    "PASS: multi-tile agricultural NDVI"
)
