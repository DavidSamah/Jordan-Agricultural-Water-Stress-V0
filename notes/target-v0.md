# Step 47 — Target V0

## Objective

Predict an agricultural stress proxy one month ahead.

## Inputs

Environmental observations available through month t:

- precipitation
- soil moisture
- land-surface temperature
- evapotranspiration
- historical vegetation condition

## Target

Vegetation stress during month t+1.

## Proposed representation

Calculate vegetation anomaly relative to the expected
seasonal vegetation condition for the same location
and time of year.

Stress = unusually negative future vegetation anomaly.

## Prediction horizon

1 month.

## Important limitation

Vegetation stress is not uniquely caused by water stress.

Potential confounders include:
- heat
- crop phenology
- harvest
- disease
- land-use changes
- management practices

Therefore this is initially treated as an agricultural
water-stress proxy rather than direct ground truth.

## Leakage rule

No information from month t+1 may appear in the predictor
variables used to predict month t+1.
