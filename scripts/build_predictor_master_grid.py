from pathlib import Path
import pandas as pd


BASE = Path("v1/data")

CHIRPS = BASE / (
    "chirps_dekad/processed/"
    "chirps_2018_2024_dekadal.csv"
)

ERA5 = BASE / (
    "era5land/processed/"
    "era5land_2018_2024_dekadal.csv"
)

AETI = BASE / (
    "wapor/processed/"
    "agricultural_aeti_2018_2024_dekadal.csv"
)

RET = BASE / (
    "wapor_ret/processed/"
    "ret_2018_2024_dekadal.csv"
)

NDVI = BASE / (
    "sentinel2/"
    "agricultural_ndvi_dekadal_final.csv"
)

OUTPUT = BASE / (
    "processed_v2/"
    "predictor_alignment_dekadal.csv"
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)


KEY = [
    "year",
    "month",
    "dekad",
]


# ---------------------------------------------------------
# 1. Load
# ---------------------------------------------------------

chirps = pd.read_csv(CHIRPS)
era5 = pd.read_csv(ERA5)
aeti = pd.read_csv(AETI)
ret = pd.read_csv(RET)
ndvi = pd.read_csv(NDVI)


print("=" * 72)
print("DEKADAL FEATURE ALIGNMENT")
print("=" * 72)


for name, df in [
    ("CHIRPS", chirps),
    ("ERA5-Land", era5),
    ("AETI", aeti),
    ("RET", ret),
    ("NDVI", ndvi),
]:

    duplicates = df.duplicated(
        KEY
    ).sum()

    print(
        name,
        "rows =",
        len(df),
        "duplicate keys =",
        duplicates,
    )

    if duplicates:
        raise RuntimeError(
            f"{name}: duplicate dekadal keys"
        )


# ---------------------------------------------------------
# 2. Start with the complete temporal grid
# ---------------------------------------------------------

master = chirps[
    [
        "date",
        "year",
        "month",
        "dekad",
        "days",
        "precipitation_mean_mm",
        "precipitation_median_mm",
        "precipitation_min_mm",
        "precipitation_max_mm",
        "valid_pixels",
    ]
].copy()

master = master.rename(
    columns={
        "valid_pixels":
            "chirps_valid_pixels"
    }
)


# ---------------------------------------------------------
# 3. ERA5-Land
# ---------------------------------------------------------

era5_cols = KEY + [
    "soil_moisture_0_7cm_mean",
    "soil_moisture_7_28cm_mean",
    "soil_moisture_28_100cm_mean",
    "temperature_2m_mean_c",
    "observations",
    "source_lat",
    "source_lon",
]

master = master.merge(
    era5[era5_cols],
    on=KEY,
    how="left",
    validate="one_to_one",
)


# ---------------------------------------------------------
# 4. Agricultural WaPOR AETI
# ---------------------------------------------------------

aeti_cols = KEY + [
    "agricultural_aeti_weighted_mm",
    "aeti_crop50_mm",
    "aeti_crop90_mm",
    "mixed_agricultural_pixels",
    "crop_equivalent_pixel_weight",
]

master = master.merge(
    aeti[aeti_cols],
    on=KEY,
    how="left",
    validate="one_to_one",
)


# ---------------------------------------------------------
# 5. WaPOR RET
# ---------------------------------------------------------

ret_cols = KEY + [
    "ret_mean_mm_dekad",
    "ret_median_mm_dekad",
    "ret_min_mm_dekad",
    "ret_max_mm_dekad",
]

master = master.merge(
    ret[ret_cols],
    on=KEY,
    how="left",
    validate="one_to_one",
)


# ---------------------------------------------------------
# 6. Sentinel NDVI
# ---------------------------------------------------------

ndvi_cols = [
    c
    for c in ndvi.columns
    if c not in ["date"]
]

master = master.merge(
    ndvi[ndvi_cols],
    on=KEY,
    how="left",
    validate="one_to_one",
)


# ---------------------------------------------------------
# 7. Observation indicator
# ---------------------------------------------------------

master[
    "has_ndvi_observation"
] = (
    master["ndvi_weighted"]
    .notna()
)


master["time_index"] = range(
    len(master)
)


# ---------------------------------------------------------
# 8. Structural validation
# ---------------------------------------------------------

print()
print("Master rows:", len(master))

print(
    "Unique dekads:",
    master[KEY]
    .drop_duplicates()
    .shape[0]
)

print(
    "NDVI-observed dekads:",
    int(
        master[
            "has_ndvi_observation"
        ].sum()
    )
)

print(
    "NDVI-missing dekads:",
    int(
        (
            ~master[
                "has_ndvi_observation"
            ]
        ).sum()
    )
)


if len(master) != 252:
    raise RuntimeError(
        f"Expected 252 dekads, "
        f"found {len(master)}"
    )


if master.duplicated(KEY).any():
    raise RuntimeError(
        "Duplicate temporal keys."
    )


# ---------------------------------------------------------
# 9. Missing predictor audit
# ---------------------------------------------------------

important = [
    "precipitation_mean_mm",
    "soil_moisture_0_7cm_mean",
    "soil_moisture_7_28cm_mean",
    "soil_moisture_28_100cm_mean",
    "temperature_2m_mean_c",
    "agricultural_aeti_weighted_mm",
    "ret_mean_mm_dekad",
]


print()
print("Predictor missing values:")
print(
    master[important]
    .isna()
    .sum()
    .to_string()
)


# ---------------------------------------------------------
# 10. Save
# ---------------------------------------------------------

master.to_csv(
    OUTPUT,
    index=False
)


print()
print("Saved:")
print(OUTPUT)

print()
print(
    "PASS: predictors aligned on "
    "252-dekad common grid"
)
