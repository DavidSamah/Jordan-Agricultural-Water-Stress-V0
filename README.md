# Jordan-Agricultural-Water-Stress-V1
# V1 Forecasting — Agricultural Vegetation State Forecasting for the Northern Jordan Valley

## Overview

This directory contains the forecasting stage of **V1 of the Jordan Agricultural Water Research project**.

The purpose of V1 forecasting is to test whether the near-future state of agricultural vegetation can be predicted from:

1. hydro-climatic conditions,
2. the current vegetation state, and
3. recent vegetation history.

The forecasting target is:

```text
target_ndvi_t_plus_1
```

In practical terms, the models attempt to answer:

> Given the environmental conditions and vegetation state at time `t`, how well can we predict agricultural NDVI at the following timestep?

V1 represents a major methodological change from the earlier V0 experiment.

V0 treated the problem primarily as a next-month soil-moisture stress classification problem.

V1 instead follows the vegetation itself through time and asks whether its previous state contains predictive information beyond hydro-climate variables alone.

The current results indicate that it does.

---

# 1. Research Question

The central V1 forecasting question is:

> Does recent vegetation state provide useful predictive information for forecasting subsequent agricultural vegetation condition in the Northern Jordan Valley beyond what can be obtained from hydro-climatic predictors alone?

A secondary question is:

> Does vegetation exhibit measurable short-term memory such that NDVI at previous timesteps improves prediction of NDVI at the next timestep?

The present results provide evidence consistent with such a vegetation-memory effect.

This should currently be interpreted as a **predictive relationship**, not yet as proof of a specific physiological or causal mechanism.

---

# 2. Study Area

The current V1 pipeline focuses on agricultural land in the **Northern Jordan Valley**.

Remote-sensing observations are aligned to the WaPOR reference grid used elsewhere in the project.

Reference raster geometry:

```text
Shape: 1331 × 512
CRS: EPSG:4326
```

Agricultural statistics are calculated using cropland weighting rather than treating every raster pixel equally.

---

# 3. V1 Research Pipeline

The forecasting system sits downstream of a larger reproducible remote-sensing and environmental-data pipeline.

The conceptual flow is:

```text
Satellite observations
        │
        ▼
Sentinel-2 RED / NIR / SCL
        │
        ▼
Scene discovery and QA
        │
        ▼
Reprojection to WaPOR grid
        │
        ▼
Cloud / invalid-pixel filtering
        │
        ▼
NDVI calculation
        │
        ▼
Agricultural weighting
        │
        ▼
Observation-level NDVI series
        │
        ▼
Temporal QA
        │
        ▼
Dekadal / forecasting alignment
        │
        ├──────── Hydro-climate predictors
        │
        └──────── Vegetation-state history
        │
        ▼
t → t+1 supervised forecasting dataset
        │
        ▼
Chronological train / validation / test split
        │
        ▼
Baselines
        │
        ▼
Hydro-climate-only models
        │
        ▼
State-aware models
        │
        ▼
Held-out 2024 evaluation
```

This structure is intentional.

The forecasting model is not treated as an isolated machine-learning experiment. It is the final layer of a chain beginning with physical Earth-observation measurements.

---

# 4. Sentinel-2 Vegetation Data

The underlying vegetation series is generated from Sentinel-2 imagery.

The main observation table is:

```text
v1/data/sentinel2/agricultural_ndvi_observations.csv
```

The current Sentinel-2 processing system:

- discovers Sentinel-2 scenes,
- reads RED and NIR reflectance,
- reads Scene Classification Layer information,
- filters unusable pixels,
- mosaics multiple scenes where necessary,
- reprojects imagery to the WaPOR grid,
- calculates NDVI,
- applies agricultural weighting,
- records coverage and observation metadata,
- supports resumable processing.

Continuous RED and NIR raster values are reprojected using bilinear interpolation.

Categorical Scene Classification Layer values are reprojected using nearest-neighbour resampling.

This distinction prevents categorical land/cloud classes from being artificially interpolated.

---

# 5. NDVI Definition

NDVI is calculated as:

```text
NDVI = (NIR - RED) / (NIR + RED)
```

NDVI provides a remotely sensed measure related to vegetation greenness and canopy condition.

For the forecasting experiment, NDVI is not interpreted as a direct measurement of irrigation, crop yield, or plant water content.

Instead, it is used as an observable vegetation-state variable that can potentially integrate the effects of multiple environmental processes over time.

---

# 6. Agricultural Weighting

The research question concerns agricultural vegetation rather than the complete landscape.

Therefore, NDVI is summarized using agricultural/cropland weighting.

Conceptually:

```text
Agricultural NDVI
        =
Σ(NDVI_pixel × cropland_fraction_pixel)
────────────────────────────────────────
Σ(cropland_fraction_pixel)
```

This prevents non-agricultural pixels from contributing equally to the regional agricultural signal.

---

# 7. NDVI Quality Assurance

The NDVI series is subjected to a dedicated quality-assurance stage before being used for forecasting.

QA outputs include:

```text
v1/results/ndvi_qa/agricultural_ndvi_qa.csv
```

The processed V1 observation dataset currently spans:

```text
2018–2024
```

The QA workflow checks temporal behavior and identifies observations that deserve further inspection.

Temporal outlier flags are treated as **diagnostic information**, not automatically as invalid observations.

An unusual NDVI value may reflect:

- cloud contamination,
- incomplete spatial coverage,
- compositing effects,
- agricultural seasonality,
- harvest,
- planting,
- crop rotation,
- drought,
- irrigation changes,
- or a genuine rapid vegetation-state transition.

Therefore, automated anomaly detection is followed by scientific interpretation rather than automatic deletion.

---

# 8. Forecasting Unit

The forecasting problem is constructed as a one-step-ahead temporal prediction problem.

For each valid timestep:

```text
X(t) → NDVI(t+1)
```

where `X(t)` contains information available at or before time `t`.

The target is explicitly shifted forward:

```text
target_ndvi_t_plus_1
```

This prevents the model from simply reconstructing the NDVI value it is given at the same timestep.

---

# 9. Predictor Families

The forecasting experiment separates predictors into two major conceptual groups.

## 9.1 Hydro-climatic predictors

These describe environmental conditions that may influence vegetation.

Examples include variables representing processes such as:

- precipitation,
- atmospheric conditions,
- soil-water state,
- evapotranspiration-related conditions,
- and other temporally aligned hydro-climatic information available in V1.

The purpose of the hydro-climate-only experiment is to ask:

> How predictable is future vegetation condition from environmental forcing alone?

---

## 9.2 Vegetation-state predictors

The state-aware forecasting experiment additionally includes recent vegetation observations.

The current state-aware formulation includes:

```text
ndvi_t
ndvi_lag_1
ndvi_lag_2
ndvi_lag_3
```

alongside the hydro-climatic predictors.

Conceptually:

```text
Future vegetation
      =
f(
    environmental forcing,
    current vegetation state,
    recent vegetation history
 )
```

This allows the model to represent persistence and short-term temporal memory.

---

# 10. Vegetation Memory Hypothesis

The vegetation-memory component is one of the most important research directions emerging from V1.

The hypothesis is:

> The future condition of vegetation depends not only on current environmental forcing but also on the vegetation system's recent state.

In simplified form:

```text
NDVI(t+1)
    ≠
f(climate_t) only
```

Instead:

```text
NDVI(t+1)
    =
f(
  climate_t,
  NDVI_t,
  NDVI_t-1,
  NDVI_t-2,
  NDVI_t-3
)
```

This is plausible because vegetation response is temporally integrated.

For example, the NDVI observed today may contain information related to earlier:

- water availability,
- crop development,
- accumulated stress,
- irrigation,
- phenological stage,
- planting history,
- or previous environmental conditions.

The current modelling results are consistent with this hypothesis because state-aware forecasting substantially outperformed both simple baselines and the tested hydro-climate-only model.

However, these results alone do not establish the exact biological mechanism responsible for the predictive memory.

That question requires further scientific validation.

---

# 11. Temporal Split

All model evaluation is chronological.

The current split is frozen as:

```text
TRAIN       2018–2022
VALIDATION  2023
TEST        2024
```

This design is deliberate.

Random train/test splitting is inappropriate for this experiment because neighboring observations are temporally related.

A random split could allow future conditions to influence model selection indirectly and produce unrealistically optimistic performance.

The chronological structure simulates the actual forecasting problem:

```text
Past → future
```

rather than:

```text
Random observations → random observations
```

---

# 12. Role of Each Split

## Training set — 2018–2022

Used to estimate model parameters.

```text
2018
2019
2020
2021
2022
```

---

## Validation set — 2023

Used for model development and comparison.

```text
2023
```

This period can be inspected while deciding:

- feature construction,
- model families,
- regularization,
- and methodological changes.

---

## Test set — 2024

Used as the final unseen evaluation period.

```text
2024
```

The purpose of the test set is to estimate how the final selected modelling approach behaves on a year not used for training or model selection.

The current state-aware test contains:

```text
n = 35 evaluable forecasts
```

---

# 13. Baseline Models

A forecast model should not be considered useful merely because it produces predictions.

It must outperform simple alternatives.

V1 therefore compares candidate models against baseline forecasts.

The two principal baselines are:

## Persistence

Persistence assumes:

```text
NDVI(t+1) = NDVI(t)
```

This is a particularly important baseline because vegetation condition is temporally autocorrelated.

A sophisticated model that cannot outperform persistence provides little additional forecasting value.

---

## Climatology

The climatological baseline predicts future vegetation using the typical historical seasonal state.

This captures recurring seasonal structure without learning complex relationships between predictors.

---

# 14. Hydro-Climate-Only Experiment

Before providing the model with vegetation history, a hydro-climate-only model was evaluated.

A HistGradientBoosting model produced approximately:

```text
Validation RMSE: 0.049272
```

The validation climatology baseline produced approximately:

```text
Validation RMSE: 0.044703
```

Therefore:

```text
Hydro-climate-only model RMSE
>
Climatology RMSE
```

The tested hydro-climate-only model did **not** outperform climatology during validation.

This result is scientifically useful.

It suggests that simply adding environmental predictors and a nonlinear machine-learning model is not automatically sufficient to improve short-horizon vegetation forecasting.

---

# 15. State-Aware Forecast Model

The strongest current model is a **state-aware Ridge regression**.

It combines:

```text
Hydro-climatic predictors
+
ndvi_t
+
ndvi_lag_1
+
ndvi_lag_2
+
ndvi_lag_3
```

Ridge regression applies L2 regularization to the linear coefficients.

The regularized formulation helps control coefficient instability when predictors are correlated.

This is especially relevant because neighboring NDVI lags are expected to contain overlapping information.

---

# 16. Validation Results

For the state-aware Ridge model:

```text
Validation MAE   = 0.022655
Validation RMSE  = 0.034488
Validation Bias  = -0.013071
```

The negative bias indicates that the model slightly underpredicted NDVI on average during validation.

These values should be interpreted in NDVI units.

---

# 17. Held-Out 2024 Results

The frozen 2024 test produced:

```text
n = 35

MAE   = 0.0183403
RMSE  = 0.0281941
Bias  = -0.00424245
```

The small negative bias indicates slight average underprediction.

---

# 18. 2024 Baseline Comparison

The 2024 baseline results were:

| Model | MAE | RMSE |
|---|---:|---:|
| Seasonal climatology | 0.0352143 | 0.0554145 |
| Persistence | 0.0272925 | 0.0420290 |
| State-aware Ridge | **0.0183403** | **0.0281941** |

The state-aware Ridge model achieved lower MAE and RMSE than both baselines on the held-out 2024 period.

Relative to persistence:

```text
Persistence RMSE = 0.0420290
State-aware RMSE = 0.0281941
```

Approximate RMSE reduction:

```text
(0.0420290 - 0.0281941) / 0.0420290
≈ 32.9%
```

Relative to climatology:

```text
Climatology RMSE = 0.0554145
State-aware RMSE = 0.0281941
```

Approximate RMSE reduction:

```text
≈ 49.1%
```

These results indicate that the state-aware formulation contains predictive information beyond both simple seasonal expectation and pure vegetation persistence.

---

# 19. Current Interpretation

The strongest result from V1 is not simply:

> Ridge regression worked well.

The more scientifically interesting result is the contrast between model states.

The tested hydro-climate-only system did not outperform climatology during validation.

However, once the current vegetation state and recent vegetation history were introduced, forecasting performance improved substantially.

Conceptually:

```text
Hydro-climate only
        ↓
limited predictive improvement

Hydro-climate
      +
current vegetation state
      +
recent vegetation history
        ↓
substantial predictive improvement
```

This suggests that the vegetation system itself contains information about its future trajectory that is not fully represented by the contemporaneous hydro-climatic predictors.

This is referred to in the project as **vegetation memory**.

---

# 20. What “Vegetation Memory” Means Here

The phrase does **not** currently imply that the model has identified a specific biological memory mechanism.

Instead, it means:

> Past vegetation state improves prediction of subsequent vegetation state after environmental predictors are included.

Possible explanations include:

- biological persistence,
- crop phenology,
- cumulative water stress,
- irrigation history,
- delayed rainfall response,
- soil-water storage,
- planting cycles,
- harvest cycles,
- spatial aggregation,
- or combinations of these mechanisms.

Determining which explanation dominates is a separate research question.

---

# 21. What the Current Results Do Not Prove

The V1 forecasting results do not yet demonstrate that:

- NDVI directly measures irrigation requirement,
- the model identifies causal relationships,
- vegetation memory is purely biological,
- the model generalizes to every agricultural region in Jordan,
- the model generalizes to different crop systems,
- the model is ready for operational irrigation decisions,
- state-aware Ridge is universally the best forecasting algorithm,
- or the observed relationship will remain stable under major climatic or land-use change.

These distinctions are important for preserving scientific validity.

---

# 22. Why Ridge Regression Is Scientifically Useful

A more complex model is not automatically preferable.

The strong performance of Ridge is useful because Ridge is comparatively interpretable.

The model is constrained enough to make the research question visible:

```text
Does vegetation history add predictive information?
```

rather than allowing a highly flexible model to hide that relationship inside thousands of nonlinear decisions.

For the current research stage, interpretability and methodological clarity are important alongside predictive performance.

---

# 23. Leakage Prevention

The forecasting workflow is designed around strict temporal causality.

Predictors for time `t` must be available at or before `t`.

The target occurs at:

```text
t + 1
```

The model must never receive:

- future NDVI,
- future climate observations,
- future water-state variables,
- target-derived information,
- or statistics calculated using the held-out future period.

The correct causal structure is:

```text
past ───────► present ───────► future
                     predict
```

and never:

```text
future information
        │
        └────────► predictor
```

---

# 24. Reproducibility Principle

The V1 forecast is intended to be reproducible from upstream data products.

The forecasting experiment should therefore be treated as a sequence of deterministic research stages:

```text
1. Build / verify Sentinel-2 observations
2. Perform NDVI QA
3. Freeze the accepted NDVI series
4. Aggregate / align forecasting timesteps
5. Join predictor datasets
6. Construct lags
7. Shift the forecasting target
8. Verify temporal ordering
9. Apply chronological split
10. Compute baselines
11. Train candidate models
12. Select using validation only
13. Freeze the selected model
14. Evaluate once on 2024
15. Save predictions and metrics
16. Interpret scientifically
```

Each stage should be inspectable independently.

---

# 25. Recommended Directory Role

`v1/forecast/` should contain only artifacts associated with forecasting and forecast evaluation.

Conceptually:

```text
v1/
├── data/
│   ├── sentinel2/
│   ├── wapor/
│   └── ...
│
├── results/
│   └── ndvi_qa/
│
└── forecast/
    ├── README.md
    ├── data/
    ├── models/
    ├── results/
    ├── figures/
    └── scripts/
```

The exact repository layout may evolve, but raw-source acquisition, processed forecasting datasets, trained models, results and figures should remain conceptually separated.

---

# 26. Forecast Dataset Structure

A model-ready forecasting row conceptually represents:

```text
Time t
│
├── hydro-climate predictors
│
├── NDVI_t
├── NDVI_t-1
├── NDVI_t-2
├── NDVI_t-3
│
└── target_NDVI_t+1
```

For example:

```text
[t predictors] ─────────► vegetation at t+1
```

The lagging and target shift naturally remove some edge observations because the earliest timesteps lack sufficient history and the final timestep lacks a known next observation.

This is expected behavior rather than missing-data corruption.

---

# 27. Evaluation Metrics

The primary regression metrics are:

## Mean Absolute Error

```text
MAE = mean(|prediction - observation|)
```

MAE describes the average absolute forecasting error.

---

## Root Mean Squared Error

```text
RMSE = sqrt(mean((prediction - observation)^2))
```

RMSE penalizes larger forecast errors more strongly.

---

## Bias

```text
Bias = mean(prediction - observation)
```

Interpretation:

```text
Bias > 0  → average overprediction
Bias < 0  → average underprediction
Bias ≈ 0  → little systematic directional error
```

No single metric is interpreted in isolation.

---

# 28. Scientific Comparison Logic

The forecasting experiment can be summarized as a sequence of increasingly informative models:

```text
Seasonal climatology
        │
        ▼
Persistence
        │
        ▼
Hydro-climate-only model
        │
        ▼
Hydro-climate + vegetation state
        │
        ▼
Hydro-climate + vegetation memory
```

The scientific question is therefore not merely:

> Which algorithm gives the lowest RMSE?

It is also:

> Which additional information causes forecasting skill to emerge?

That distinction is central to the V1 research design.

---

# 29. Current Main Finding

The current evidence can be summarized conservatively as:

> In the Northern Jordan Valley V1 dataset, a state-aware model containing current and lagged vegetation information predicted next-step agricultural NDVI more accurately than seasonal climatology and persistence during the held-out 2024 evaluation.

A second result is:

> The tested hydro-climate-only HistGradientBoosting model did not outperform climatology during 2023 validation.

Together, these findings motivate deeper investigation of vegetation-state persistence and memory.

---

# 30. Scientific Contribution Under Investigation

The project is currently evaluating whether its main contribution should center on one or more of the following:

### A. Vegetation memory

Quantifying how much previous agricultural vegetation state contributes to short-term vegetation forecasting.

### B. State-aware agricultural forecasting

Showing that environmental forcing becomes more useful when interpreted together with the system's current biological state.

### C. Hybrid Earth-observation forecasting

Integrating satellite vegetation observations, water/climate variables and temporal machine learning within a reproducible agricultural monitoring system.

### D. Decision-support translation

Investigating whether forecast vegetation trajectories can eventually provide useful information for water-management or agricultural planning.

The first three are currently research questions.

The fourth requires considerably more validation before operational claims can be made.

---

# 31. Required Next Validation

The current 2024 result is promising, but deeper validation is required.

Priority analyses include:

## 31.1 Ablation analysis

Train models using progressively different predictor sets:

```text
Hydro-climate only

Hydro-climate + NDVI_t

Hydro-climate + NDVI_t + lag_1

Hydro-climate + NDVI_t + lag_1 + lag_2

Hydro-climate + NDVI_t + lag_1 + lag_2 + lag_3
```

This will quantify how much predictive information each level of vegetation history contributes.

---

## 31.2 Lag sensitivity

Test whether predictive performance changes systematically with vegetation-history depth.

For example:

```text
1 dekad
2 dekads
3 dekads
...
```

This may reveal the temporal scale over which useful vegetation-state information persists.

---

## 31.3 Rolling-origin evaluation

The current frozen split should be complemented by repeated historical forecasting tests.

Example:

```text
Train → 2018–2020
Test  → 2021

Train → 2018–2021
Test  → 2022

Train → 2018–2022
Test  → 2023

Train → 2018–2023
Test  → 2024
```

This would show whether the result is stable across multiple forecast years rather than being specific to 2024.

---

## 31.4 Predictor ablation

Remove individual hydro-climatic predictors and observe the change in performance.

This helps distinguish:

```text
predictive necessity
```

from:

```text
predictor availability
```

---

## 31.5 Seasonal error analysis

Model skill should be examined by agricultural season rather than only through annual averages.

A low annual RMSE may conceal periods of poor prediction during critical crop-development or water-stress periods.

---

## 31.6 Extreme-event analysis

Forecast errors should be examined separately during:

- unusually dry periods,
- unusually wet periods,
- rapid vegetation decline,
- rapid vegetation recovery,
- and strong seasonal transitions.

Operational usefulness often depends more on unusual conditions than normal ones.

---

## 31.7 Spatial validation

The current aggregated signal should eventually be complemented by spatial analysis.

Regional averaging may hide heterogeneous behavior among:

- farms,
- crop types,
- irrigation systems,
- elevations,
- soils,
- and water-access regimes.

---

# 32. Connection to the Larger Hybrid Simulation

The forecasting work is one component of the broader project concept.

The eventual hybrid framework aims to connect:

```text
Remote sensing
+
Hydrology / climate
+
Vegetation state
+
Machine learning
+
Scenario analysis
```

Potential future state variables may include:

- vegetation condition,
- evapotranspiration,
- soil-water availability,
- crop-water stress,
- irrigation requirement,
- and other water-management indicators.

The present V1 forecasting work should therefore be understood as a validated building block, not the final hybrid simulation.

---

# 33. Difference Between Forecasting and Simulation

These concepts must remain separate.

## Forecasting

Asks:

> Given observed conditions, what is likely to happen next?

```text
observations
    ↓
model
    ↓
future estimate
```

## Simulation

Asks:

> What might happen under a hypothetical intervention or scenario?

```text
scenario
    ↓
system assumptions
    ↓
simulated trajectory
```

A predictive model does not automatically become a valid intervention simulator.

Moving from forecasting to scenario simulation requires additional causal and process-based justification.

---

# 34. Research Integrity

The project follows several methodological principles:

### No future leakage

Future observations cannot enter present predictors.

### Frozen held-out evaluation

The final test year should not repeatedly influence model redesign.

### Baselines before complexity

Every model must be compared with simple alternatives.

### Reproducibility

Intermediate datasets and model decisions should be reconstructable.

### Physical interpretation

Machine-learning performance must remain connected to the underlying water–vegetation system.

### Conservative claims

Predictive improvement is not automatically evidence of causality.

---

# 35. Current Status

Current V1 forecasting status:

```text
[✓] Sentinel-2 NDVI pipeline
[✓] Agricultural weighting
[✓] Multi-scene processing
[✓] Reprojection to WaPOR grid
[✓] Resumable observation construction
[✓] 2018–2024 vegetation series
[✓] NDVI quality assurance
[✓] Forecasting dataset construction
[✓] Chronological split
[✓] Baseline forecasts
[✓] Hydro-climate-only experiment
[✓] State-aware forecasting
[✓] Frozen 2024 evaluation
[✓] Vegetation-memory signal identified

[ ] Formal lag-ablation study
[ ] Rolling-origin validation
[ ] Seasonal error decomposition
[ ] Extreme-event validation
[ ] Spatial robustness analysis
[ ] Crop-specific interpretation
[ ] Supervisor methodological review
[ ] Final contribution definition
[ ] Manuscript / funding framing
[ ] Operational decision-support validation
```

---

# 36. Current Numerical Summary

## Validation

```text
Hydro-climate HistGradientBoosting
RMSE = 0.049272

Climatology
RMSE = 0.044703
```

State-aware Ridge:

```text
MAE   = 0.022655
RMSE  = 0.034488
Bias  = -0.013071
```

---

## Held-Out Test — 2024

```text
n = 35
```

### Climatology

```text
MAE  = 0.0352143
RMSE = 0.0554145
```

### Persistence

```text
MAE  = 0.0272925
RMSE = 0.0420290
```

### State-Aware Ridge

```text
MAE   = 0.0183403
RMSE  = 0.0281941
Bias  = -0.00424245
```

Approximate improvement in test RMSE:

```text
vs persistence : 32.9%
vs climatology : 49.1%
```

---

# 37. Interpretation in One Diagram

```text
          HYDRO-CLIMATE
                │
                │
                ▼
         ┌─────────────┐
         │ Vegetation  │
         │   state t   │
         └──────┬──────┘
                │
       ┌────────┼─────────┐
       │        │         │
       ▼        ▼         ▼
     t-1      t-2       t-3
       │        │         │
       └────────┼─────────┘
                │
                ▼
       VEGETATION MEMORY
                │
                ▼
      ┌───────────────────┐
      │ STATE-AWARE MODEL │
      └─────────┬─────────┘
                │
                ▼
           NDVI(t+1)
```

The key V1 result is that knowledge of the **state of the system** materially improves the ability to forecast its next state.

---

# 38. Broader Research Idea

The project is gradually moving from a simple prediction question toward a more general systems question:

> Can an agricultural water system be forecast more accurately when environmental forcing is interpreted through the state and recent history of the vegetation responding to that forcing?

That question connects:

- remote sensing,
- agricultural water management,
- environmental forecasting,
- time-series analysis,
- machine learning,
- and eventually hybrid simulation.

---

# 39. Immediate Research Sequence

The methodological sequence from the current checkpoint is:

```text
Current state-aware result
        │
        ▼
Ablation analysis
        │
        ▼
Lag / memory sensitivity
        │
        ▼
Rolling temporal validation
        │
        ▼
Error decomposition
        │
        ▼
Scientific interpretation
        │
        ▼
Supervisor review
        │
        ├──► research paper direction
        │
        ├──► research-funding direction
        │
        └──► decision-support direction
```

The scientific contribution should be defined before expanding the system merely for technical complexity.

---

# 40. Reproducibility Philosophy

V1 follows a simple principle:

> Every final number should have a traceable path back to an observation.

For a forecast this means being able to trace:

```text
prediction
   ↓
model
   ↓
model-ready row
   ↓
lag construction
   ↓
aligned predictors
   ↓
dekadal vegetation state
   ↓
agricultural NDVI statistic
   ↓
valid Sentinel-2 pixels
   ↓
RED / NIR observations
   ↓
satellite acquisition
```

The model is therefore only the final component of the research object.

The complete pipeline is the research system.

---

# 41. Project Stage

V1 should currently be described as:

> A reproducible research forecasting pipeline with promising held-out evidence that recent vegetation state improves short-horizon agricultural NDVI forecasting in the Northern Jordan Valley.

It should **not yet** be described as:

> An operational irrigation prediction system.

That transition requires further validation, interpretation and domain review.

---

# 42. Citation / Publication Status

This project is currently under active research development.

Results in this directory should be treated as preliminary until:

- validation is completed,
- methodology is reviewed,
- the scientific contribution is finalized,
- and the research team determines the appropriate publication or funding pathway.

---

# 43. Collaboration

The V1 system is being developed as part of a collaborative research process combining:

- AI and machine learning,
- data analysis,
- remote sensing,
- agriculture,
- water management,
- environmental modelling,
- and reproducible computational research.

The next research stage will be carried out with additional scientific guidance and supervisor review.

---

# 44. Final Principle

V1 is built around a distinction that increasingly defines the project:

```text
More data ≠ more understanding
More complex model ≠ better science
Better prediction ≠ causality
```

The objective is to determine **which information about the physical system actually improves our understanding and forecasting of agricultural vegetation behavior**.

The current evidence points toward one particularly important piece of that information:

```text
The recent history of the vegetation itself.
```
