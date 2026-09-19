# Experiment V0

## Study area
Northern Jordan Valley

## Period
2018-01-01 to 2024-12-31

## Spatial unit
Approximately 10 km grid

## Temporal unit
Monthly

## Predictors

- GPM IMERG precipitation
- SMAP soil moisture
- MODIS NDVI
- MODIS land-surface temperature
- WaPOR actual evapotranspiration

## Candidate target

Agricultural water stress

## Prediction structure

Environmental conditions through month t

        ↓

Model

        ↓

Predict water stress at t+1

## Baseline

Single conventional drought indicator.

## Experimental comparison

Baseline
vs
multi-sensor ML model

## Status

Feasible in principle.
Exact target definition and boundary still unresolved.
