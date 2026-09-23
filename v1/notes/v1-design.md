# V1 Design

## Inputs

Weather:
- precipitation
- air temperature
- humidity
- wind
- solar radiation

Water state:
- soil moisture

Remote sensing:
- NDVI/EVI
- land-surface temperature
- evapotranspiration / AETI
- vegetation condition

Agricultural context:
- crop type
- crop growth stage
- soil characteristics

## Derived quantities

Reference evapotranspiration:
ET0

Crop evapotranspiration:
ETc = Kc * ET0

Water balance concept:

Irrigation requirement
≈ crop evapotranspiration
- effective precipitation
- usable soil-water contribution

## Forecast

X(t)
    ↓
water-balance state
    ↓
forecast model
    ↓
irrigation need at t + horizon

## V1 objective

Predict irrigation need early enough to act
before visible crop stress occurs.
