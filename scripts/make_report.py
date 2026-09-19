import json
import pandas as pd
from pathlib import Path

with open(
    "results/metrics_v0.json"
) as f:
    metrics = json.load(f)

importance = pd.read_csv(
    "results/feature_importance.csv"
)

test = metrics["test_2024"]

rf = test["random_forest"]
pers = test["persistence"]
clim = test["climatology"]

top = importance.iloc[0]

report = f"""
# Jordan Agricultural Water-Stress Forecasting V0

## Research question

Can current environmental conditions predict
next-month shallow-soil-moisture stress in the
Northern Jordan Valley better than simple temporal
baselines?

## Study period

2018–2024

## Temporal design

Training:
2018–2022

Validation:
2023

Held-out test:
2024

## Predictors

- CHIRPS monthly precipitation
- ERA5-Land shallow soil moisture
- ERA5-Land 2 m air temperature
- one-month lagged values
- seasonal month encoding

## Target

Next-month shallow-soil-moisture stress.

Stress was defined using calendar-month-specific
25th percentile thresholds learned exclusively from
the 2018–2022 training period.

## Test results

### Random Forest

Accuracy:
{rf['accuracy']:.3f}

Precision:
{rf['precision']:.3f}

Recall:
{rf['recall']:.3f}

F1:
{rf['f1']:.3f}

ROC-AUC:
{rf.get('roc_auc', float('nan')):.3f}

### Persistence baseline

Accuracy:
{pers['accuracy']:.3f}

Precision:
{pers['precision']:.3f}

Recall:
{pers['recall']:.3f}

F1:
{pers['f1']:.3f}

### Seasonal climatology

Accuracy:
{clim['accuracy']:.3f}

Precision:
{clim['precision']:.3f}

Recall:
{clim['recall']:.3f}

F1:
{clim['f1']:.3f}

ROC-AUC:
{clim.get('roc_auc', float('nan')):.3f}

## Interpretation

The Random Forest detected both held-out stress
events in 2024, producing recall of 1.0.

However, it generated multiple false-positive stress
alerts, producing low precision and lower overall
accuracy than the seasonal climatology baseline.

The climatology and persistence baselines failed to
detect either held-out stress event.

Therefore V0 provides evidence of possible sensitivity
to stress events, but does not demonstrate reliable
predictive superiority.

The held-out set contains only 11 observations and
2 stress events, making performance estimates highly
uncertain.

## Feature importance

The highest Random Forest importance was:

{top['feature']}
importance = {top['importance']:.3f}

Feature importance should not be interpreted as causal
importance.

## Hypothesis status

H3 is INCONCLUSIVE.

The model may identify stress events that simple
baselines miss, but the available evidence is too small
and false-positive performance is too weak to claim
general predictive improvement.

## Major limitations

1. Very small held-out dataset.
2. Only two positive stress cases in the test period.
3. ERA5-Land soil moisture is modeled/reanalysis data.
4. ERA5-Land point measurements are not regional field observations.
5. The study boundary is provisional.
6. The target is a soil-moisture stress proxy rather than
   direct measured crop stress.
7. No vegetation observations are included yet.
8. No independent field irrigation, yield, or soil-moisture
   validation is currently available.

## What V0 demonstrates

A reproducible scientific workflow:

literature review
→ gap falsification
→ data acquisition
→ verification
→ preprocessing
→ temporal alignment
→ leakage-safe target construction
→ baseline comparison
→ chronological validation
→ held-out testing
→ uncertainty analysis

## Required V1 work

- Acquire NDVI or comparable vegetation observations.
- Replace the provisional study rectangle with a verified
  agricultural-area polygon.
- Add multiple spatial grid cells rather than one
  representative ERA5-Land point.
- Perform rolling-origin validation across multiple years.
- Add independent field or irrigation observations.
- Compare against established drought indicators.
- Revisit SMAP when Earthdata access is available.
"""

Path(
    "reports/v0_experiment_report.md"
).write_text(
    report.strip() + "\n",
    encoding="utf-8"
)

print(report)
