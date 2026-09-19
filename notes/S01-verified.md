# S01 Verified Methodology

## Scope
Jordan and Syria

## Problem
Agricultural drought monitoring in semi-arid environments.

## Data
- MODIS
- GPM
- SMAP
- Sentinel-1A

## Indicators
- VCI
- TCI
- ETCI
- PCI
- SMCI
- VHI

## Machine learning
Random Forest was used to estimate the relative importance
of drought-condition indices using SPI as the reference.

## Selected indices
- PCI
- TCI
- VCI

## Validation
CADCI was evaluated using SPI-1 and SPI-3.

## Reported performance
Jordan:
- Overall accuracy: 85%
- Kappa: 0.80

Syria:
- Overall accuracy: 83%
- Kappa: 0.76

## Candidate unresolved questions
- Monitoring versus forecasting
- Field/ground validation
- Learned fusion versus fixed thresholds
- Geographic generalization
- Crop-specific performance
- Irrigated versus rainfed conditions

## Epistemic status
Methodology verified from reconstructed abstract.
Research gap not yet established.
