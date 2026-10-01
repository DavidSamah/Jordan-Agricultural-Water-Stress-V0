from pathlib import Path
import argparse
import time

import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from pystac_client import Client
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.transform import array_bounds
from rasterio.windows import from_bounds, Window


# ============================================================
# AOI-ONLY REMOTE RASTER READER
# ============================================================

def read_window_to_target(
    href,
    label,
    target_shape,
    target_transform,
    target_crs,
    resampling,
    dtype,
    dst_nodata
):
    """
    Read only the source raster window overlapping the WaPOR
    target grid, then reproject that smaller in-memory array.

    This avoids asking GDAL/Rasterio to warp an entire remote
    Sentinel-2 band for a small study area.
    """

    # --------------------------------------------------------
    # Destination array
    # --------------------------------------------------------

    if np.issubdtype(
        np.dtype(dtype),
        np.floating
    ):
        destination = np.full(
            target_shape,
            dst_nodata,
            dtype=dtype
        )
    else:
        destination = np.full(
            target_shape,
            dst_nodata,
            dtype=dtype
        )

    # --------------------------------------------------------
    # Open remote asset
    # --------------------------------------------------------

    open_t0 = time.perf_counter()

    print(
        f"Opening {label} asset..."
    )

    print(
        f"{label} href scheme:",
        href.split(":", 1)[0]
    )

    with rasterio.Env(
        AWS_NO_SIGN_REQUEST="YES"
    ):
        with rasterio.open(href) as src:

            print(
                f"{label} open:",
                f"{time.perf_counter() - open_t0:.2f}s"
            )

            # ----------------------------------------------------
            # Exact WaPOR target bounds
            # ----------------------------------------------------

            dst_bounds = array_bounds(
                target_shape[0],
                target_shape[1],
                target_transform
            )

            # ----------------------------------------------------
            # Convert those bounds to Sentinel source CRS
            # ----------------------------------------------------

            src_bounds = transform_bounds(
                target_crs,
                src.crs,
                *dst_bounds,
                densify_pts=21
            )

            # ----------------------------------------------------
            # Convert geographic bounds to source pixel window
            # ----------------------------------------------------

            raw_window = from_bounds(
                *src_bounds,
                transform=src.transform
            )

            # Add a 2-pixel halo.
            #
            # This is useful for bilinear interpolation because
            # pixels immediately outside the nominal AOI can
            # contribute at the boundary.
            # ----------------------------------------------------

            col_start = max(
                0,
                int(
                    np.floor(
                        raw_window.col_off
                    )
                ) - 2
            )

            row_start = max(
                0,
                int(
                    np.floor(
                        raw_window.row_off
                    )
                ) - 2
            )

            col_stop = min(
                src.width,
                int(
                    np.ceil(
                        raw_window.col_off
                        +
                        raw_window.width
                    )
                ) + 2
            )

            row_stop = min(
                src.height,
                int(
                    np.ceil(
                        raw_window.row_off
                        +
                        raw_window.height
                    )
                ) + 2
            )

            # ----------------------------------------------------
            # Scene does not overlap WaPOR target
            # ----------------------------------------------------

            if (
                col_stop <= col_start
                or
                row_stop <= row_start
            ):
                print(
                    f"{label}: no overlap "
                    "with target grid"
                )

                return destination

            window = Window(
                col_start,
                row_start,
                col_stop - col_start,
                row_stop - row_start
            )

            # ----------------------------------------------------
            # Remote read: only required source pixels
            # ----------------------------------------------------

            read_t0 = time.perf_counter()

            # ----------------------------------------------------
            # REDUCED-RESOLUTION REMOTE READ
            #
            # The final WaPOR grid is only 1331 x 512.
            # Reading the complete 10 m Sentinel window can require
            # tens of millions of pixels per band.
            #
            # Read at approximately 2x destination resolution.
            # This preserves an intermediate oversampling margin
            # before the final warp.
            # ----------------------------------------------------

            oversample = 2

            out_height = min(
                int(np.ceil(window.height)),
                int(target_shape[0] * oversample)
            )

            out_width = min(
                int(np.ceil(window.width)),
                int(target_shape[1] * oversample)
            )

            out_height = max(
                1,
                out_height
            )

            out_width = max(
                1,
                out_width
            )

            source = None
            read_error = None

            for read_attempt in range(1, 6):

                try:

                    source = src.read(
                        1,
                        window=window,
                        out_shape=(
                            out_height,
                            out_width
                        ),
                        masked=True,
                        resampling=resampling
                    )

                    if read_attempt > 1:
                        print(
                            f"{label} read recovered "
                            f"on attempt {read_attempt}/5"
                        )

                    break

                except rasterio.errors.RasterioIOError as e:

                    read_error = e

                    print(
                        f"{label} raster read error "
                        f"attempt {read_attempt}/5:",
                        type(e).__name__
                    )

                    if read_attempt < 5:

                        delay = 2 ** read_attempt

                        print(
                            f"Retrying {label} read "
                            f"after {delay} seconds..."
                        )

                        time.sleep(delay)

            if source is None:
                raise read_error

            # ----------------------------------------------------
            # Adjust transform for the reduced-resolution array
            # ----------------------------------------------------

            native_window_transform = (
                src.window_transform(window)
            )

            scale_x = (
                float(window.width)
                /
                float(out_width)
            )

            scale_y = (
                float(window.height)
                /
                float(out_height)
            )

            reduced_transform = (
                native_window_transform
                *
                Affine.scale(
                    scale_x,
                    scale_y
                )
            )

            print(
                f"{label} requested window:",
                f"{int(np.ceil(window.height))}x"
                f"{int(np.ceil(window.width))}"
            )

            print(
                f"{label} reduced read:",
                f"{source.shape[0]}x"
                f"{source.shape[1]}",
                f"(full raster "
                f"{src.height}x{src.width})"
            )

            print(
                f"{label} reduced window read:",
                f"{time.perf_counter() - read_t0:.2f}s"
            )

            # ----------------------------------------------------
            # Preserve appropriate nodata behaviour
            # ----------------------------------------------------

            if np.issubdtype(
                np.dtype(dtype),
                np.floating
            ):
                source = (
                    source
                    .astype(dtype)
                    .filled(np.nan)
                )

                src_nodata = np.nan

            else:
                source = (
                    source
                    .filled(dst_nodata)
                    .astype(dtype)
                )

                src_nodata = dst_nodata

            # ----------------------------------------------------
            # Warp SMALL LOCAL ARRAY -> WaPOR grid
            # ----------------------------------------------------

            warp_t0 = time.perf_counter()

            reproject(
                source=source,
                destination=destination,

                src_transform=reduced_transform,
                src_crs=src.crs,
                src_nodata=src_nodata,

                dst_transform=target_transform,
                dst_crs=target_crs,
                dst_nodata=dst_nodata,

                resampling=resampling
            )

            print(
                f"{label} local warp:",
                f"{time.perf_counter() - warp_t0:.2f}s"
            )
    return destination



# ============================================================
# STEP 5D
# Convert Sentinel-2 acquisition dates into agricultural NDVI
# observations.
# ============================================================

BBOX = [35.3, 32.0, 35.8, 33.3]

LEDGER = Path(
    "v1/data/sentinel2/"
    "sentinel2_observation_ledger.csv"
)

AETI_DIR = Path(
    "v1/data/wapor/processed/aeti_dekad"
)

CROP = Path(
    "v1/data/worldcover/processed/"
    "cropland_fraction_on_wapor_grid.tif"
)

OUT = Path(
    "v1/data/sentinel2/"
    "agricultural_ndvi_observations.csv"
)


# ------------------------------------------------------------
# Optional test limit
# ------------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--limit",
    type=int,
    default=None,
    help="Process only the first N acquisition dates"
)


parser.add_argument(
    "--resume",
    action="store_true",
    help="Skip acquisition dates already saved in output"
)

args = parser.parse_args()


# ------------------------------------------------------------
# 1. Load observation ledger
# ------------------------------------------------------------

if not LEDGER.exists():
    raise SystemExit(
        f"STOP: ledger missing: {LEDGER}"
    )

ledger = pd.read_csv(LEDGER)

ledger["date"] = pd.to_datetime(
    ledger["date"]
)

dates = (
    ledger["date"]
    .drop_duplicates()
    .sort_values()
    .tolist()
)

if args.limit is not None:
    dates = dates[:args.limit]

existing = pd.DataFrame()

if args.resume and OUT.exists():

    existing = pd.read_csv(
        OUT
    )

    if len(existing):

        completed_dates = set(
            pd.to_datetime(
                existing["date"]
            )
            .dt.strftime("%Y-%m-%d")
        )

        before = len(dates)

        dates = [
            d for d in dates
            if pd.Timestamp(d).strftime("%Y-%m-%d")
            not in completed_dates
        ]

        print(
            "Already completed:",
            before - len(dates)
        )

print(
    "Acquisition dates to process:",
    len(dates)
)


# ------------------------------------------------------------
# 2. Establish common WaPOR grid
# ------------------------------------------------------------

references = sorted(
    AETI_DIR.glob("*.tif")
)

if not references:
    raise SystemExit(
        "STOP: no WaPOR AETI reference raster found"
    )

REFERENCE = references[0]

with rasterio.open(REFERENCE) as ref:

    target_shape = (
        ref.height,
        ref.width
    )

    target_transform = ref.transform
    target_crs = ref.crs

print(
    "WaPOR reference:",
    REFERENCE
)

print(
    "Target shape:",
    target_shape
)

print(
    "Target CRS:",
    target_crs
)


# ------------------------------------------------------------
# 3. Load cropland fraction
# ------------------------------------------------------------

if not CROP.exists():
    raise SystemExit(
        f"STOP: cropland raster missing: {CROP}"
    )

with rasterio.open(CROP) as src:

    crop = (
        src.read(
            1,
            masked=True
        )
        .filled(0)
        .astype("float64")
    )

    crop_transform = src.transform
    crop_crs = src.crs


if crop.shape != target_shape:
    raise RuntimeError(
        "STOP: cropland raster shape does not "
        "match WaPOR target grid"
    )

if crop_crs != target_crs:
    raise RuntimeError(
        "STOP: cropland CRS does not match WaPOR CRS"
    )

if not crop_transform.almost_equals(
    target_transform
):
    raise RuntimeError(
        "STOP: cropland transform does not "
        "match WaPOR grid"
    )


# ------------------------------------------------------------
# 4. Connect to Sentinel-2 catalog
# ------------------------------------------------------------

catalog = Client.open(
    "https://earth-search.aws.element84.com/v1"
)


# Sentinel-2 Scene Classification classes excluded.
BAD_SCL = {
    0,   # no data
    1,   # saturated / defective
    3,   # cloud shadow
    8,   # medium probability cloud
    9,   # high probability cloud
    10,  # cirrus
    11,  # snow / ice
}


def get_items_with_retry(
    catalog,
    date_string,
    attempts=6
):
    last_error = None

    for attempt in range(
        1,
        attempts + 1
    ):

        try:

            print(
                f"STAC attempt {attempt}/{attempts}"
            )

            return list(
                catalog.search(
                    collections=[
                        "sentinel-2-l2a"
                    ],
                    bbox=BBOX,
                    datetime=(
                        f"{date_string}/"
                        f"{date_string}"
                    )
                ).items()
            )

        except Exception as exc:

            last_error = exc

            print(
                "STAC connection error:",
                type(exc).__name__
            )

            if attempt == attempts:
                break

            delay = min(
                2 ** attempt,
                30
            )

            print(
                f"Retrying after {delay} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError(
        f"STAC request failed after "
        f"{attempts} attempts for "
        f"{date_string}: {last_error}"
    )


results = []


# ------------------------------------------------------------
# 5. Process each actual acquisition date
# ------------------------------------------------------------

for index, date in enumerate(
    dates,
    start=1
):

    timestamp = pd.Timestamp(date)

    date_string = timestamp.strftime(
        "%Y-%m-%d"
    )

    print()
    print("=" * 70)

    print(
        f"[{index}/{len(dates)}]",
        date_string
    )


    # --------------------------------------------------------
    # Retrieve all scenes intersecting study region that day
    # --------------------------------------------------------

    items = get_items_with_retry(
        catalog,
        date_string
    )

    print(
        "Scenes:",
        len(items)
    )

    if not items:

        print(
            "SKIP: no scenes returned"
        )

        continue


    # --------------------------------------------------------
    # Arrays used to combine overlapping Sentinel tiles
    # --------------------------------------------------------

    ndvi_sum = np.zeros(
        target_shape,
        dtype="float64"
    )

    ndvi_count = np.zeros(
        target_shape,
        dtype="uint16"
    )


    usable_scenes = 0


    for item in items:

        if not all(
            key in item.assets
            for key in [
                "red",
                "nir",
                "scl"
            ]
        ):

            print(
                "SKIP scene:",
                item.id,
                "missing RED/NIR/SCL"
            )

            continue


        # ----------------------------------------------------
        # RED → WaPOR grid
        # ----------------------------------------------------

        red = read_window_to_target(
            href=item.assets["red"].href,
            label="RED",
            target_shape=target_shape,
            target_transform=target_transform,
            target_crs=target_crs,
            resampling=Resampling.bilinear,
            dtype="float32",
            dst_nodata=np.nan
        )


        # ----------------------------------------------------
        # NIR -> WaPOR grid
        # AOI-only remote read
        # ----------------------------------------------------

        nir = read_window_to_target(
            href=item.assets["nir"].href,
            label="NIR",
            target_shape=target_shape,
            target_transform=target_transform,
            target_crs=target_crs,
            resampling=Resampling.bilinear,
            dtype="float32",
            dst_nodata=np.nan
        )


        # ----------------------------------------------------
        # SCL -> WaPOR grid
        # AOI-only remote read
        #
        # IMPORTANT:
        # SCL remains NEAREST-neighbour because SCL contains
        # categorical class labels.
        # ----------------------------------------------------

        scl = read_window_to_target(
            href=item.assets["scl"].href,
            label="SCL",
            target_shape=target_shape,
            target_transform=target_transform,
            target_crs=target_crs,
            resampling=Resampling.nearest,
            dtype="uint8",
            dst_nodata=0
        )


        # Quality filtering
        # ----------------------------------------------------

        bad = np.isin(
            scl,
            list(BAD_SCL)
        )

        denominator = (
            nir
            +
            red
        )

        valid = (
            ~bad
            &
            np.isfinite(red)
            &
            np.isfinite(nir)
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
                nir[valid]
                -
                red[valid]
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


        valid_pixels = int(
            physical.sum()
        )

        if valid_pixels == 0:
            continue


        usable_scenes += 1

        ndvi_sum[physical] += (
            tile_ndvi[physical]
        )

        ndvi_count[physical] += 1


    # --------------------------------------------------------
    # 6. Construct daily multi-tile mosaic
    # --------------------------------------------------------

    covered = (
        ndvi_count > 0
    )

    covered_pixels = int(
        covered.sum()
    )

    if covered_pixels == 0:

        print(
            "SKIP: no valid pixels after masking"
        )

        continue


    coverage_fraction = (
        covered_pixels
        /
        covered.size
    )


    mosaic = np.full(
        target_shape,
        np.nan,
        dtype="float32"
    )

    mosaic[covered] = (
        ndvi_sum[covered]
        /
        ndvi_count[covered]
    )


    # --------------------------------------------------------
    # 7. Restrict result to cropland
    # --------------------------------------------------------

    agricultural = (
        np.isfinite(mosaic)
        &
        (crop > 0)
    )


    agricultural_pixels = int(
        agricultural.sum()
    )


    if agricultural_pixels == 0:

        print(
            "SKIP: no valid agricultural pixels"
        )

        continue


    values = mosaic[
        agricultural
    ]

    weights = crop[
        agricultural
    ]


    crop_equivalent_weight = float(
        weights.sum()
    )


    if crop_equivalent_weight <= 0:

        print(
            "SKIP: zero cropland weight"
        )

        continue


    weighted_ndvi = float(
        np.sum(
            values
            *
            weights
        )
        /
        crop_equivalent_weight
    )


    # --------------------------------------------------------
    # 8. Assign observation to dekad
    # --------------------------------------------------------

    if timestamp.day <= 10:
        dekad = 1

    elif timestamp.day <= 20:
        dekad = 2

    else:
        dekad = 3


    print(
        "Usable scenes:",
        usable_scenes
    )

    print(
        "Coverage:",
        round(
            coverage_fraction,
            4
        )
    )

    print(
        "Agricultural pixels:",
        agricultural_pixels
    )

    print(
        "Weighted NDVI:",
        round(
            weighted_ndvi,
            5
        )
    )


    results.append({

        "date":
            date_string,

        "year":
            timestamp.year,

        "month":
            timestamp.month,

        "dekad":
            dekad,

        "scene_count":
            len(items),

        "usable_scene_count":
            usable_scenes,

        "coverage_fraction":
            coverage_fraction,

        "valid_pixels":
            covered_pixels,

        "agricultural_pixels":
            agricultural_pixels,

        "crop_equivalent_weight":
            crop_equivalent_weight,

        "agricultural_ndvi_weighted":
            weighted_ndvi,

        "agricultural_ndvi_mean":
            float(
                values.mean()
            ),

        "agricultural_ndvi_median":
            float(
                np.median(values)
            ),
    })


    # --------------------------------------------------------
    # CHECKPOINT
    # --------------------------------------------------------

    current = pd.DataFrame(
        results
    )

    if (
        args.resume
        and len(existing)
    ):

        current = pd.concat(
            [
                existing,
                current
            ],
            ignore_index=True
        )

        current = (
            current
            .drop_duplicates(
                subset=["date"],
                keep="last"
            )
            .sort_values("date")
        )

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    current.to_csv(
        OUT,
        index=False
    )

    print(
        "Checkpoint saved:",
        len(current),
        "dates"
    )


# ------------------------------------------------------------
# 9. Save observation-level table
# ------------------------------------------------------------

result_df = pd.DataFrame(
    results
)

if (
    args.resume
    and len(existing)
):

    result_df = pd.concat(
        [
            existing,
            result_df
        ],
        ignore_index=True
    )

    result_df = (
        result_df
        .drop_duplicates(
            subset=["date"],
            keep="last"
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


if len(result_df) == 0:

    raise RuntimeError(
        "STOP: no NDVI observations were produced"
    )


if not result_df[
    "agricultural_ndvi_weighted"
].between(
    -1,
    1
).all():

    raise RuntimeError(
        "STOP: agricultural NDVI outside "
        "physical range"
    )


OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

result_df.to_csv(
    OUT,
    index=False
)


print()
print("=" * 70)

print(
    "Dates successfully processed:",
    len(result_df)
)

print(
    "NDVI range:",
    result_df[
        "agricultural_ndvi_weighted"
    ].min(),
    "to",
    result_df[
        "agricultural_ndvi_weighted"
    ].max()
)

print(
    "Saved:",
    OUT
)

print(
    "\nPASS: agricultural NDVI "
    "observation series created"
)
