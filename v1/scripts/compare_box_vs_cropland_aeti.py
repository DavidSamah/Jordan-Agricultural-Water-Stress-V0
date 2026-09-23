import pandas as pd

box = pd.read_csv(
    "v1/data/wapor/processed/"
    "aeti_2018_2024_dekadal.csv"
)

farm = pd.read_csv(
    "v1/data/wapor/processed/"
    "agricultural_aeti_2018_2024_dekadal.csv"
)

merged = box.merge(
    farm,
    on=[
        "year",
        "month",
        "dekad"
    ],
    validate="one_to_one"
)

merged["difference_mm"] = (
    merged[
        "agricultural_aeti_weighted_mm"
    ]
    -
    merged[
        "aeti_mean_mm_dekad"
    ]
)

print(
    merged[
        [
            "year",
            "month",
            "dekad",
            "aeti_mean_mm_dekad",
            "agricultural_aeti_weighted_mm",
            "difference_mm"
        ]
    ].head(20)
)

print("\nMEAN WHOLE BOX AETI")

print(
    merged[
        "aeti_mean_mm_dekad"
    ].mean()
)

print("\nMEAN AGRICULTURAL AETI")

print(
    merged[
        "agricultural_aeti_weighted_mm"
    ].mean()
)

print("\nMEAN DIFFERENCE")

print(
    merged[
        "difference_mm"
    ].mean()
)

merged.to_csv(
    "v1/data/wapor/processed/"
    "aeti_box_vs_agriculture.csv",
    index=False
)

print(
    "\nPASS: agricultural comparison complete"
)
