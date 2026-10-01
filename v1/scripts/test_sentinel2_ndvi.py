from pathlib import Path

import numpy as np
import rasterio
from pystac_client import Client
from rasterio.warp import (
    reproject,
    Resampling,
    transform_bounds,
)
from rasterio.windows import from_bounds

WGS84_BBOX = [35.3, 32.0, 35.8, 33.3]

TARGET_ID = "S2B_37SBS_20180302_0_L2A"

catalog = Client.open(
    "https://earth-search.aws.element84.com/v1"
)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=WGS84_BBOX,
    datetime="2018-03-02/2018-03-02"
)

items = list(search.items())

item = next(
    (
        x for x in items
        if x.id == TARGET_ID
    ),
    None
)

if item is None:
    raise SystemExit(
        f"STOP: target scene not found: {TARGET_ID}"
    )

print("Scene:", item.id)
print("Datetime:", item.datetime)
print(
    "Cloud cover:",
    item.properties.get("eo:cloud_cover")
)

for required in ["red", "nir", "scl"]:
    if required not in item.assets:
        raise SystemExit(
            f"STOP: missing asset {required}"
        )

red_url = item.assets["red"].href
nir_url = item.assets["nir"].href
scl_url = item.assets["scl"].href


# --------------------------------------------------
# RED — establish actual tile intersection
# --------------------------------------------------

with rasterio.open(red_url) as red_src:

    print("\nRED CRS:", red_src.crs)
    print("RED resolution:", red_src.res)
    print("RED bounds:", red_src.bounds)

    requested = transform_bounds(
        "EPSG:4326",
        red_src.crs,
        *WGS84_BBOX,
        densify_pts=21
    )

    print(
        "\nRequested projected bounds:",
        requested
    )

    req_w, req_s, req_e, req_n = requested

    # Clip requested study area to this Sentinel tile.
    west = max(
        req_w,
        red_src.bounds.left
    )

    south = max(
        req_s,
        red_src.bounds.bottom
    )

    east = min(
        req_e,
        red_src.bounds.right
    )

    north = min(
        req_n,
        red_src.bounds.top
    )

    print(
        "Actual tile intersection:",
        (west, south, east, north)
    )

    if (
        west >= east
        or south >= north
    ):
        raise SystemExit(
            "STOP: scene does not intersect study area"
        )

    window = from_bounds(
        west,
        south,
        east,
        north,
        transform=red_src.transform
    )

    window = (
        window
        .round_offsets()
        .round_lengths()
    )

    print("\nClipped window:", window)

    red = red_src.read(
        1,
        window=window,
        masked=True
    ).astype("float32")

    target_transform = (
        red_src.window_transform(window)
    )

    target_crs = red_src.crs
    target_shape = red.shape

    profile = red_src.profile.copy()


print(
    "Target shape:",
    target_shape
)

if (
    target_shape[0] == 0
    or target_shape[1] == 0
):
    raise RuntimeError(
        "STOP: empty RED intersection"
    )


# --------------------------------------------------
# NIR — reproject directly to RED target grid
# --------------------------------------------------

nir_target = np.full(
    target_shape,
    np.nan,
    dtype="float32"
)

with rasterio.open(nir_url) as nir_src:

    reproject(
        source=rasterio.band(
            nir_src,
            1
        ),

        destination=nir_target,

        src_transform=nir_src.transform,
        src_crs=nir_src.crs,

        dst_transform=target_transform,
        dst_crs=target_crs,

        dst_nodata=np.nan,

        resampling=Resampling.bilinear
    )


# --------------------------------------------------
# SCL — reproject onto exactly same grid
# --------------------------------------------------

scl = np.zeros(
    target_shape,
    dtype="uint8"
)

with rasterio.open(scl_url) as scl_src:

    print(
        "SCL resolution:",
        scl_src.res
    )

    reproject(
        source=rasterio.band(
            scl_src,
            1
        ),

        destination=scl,

        src_transform=scl_src.transform,
        src_crs=scl_src.crs,

        dst_transform=target_transform,
        dst_crs=target_crs,

        dst_nodata=0,

        resampling=Resampling.nearest
    )


# --------------------------------------------------
# CLOUD / QUALITY MASK
# --------------------------------------------------

BAD_SCL = {
    0,   # no data
    1,   # saturated / defective
    3,   # cloud shadow
    8,   # medium cloud
    9,   # high cloud
    10,  # thin cirrus
    11,  # snow / ice
}

bad = np.isin(
    scl,
    list(BAD_SCL)
)

red_data = red.filled(
    np.nan
).astype("float32")

nir_data = nir_target

denominator = (
    nir_data
    +
    red_data
)

valid = (
    ~bad
    &
    np.isfinite(red_data)
    &
    np.isfinite(nir_data)
    &
    (denominator != 0)
)


print(
    "\nValid RED:",
    int(np.isfinite(red_data).sum())
)

print(
    "Valid NIR:",
    int(np.isfinite(nir_data).sum())
)

print(
    "Good SCL:",
    int((~bad).sum())
)

print(
    "Combined valid:",
    int(valid.sum())
)


ndvi = np.full(
    target_shape,
    np.nan,
    dtype="float32"
)

ndvi[valid] = (
    (
        nir_data[valid]
        -
        red_data[valid]
    )
    /
    denominator[valid]
)

values = ndvi[
    np.isfinite(ndvi)
]

if len(values) == 0:
    raise SystemExit(
        "STOP: no valid NDVI after intersection"
    )


print("\nNDVI")

print("Valid pixels:", len(values))

print(
    "Valid fraction:",
    len(values) / ndvi.size
)

print("Min:", float(values.min()))
print("Mean:", float(values.mean()))
print(
    "Median:",
    float(np.median(values))
)
print("Max:", float(values.max()))


if values.min() < -1.01:
    raise RuntimeError(
        "NDVI below valid range"
    )

if values.max() > 1.01:
    raise RuntimeError(
        "NDVI above valid range"
    )


# --------------------------------------------------
# SAVE
# --------------------------------------------------

out = Path(
    "v1/data/sentinel2/processed/"
    "ndvi_2018_03_02_37SBS.tif"
)

out.parent.mkdir(
    parents=True,
    exist_ok=True
)

profile.update(
    dtype="float32",
    nodata=-9999.0,
    count=1,
    height=target_shape[0],
    width=target_shape[1],
    transform=target_transform,
    compress="deflate"
)

with rasterio.open(
    out,
    "w",
    **profile
) as dst:

    dst.write(
        np.where(
            np.isfinite(ndvi),
            ndvi,
            -9999.0
        ),
        1
    )

    dst.update_tags(
        variable="NDVI",
        source="Sentinel-2 L2A",
        scene_id=item.id,
        observation_date="2018-03-02",
        formula="(NIR-RED)/(NIR+RED)",
        cloud_mask="SCL",
        processing="study-area/tile intersection only"
    )

print("\nSaved:", out)
print(
    "PASS: tile-intersection NDVI extraction"
)
