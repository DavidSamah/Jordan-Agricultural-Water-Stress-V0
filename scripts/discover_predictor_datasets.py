from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path("v1/data")

OUT = Path(
    "v1/results/predictor_dataset_inventory.csv"
)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)


records = []


# ---------------------------------------------------------
# Helper: infer possible date columns
# ---------------------------------------------------------

def detect_date_columns(df):

    candidates = []

    for col in df.columns:

        name = col.lower()

        if any(
            token in name
            for token in [
                "date",
                "time",
                "datetime",
                "timestamp",
                "year",
                "month",
                "dekad",
            ]
        ):
            candidates.append(col)

    return candidates


# ---------------------------------------------------------
# Helper: infer temporal spacing
# ---------------------------------------------------------

def inspect_date_series(series):

    parsed = pd.to_datetime(
        series,
        errors="coerce"
    )

    parsed = (
        parsed
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    if len(parsed) < 2:
        return {
            "date_start": None,
            "date_end": None,
            "unique_dates": len(parsed),
            "median_interval_days": None,
            "min_interval_days": None,
            "max_interval_days": None,
        }

    diffs = (
        parsed
        .diff()
        .dropna()
        .dt.total_seconds()
        / 86400
    )

    return {
        "date_start": parsed.min(),
        "date_end": parsed.max(),
        "unique_dates": len(parsed),
        "median_interval_days": diffs.median(),
        "min_interval_days": diffs.min(),
        "max_interval_days": diffs.max(),
    }


# ---------------------------------------------------------
# Scan CSV files
# ---------------------------------------------------------

csv_files = list(
    ROOT.rglob("*.csv")
)


for path in sorted(csv_files):

    rel = path.relative_to(ROOT)

    print("=" * 72)
    print(rel)

    try:

        df = pd.read_csv(path)

    except Exception as exc:

        records.append({
            "file": str(rel),
            "type": "csv",
            "status": "read_error",
            "error": str(exc),
        })

        print("READ ERROR:", exc)

        continue


    print(
        "Rows:",
        len(df),
        "Columns:",
        len(df.columns)
    )

    print(
        "Columns:",
        list(df.columns)
    )


    date_candidates = detect_date_columns(df)

    selected_date = None
    temporal = {}


    # Prefer explicit date/time columns first.
    priority = [
        c
        for c in date_candidates
        if any(
            key in c.lower()
            for key in [
                "date",
                "datetime",
                "timestamp",
                "time",
            ]
        )
    ]


    for col in priority:

        test = pd.to_datetime(
            df[col],
            errors="coerce"
        )

        if test.notna().mean() >= 0.8:

            selected_date = col
            temporal = inspect_date_series(
                df[col]
            )

            break


    missing_fraction = (
        df.isna()
        .mean()
        .mean()
    )


    numeric_cols = (
        df.select_dtypes(
            include=np.number
        )
        .columns
        .tolist()
    )


    record = {
        "file": str(rel),
        "type": "csv",
        "status": "ok",
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": " | ".join(
            map(str, df.columns)
        ),
        "numeric_columns": " | ".join(
            numeric_cols
        ),
        "date_candidates": " | ".join(
            date_candidates
        ),
        "selected_date_column": selected_date,
        "overall_missing_fraction": missing_fraction,
    }


    record.update(temporal)

    records.append(record)


# ---------------------------------------------------------
# Raster inventory
# ---------------------------------------------------------

for extension in [
    "*.tif",
    "*.tiff",
]:

    for path in sorted(
        ROOT.rglob(extension)
    ):

        rel = path.relative_to(ROOT)

        records.append({
            "file": str(rel),
            "type": "raster",
            "status": "not_tabular",
        })


# ---------------------------------------------------------
# NetCDF inventory
# ---------------------------------------------------------

for path in sorted(
    ROOT.rglob("*.nc")
):

    rel = path.relative_to(ROOT)

    records.append({
        "file": str(rel),
        "type": "netcdf",
        "status": "requires_variable_inspection",
    })


inventory = pd.DataFrame(records)

inventory.to_csv(
    OUT,
    index=False
)


print()
print("=" * 72)
print("PREDICTOR DATASET INVENTORY")
print("=" * 72)

print(
    inventory[
        [
            c for c in [
                "file",
                "type",
                "status",
                "rows",
                "selected_date_column",
                "date_start",
                "date_end",
                "median_interval_days",
            ]
            if c in inventory.columns
        ]
    ].to_string(
        index=False
    )
)

print()
print("Saved:", OUT)
