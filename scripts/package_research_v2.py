from pathlib import Path
import json
import pandas as pd


ROOT = Path("v1")

BASELINE = (
    ROOT
    / "results"
    / "baselines_v2"
    / "baseline_metrics.csv"
)

CANDIDATE = (
    ROOT
    / "results"
    / "models_v2"
    / "candidate_validation_metrics.csv"
)

FINAL = (
    ROOT
    / "results"
    / "final_v2"
    / "unseen_2024_metrics.csv"
)

SELECTED = (
    ROOT
    / "results"
    / "models_v2"
    / "selected_models_v2.json"
)

OUTPUT = (
    ROOT
    / "results"
    / "final_v2"
    / "research_summary_v2.md"
)


baseline = pd.read_csv(BASELINE)
candidate = pd.read_csv(CANDIDATE)
final = pd.read_csv(FINAL)


with open(
    SELECTED,
    "r",
    encoding="utf-8"
) as f:
    selected = json.load(f)


lines = []

lines.append(
    "# Northern Jordan Valley Water–Vegetation Forecast V2"
)

lines.append("")
lines.append("## Research objective")
lines.append("")
lines.append(
    "Forecast agricultural vegetation condition one dekad ahead "
    "using remote sensing, meteorological, and water-state predictors."
)

lines.append("")
lines.append("## Study period")
lines.append("")
lines.append("2018–2024")

lines.append("")
lines.append("## Temporal resolution")
lines.append("")
lines.append("Dekadal")

lines.append("")
lines.append("## Target")
lines.append("")
lines.append(
    "Agricultural Sentinel-2 NDVI at t+1."
)

lines.append("")
lines.append("## Environmental predictors")
lines.append("")

predictors = [
    "CHIRPS precipitation",
    "ERA5-Land 2 m temperature",
    "ERA5-Land soil moisture at 0–7 cm",
    "ERA5-Land soil moisture at 7–28 cm",
    "ERA5-Land soil moisture at 28–100 cm",
    "WaPOR agricultural actual evapotranspiration",
    "WaPOR reference evapotranspiration",
    "derived water-balance variables",
    "lagged environmental variables",
    "seasonal terms",
    "current and historical NDVI for state-aware models",
]

for item in predictors:
    lines.append(f"- {item}")


lines.append("")
lines.append("## NDVI processing")
lines.append("")
lines.append(
    "486 Sentinel-2 agricultural NDVI observations were produced."
)
lines.append("")
lines.append(
    "Following quality assurance, 481 observations remained "
    "as model candidates."
)
lines.append("")
lines.append(
    "The native Sentinel acquisition series was aligned to "
    "the common dekadal predictor grid."
)


lines.append("")
lines.append("## Temporal evaluation design")
lines.append("")
lines.append("- Training: 2018–2022")
lines.append("- Validation: 2023")
lines.append("- Unseen future test: 2024")
lines.append("- Forecast horizon: one dekad ahead")
lines.append("")
lines.append(
    "No random temporal splitting was used. "
    "The 2024 period remained outside model selection."
)


lines.append("")
lines.append("## Baseline results")
lines.append("")
lines.append(baseline.to_string(index=False))


lines.append("")
lines.append("## Candidate validation results")
lines.append("")
lines.append(candidate.to_string(index=False))


lines.append("")
lines.append("## Selected candidate models")
lines.append("")
lines.append(
    json.dumps(
        selected,
        indent=2
    )
)


lines.append("")
lines.append("## Unseen 2024 evaluation")
lines.append("")
lines.append(final.to_string(index=False))


lines.append("")
lines.append("## Leakage controls")
lines.append("")

controls = [
    "chronological train/validation/test split",
    "explicit t → t+1 forecasting structure",
    "future targets excluded from predictors",
    "no random temporal shuffling",
    "no future NDVI interpolation",
    "2024 excluded from model selection",
    "candidate selection based on validation data only",
]

for item in controls:
    lines.append(f"- {item}")


lines.append("")
lines.append("## Reproducibility")
lines.append("")
lines.append(
    "The repository preserves processing scripts, QA outputs, "
    "feature definitions, temporal splits, baseline results, "
    "candidate-model validation results, final predictions, "
    "and unseen-period evaluation metrics."
)


OUTPUT.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8"
)


print("=" * 72)
print("RESEARCH PACKAGE")
print("=" * 72)

print()
print("Saved:")
print(OUTPUT)

print()
print("PASS: RESEARCH SUMMARY CREATED")
