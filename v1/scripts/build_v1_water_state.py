from pathlib import Path

import pandas as pd

DEMAND = Path(
    "v1/data/processed_v1/"
    "water_demand_diagnostics_dekadal.csv"
)

RAIN = Path(
    "v1/data/chirps_dekad/processed/"
    "chirps_2018_2024_dekadal.csv"
)

SOIL = Path(
    "v1/data/era5land/processed/"
    "era5land_2018_2024_dekadal.csv"
)

OUT = Path(
    "v1/data/processed_v1/"
    "water_state_dekadal.csv"
)

keys = [
    "year",
    "month",
    "dekad"
]

demand = pd.read_csv(
    DEMAND
)

rain = pd.read_csv(
    RAIN
)

soil = pd.read_csv(
    SOIL
)

print(
    "Demand:",
    len(demand)
)

print(
    "Rain:",
    len(rain)
)

print(
    "Soil:",
    len(soil)
)

df = (
    demand
    .merge(
        rain[
            keys
            +
            [
                "precipitation_mean_mm"
            ]
        ],
        on=keys,
        validate="one_to_one"
    )
    .merge(
        soil[
            keys
            +
            [
                "soil_moisture_0_7cm_mean",
                "soil_moisture_7_28cm_mean",
                "soil_moisture_28_100cm_mean",
                "temperature_2m_mean_c"
            ]
        ],
        on=keys,
        validate="one_to_one"
    )
)

print(
    "\nMerged rows:",
    len(df)
)

if len(df) != 252:
    raise RuntimeError(
        f"Expected 252 rows, got {len(df)}"
    )

nulls = (
    df.isna()
    .sum()
)

bad = nulls[
    nulls > 0
]

if len(bad):
    print(
        "\nColumns containing nulls:"
    )
    print(bad)

else:
    print(
        "\nNo missing values."
    )


# Diagnostic only:
# atmospheric demand minus rainfall.
df[
    "ret_minus_precip_mm"
] = (
    df[
        "ret_mean_mm_dekad"
    ]
    -
    df[
        "precipitation_mean_mm"
    ]
)


# Diagnostic only:
# agricultural AETI minus rainfall.
df[
    "aeti_minus_precip_mm"
] = (
    df[
        "agricultural_aeti_weighted_mm"
    ]
    -
    df[
        "precipitation_mean_mm"
    ]
)


OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUT,
    index=False
)

print(
    "\nSaved:",
    OUT
)

print(
    "\nPASS: V1 water-state "
    "table constructed"
)
