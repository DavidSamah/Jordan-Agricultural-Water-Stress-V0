from pathlib import Path

import numpy as np
import pandas as pd

AETI = Path(
    "v1/data/wapor/processed/"
    "agricultural_aeti_2018_2024_dekadal.csv"
)

RET = Path(
    "v1/data/wapor_ret/processed/"
    "ret_2018_2024_dekadal.csv"
)

OUT = Path(
    "v1/data/processed_v1/"
    "water_demand_diagnostics_dekadal.csv"
)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

aeti = pd.read_csv(AETI)
ret = pd.read_csv(RET)

print("AETI rows:", len(aeti))
print("RET rows:", len(ret))

keys = [
    "year",
    "month",
    "dekad"
]

df = aeti.merge(
    ret[
        [
            "year",
            "month",
            "dekad",
            "ret_mean_mm_dekad"
        ]
    ],
    on=keys,
    how="inner",
    validate="one_to_one"
)

print("Merged rows:", len(df))

if len(df) != len(aeti):
    raise RuntimeError(
        "AETI/RET merge lost observations"
    )

if df[
    "ret_mean_mm_dekad"
].isna().any():
    raise RuntimeError(
        "RET contains missing values"
    )

if df[
    "agricultural_aeti_weighted_mm"
].isna().any():
    raise RuntimeError(
        "Agricultural AETI contains missing values"
    )

# Diagnostic 1:
# actual ET relative to reference demand
df["aeti_ret_ratio"] = np.where(
    df["ret_mean_mm_dekad"] > 0,
    (
        df[
            "agricultural_aeti_weighted_mm"
        ]
        /
        df[
            "ret_mean_mm_dekad"
        ]
    ),
    np.nan
)

# Diagnostic 2:
# reference-demand gap
df["ret_minus_aeti_mm"] = (
    df["ret_mean_mm_dekad"]
    -
    df[
        "agricultural_aeti_weighted_mm"
    ]
)

# Diagnostic flag only.
# NOT irrigation need.
df["high_demand_low_actual_et"] = (
    (df["aeti_ret_ratio"] < 0.5)
    &
    (
        df["ret_mean_mm_dekad"]
        >
        df[
            "ret_mean_mm_dekad"
        ].median()
    )
).astype(int)

df.to_csv(
    OUT,
    index=False
)

print("\nAETI / RET")
print(
    df["aeti_ret_ratio"]
    .describe()
)

print("\nRET - AETI")
print(
    df["ret_minus_aeti_mm"]
    .describe()
)

print(
    "\nDiagnostic flagged dekads:",
    int(
        df[
            "high_demand_low_actual_et"
        ].sum()
    )
)

print("\nSaved:", OUT)

print(
    "\nPASS: water-demand diagnostics created"
)
