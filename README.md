# Jordan-Agricultural-Water-Stress-V0
````bash
cat > README.md <<'EOF'
# Jordan Water-Stress Forecasting V0

A reproducible research prototype for forecasting next-month shallow soil-moisture stress in the Northern Jordan Valley using climate and environmental variables.

## Project Status

- Version: V0
- Status: Research prototype complete
- Study period: 2018–2024
- Hypothesis status: Inconclusive
- Next phase: V1

V0 is a methodological proof of concept. It is not yet an operational agricultural water-stress forecasting system.

---

## Research Question

Can environmental conditions observed at month `t` help predict shallow soil-moisture stress at month `t+1` better than simple persistence and seasonal-climatology baselines?

---

## Study Design

### Training

2018–2022

### Validation

2023

### Held-out testing

2024

The time series is kept chronological throughout the experiment.

No random train/test shuffling is used.

---

## Study Area

V0 uses a provisional Northern Jordan Valley region.

Approximate bounding box:

- Latitude: 32.0 to 33.3
- Longitude: 35.3 to 35.8

This boundary is provisional and should be replaced in V1 with a more accurate agricultural or irrigated-land mask.

---

## Data Sources

### CHIRPS V3

Used for precipitation.

Feature:

`precipitation_mm`

Resolution in V0:

Monthly regional precipitation.

---

### ERA5-Land

Used for:

- shallow soil moisture
- 2 m air temperature

Features:

`soil_moisture_m3_m3`

`temperature_2m_c`

Important:

ERA5-Land is a reanalysis dataset.

Its soil-moisture values are modelled environmental estimates rather than direct field measurements.

---

## Final V0 Features

The Random Forest model uses:

- precipitation
- shallow soil moisture
- 2 m air temperature
- previous-month precipitation
- previous-month soil moisture
- previous-month temperature
- seasonal sine encoding
- seasonal cosine encoding

Feature columns:

```text
precipitation_mm
soil_moisture_m3_m3
temperature_2m_c
precipitation_mm_lag1
soil_moisture_m3_m3_lag1
temperature_2m_c_lag1
month_sin
month_cos
````

---

## Forecast Target

The model predicts:

**next-month shallow soil-moisture stress**

Conceptually:

```text
Environmental conditions at month t
                |
                v
        forecasting model
                |
                v
       stress at month t+1
```

Stress is defined using calendar-month-specific soil-moisture thresholds.

The threshold for each month is the 25th percentile of soil moisture calculated using only the 2018–2022 training period.

The thresholds are then frozen and applied to validation and test data.

This prevents validation and test information from influencing the target definition.

---

## Data Leakage Protection

V0 explicitly checks that:

* future soil moisture is not a model feature
* the target is not included in the feature matrix
* training occurs before validation
* validation occurs before testing
* target thresholds are learned only from training data

The leakage check can be run with:

```bash
python scripts/leakage_check.py
```

Expected output:

```text
PASS: temporal ordering
PASS: no target included as feature
PASS: no future soil moisture included as feature
PASS: chronological split
```

---

## Machine-Learning Model

V0 uses:

`RandomForestClassifier`

Main configuration:

```text
n_estimators = 500
max_depth = 5
min_samples_leaf = 2
class_weight = balanced
random_state = 42
```

The classification probability threshold is selected using the 2023 validation period only.

Selected V0 threshold:

`0.25`

---

## Baselines

The Random Forest is compared against two simple baselines.

### Persistence

Assumes:

```text
next-month stress = current-month stress
```

### Seasonal climatology

Uses historical stress frequency for each calendar month based only on training data.

---

## 2024 Held-Out Results

### Random Forest

| Metric    | Result |
| --------- | -----: |
| Accuracy  |  0.545 |
| Precision |  0.286 |
| Recall    |  1.000 |
| F1        |  0.444 |
| ROC-AUC   |  0.556 |

The Random Forest detected both held-out stress events.

However, it also produced several false-positive alerts.

---

### Persistence Baseline

| Metric    | Result |
| --------- | -----: |
| Accuracy  |  0.727 |
| Precision |  0.000 |
| Recall    |  0.000 |
| F1        |  0.000 |

Persistence failed to detect either held-out stress event.

---

### Seasonal Climatology

| Metric    | Result |
| --------- | -----: |
| Accuracy  |  0.818 |
| Precision |  0.000 |
| Recall    |  0.000 |
| F1        |  0.000 |
| ROC-AUC   |  0.556 |

Seasonal climatology achieved higher overall accuracy because most months were non-stress months.

However, it failed to identify either positive stress event.

---

## Scientific Interpretation

The Random Forest showed higher event sensitivity than the simple baselines.

It detected:

```text
2 of 2 held-out stress events
```

but produced several false positives.

Therefore:

**H3 remains inconclusive.**

V0 does not demonstrate reliable predictive superiority.

The experiment suggests that the environmental features may contain useful forecasting information, but the available test evidence is too limited to support a strong conclusion.

---

## Test-Set Limitation

The held-out 2024 dataset contains only:

```text
11 usable monthly observations
2 positive stress events
```

This makes performance metrics highly uncertain.

Accuracy alone is particularly misleading because stress events are rare.

---

## Bootstrap Uncertainty

Random Forest F1 bootstrap results:

```text
2.5th percentile: 0.000
Median:           0.444
97.5th percentile: 0.800
```

The wide interval shows that the current test sample is too small for precise performance estimation.

---

## Threshold Sensitivity

The model was evaluated across multiple probability thresholds.

Thresholds around:

```text
0.20–0.30
```

produced:

```text
Recall = 1.0
F1 ≈ 0.444
```

Above approximately:

```text
0.35
```

recall began to fall.

At thresholds of approximately:

```text
0.40+
```

the model missed all held-out stress events.

This indicates that V0 is sensitive to threshold choice.

---

## Feature Importance

The highest Random Forest feature importance was:

`temperature_2m_c`

Approximate importance:

`0.213`

Other important variables included:

* current soil moisture
* precipitation
* previous-month precipitation
* previous-month soil moisture
* previous-month temperature

Feature importance should not be interpreted as causal importance.

---

## Repository Structure

```text
jordan-water-research/
|
├── data/
│   ├── chirps/
│   │   ├── raw/
│   │   └── processed/
│   ├── era5land/
│   │   ├── raw/
│   │   └── processed/
│   └── processed_v0/
|
├── evidence/
├── figures/
├── metadata/
├── models/
├── notes/
├── reports/
├── results/
├── scripts/
|
├── RUN_V0.sh
├── requirements-lock.txt
├── .gitignore
└── README.md
```

---

## Main Scripts

```text
scripts/build_target.py
scripts/build_features.py
scripts/leakage_check.py
scripts/train_v0.py
scripts/bootstrap_test.py
scripts/threshold_sensitivity.py
scripts/plot_results.py
scripts/make_report.py
```

---

## Running the Project

Install dependencies using the frozen environment:

```bash
python -m pip install -r requirements-lock.txt
```

Run the full experiment:

```bash
./RUN_V0.sh
```

A successful run ends with:

```text
V0 PIPELINE COMPLETE
```

---

## Individual Pipeline Stages

Build the leakage-safe target:

```bash
python scripts/build_target.py
```

Build lagged features:

```bash
python scripts/build_features.py
```

Run leakage tests:

```bash
python scripts/leakage_check.py
```

Train and evaluate:

```bash
python scripts/train_v0.py
```

Estimate uncertainty:

```bash
python scripts/bootstrap_test.py
```

Test probability thresholds:

```bash
python scripts/threshold_sensitivity.py
```

Generate figures:

```bash
python scripts/plot_results.py
```

Generate the research report:

```bash
python scripts/make_report.py
```

---

## Reproducibility

Important output files have SHA-256 checksums.

Verify them using:

```bash
sha256sum -c evidence/v0-checksums.sha256
```

All tracked files should return:

```text
OK
```

---

## Large Raw Files

Large downloaded environmental datasets are intentionally excluded from Git.

Examples:

```text
data/chirps/raw/
data/gpm/raw/
data/smap/raw/
data/era5land/raw/
```

Processed datasets, scripts, evidence, models, reports and reproducibility artifacts remain version-controlled.

---

## Important V0 Lessons

### Successful code does not guarantee valid science

During development, an evapotranspiration feature initially appeared as zero.

Further inspection showed that the source data were entirely missing.

The feature was removed rather than preserved as false data.

---

### Search failure does not prove absence

A literature database returning no matches does not prove that a research method has never been used.

The correct interpretation is:

> No matching study was identified in the searches performed so far.

---

### Dataset access problems are not scientific evidence

Authentication failures encountered while accessing NASA products do not imply that those datasets are invalid.

---

### Leakage can occur outside model training

V0 initially calculated stress thresholds using the entire dataset.

This was corrected so that thresholds are learned only from 2018–2022 training data.

---

## Major Limitations

V0 currently has several important limitations:

1. The test set is extremely small.
2. Only two stress events occur in the held-out period.
3. ERA5-Land soil moisture is reanalysis data.
4. ERA5-Land predictors use a representative point rather than a full regional spatial grid.
5. The study region is currently a provisional bounding box.
6. Soil-moisture stress is a proxy rather than direct crop stress.
7. Vegetation observations are not yet included.
8. Independent field observations are not yet available.
9. Irrigation demand is not directly measured.
10. Crop yield is not currently used for validation.

---

## V1 Roadmap

V1 will focus on improving scientific realism and validation.

### Vegetation observations

Add data such as:

* MODIS NDVI
* Sentinel-2 vegetation indices
* VCI
* EVI
* vegetation-health indicators

### Spatial modelling

Move from a representative ERA5-Land point to multiple spatial cells.

### Agricultural-area masking

Replace the provisional rectangle with agricultural or irrigated-land boundaries.

### Rolling validation

Use repeated chronological forecasting experiments such as:

```text
Train through 2020 → Test 2021
Train through 2021 → Test 2022
Train through 2022 → Test 2023
Train through 2023 → Test 2024
```

### Independent validation

Future validation should ideally include:

* measured soil moisture
* irrigation records
* crop-stress observations
* evapotranspiration measurements
* crop yield
* groundwater abstraction

### Drought-index comparison

Future models should also be compared with established indicators such as:

* SPI
* SPEI
* VCI
* TCI
* VHI
* soil-moisture anomaly

### SMAP

NASA SMAP remains a candidate satellite soil-moisture dataset for future versions once data-access issues are resolved.

---

## Scientific Conclusion

V0 demonstrates that a reproducible forecasting experiment can be built from climate and soil-moisture data while preserving chronological validation and preventing obvious information leakage.

The Random Forest detected both stress events in the held-out 2024 period, whereas persistence and seasonal climatology detected none.

However, low precision, multiple false positives, threshold sensitivity and the extremely small held-out sample prevent a strong predictive claim.

Therefore:

**V0 hypothesis status: INCONCLUSIVE**

The evidence supports continued investigation rather than declaring success.

---

## Research Philosophy

> Do not make the evidence defend the hypothesis.
> Make the hypothesis survive the evidence.

The project changed repeatedly when evidence contradicted the original plan.

That is part of the research process.

---

## Next Version

**V1: vegetation + spatial modelling + rolling validation + independent agricultural validation**

V0 establishes the pipeline.

V1 will test whether the signal survives stronger evidence.
EOF

````

Then verify the README:

```bash
head -n 30 README.md
````

Check that Git sees it:

```bash
git status --short README.md
```

Then stage and inspect:

```bash
git add README.md
git diff --cached -- README.md
```

Commit it:

```bash
git commit -m "Add comprehensive V0 research README"
```

Then pull/rebase before pushing if the remote may have changed:

```bash
git pull --rebase origin main
```

Finally:

```bash
git push origin main
```

This version avoids the nested heredoc/code-fence problem from the previous attempt and is ready to create directly from Git Bash.
