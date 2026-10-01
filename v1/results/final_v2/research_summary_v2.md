# Northern Jordan Valley Water–Vegetation Forecast V2

## Research objective

Forecast agricultural vegetation condition one dekad ahead using remote sensing, meteorological, and water-state predictors.

## Study period

2018–2024

## Temporal resolution

Dekadal

## Target

Agricultural Sentinel-2 NDVI at t+1.

## Environmental predictors

- CHIRPS precipitation
- ERA5-Land 2 m temperature
- ERA5-Land soil moisture at 0–7 cm
- ERA5-Land soil moisture at 7–28 cm
- ERA5-Land soil moisture at 28–100 cm
- WaPOR agricultural actual evapotranspiration
- WaPOR reference evapotranspiration
- derived water-balance variables
- lagged environmental variables
- seasonal terms
- current and historical NDVI for state-aware models

## NDVI processing

486 Sentinel-2 agricultural NDVI observations were produced.

Following quality assurance, 481 observations remained as model candidates.

The native Sentinel acquisition series was aligned to the common dekadal predictor grid.

## Temporal evaluation design

- Training: 2018–2022
- Validation: 2023
- Unseen future test: 2024
- Forecast horizon: one dekad ahead

No random temporal splitting was used. The 2024 period remained outside model selection.

## Baseline results

     split                 baseline   n      mae     rmse          bias
     train   baseline_training_mean 175 0.134338 0.154514  2.410770e-17
     train baseline_training_median 175 0.121722 0.172024 -7.561522e-02
     train     baseline_climatology 175 0.028667 0.047807 -8.036900e-04
     train     baseline_persistence 174 0.032250 0.049886  1.119116e-03
validation   baseline_training_mean  36 0.140827 0.155976 -1.760037e-02
validation baseline_training_median  36 0.136182 0.180854 -9.321560e-02
validation     baseline_climatology  36 0.025400 0.044703 -1.289356e-02
validation     baseline_persistence  36 0.030556 0.046132 -3.364101e-03

## Candidate validation results

       family                  model  n      mae     rmse      bias
hydro_climate                  ridge 36 0.036902 0.050968 -0.022439
hydro_climate          random_forest 36 0.046632 0.075736 -0.032668
hydro_climate hist_gradient_boosting 36 0.030985 0.049272 -0.019046
  state_aware                  ridge 36 0.022655 0.034488 -0.013071
  state_aware          random_forest 36 0.035177 0.059786 -0.025732
  state_aware hist_gradient_boosting 36 0.027504 0.046607 -0.020307

## Selected candidate models

{
  "hydro_climate": {
    "model": "hist_gradient_boosting",
    "validation_mae": 0.030985273645655342,
    "validation_rmse": 0.04927212237994203,
    "features": [
      "precipitation_mean_mm",
      "soil_moisture_0_7cm_mean",
      "soil_moisture_7_28cm_mean",
      "soil_moisture_28_100cm_mean",
      "temperature_2m_mean_c",
      "agricultural_aeti_weighted_mm",
      "ret_mean_mm_dekad",
      "water_balance_ret_minus_rain",
      "water_balance_aeti_minus_rain",
      "aeti_ret_ratio",
      "rainfall_sum_3dekad",
      "rainfall_sum_6dekad",
      "soil_moisture_0_7cm_mean_3dekad",
      "aeti_mean_3dekad",
      "ret_mean_3dekad",
      "season_sin",
      "season_cos"
    ]
  },
  "state_aware": {
    "model": "ridge",
    "validation_mae": 0.022655048010401767,
    "validation_rmse": 0.034488186559744345,
    "features": [
      "precipitation_mean_mm",
      "soil_moisture_0_7cm_mean",
      "soil_moisture_7_28cm_mean",
      "soil_moisture_28_100cm_mean",
      "temperature_2m_mean_c",
      "agricultural_aeti_weighted_mm",
      "ret_mean_mm_dekad",
      "water_balance_ret_minus_rain",
      "water_balance_aeti_minus_rain",
      "aeti_ret_ratio",
      "rainfall_sum_3dekad",
      "rainfall_sum_6dekad",
      "soil_moisture_0_7cm_mean_3dekad",
      "aeti_mean_3dekad",
      "ret_mean_3dekad",
      "season_sin",
      "season_cos",
      "ndvi_t",
      "ndvi_lag_1",
      "ndvi_lag_2",
      "ndvi_lag_3"
    ]
  }
}

## Unseen 2024 evaluation

       family                  model  n      mae     rmse      bias
hydro_climate hist_gradient_boosting 35 0.030803 0.046872 -0.027537
  state_aware                  ridge 35 0.018340 0.028194 -0.004242

## Leakage controls

- chronological train/validation/test split
- explicit t → t+1 forecasting structure
- future targets excluded from predictors
- no random temporal shuffling
- no future NDVI interpolation
- 2024 excluded from model selection
- candidate selection based on validation data only

## Reproducibility

The repository preserves processing scripts, QA outputs, feature definitions, temporal splits, baseline results, candidate-model validation results, final predictions, and unseen-period evaluation metrics.
