# V1 Next Research Step

Priority order:

1. Acquire FAO WaPOR AETI / ET-related data
2. Acquire vegetation state data (NDVI/EVI)
3. Acquire land-surface temperature
4. Define a common spatial grid
5. Determine whether crop-type or agricultural-mask data are available
6. Search for irrigation-delivery or field-validation records
7. Only after these steps, define the final irrigation-need target

## Reason

V1 should not begin by training a model.

The first goal is to establish whether we can construct a physically meaningful
and independently defensible irrigation-demand target.

## Current strongest candidate predictors

- precipitation
- soil moisture
- air temperature
- AETI / actual ET
- reference ET / ET0
- vegetation state
- land-surface temperature

## Preferred validation hierarchy

1. actual irrigation delivery
2. measured crop-water deficit
3. field soil moisture / ET observations
4. crop or vegetation response
5. proxy-only target as last resort
