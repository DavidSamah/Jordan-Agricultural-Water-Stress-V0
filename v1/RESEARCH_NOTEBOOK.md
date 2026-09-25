# V1 Research Notebook — Jordan Agricultural Water Demand Forecasting

## Research direction

V1 moves beyond detecting shallow-soil-moisture stress toward the more practical question:

> Can environmental and remote-sensing variables help forecast when and where agricultural water demand is likely to rise before visible crop stress appears?

The purpose is not to label every dry condition as irrigation need. The target must have a clear physical or operational interpretation.

## Working principle

The V1 state is being built from:

- precipitation — water input
- soil moisture — stored water state
- reference evapotranspiration — atmospheric demand
- actual evapotranspiration and interception — actual water consumption
- vegetation state — crop/vegetation response
- cropland fraction — agricultural spatial context

Ground-truth irrigation delivery or field observations remain the preferred validation source.

## Target hierarchy

### Strongest target
Actual irrigation delivery or field-observed irrigation event.

### Intermediate physical targets
Measured or physically estimated crop-water deficit.

### Remote-sensing-supported target
AETI + RET + precipitation + soil moisture + vegetation response.

### Proxy only
Low soil moisture + high evaporative demand + vegetation deterioration.

**Rule:** do not claim "irrigation need" unless the label has a clear physical or operational interpretation.

---

## Step 1 — WaPOR AETI

Verified product:

- FAO WaPOR v3
- mapset: `L2-AETI-D`
- Actual Evapotranspiration and Interception
- 100 m
- dekadal
- raster CRS: EPSG:4326
- nodata: -9999
- scale: 0.1
- unit: mm/day

Initial test raster:

`WAPOR-3.L2-AETI-D.2018-01-D1`

Study box:

- west: 35.3
- south: 32.0
- east: 35.8
- north: 33.3

Successful test extraction:

- shape: 1331 × 512
- valid pixels: 681,472
- raw min: 0
- raw mean: 3.8712
- raw median: 3
- raw max: 21

The stored integer values must be converted using the verified scale factor before interpretation.

For D1:

`AETI_mm_day = raw × 0.1`

and:

`AETI_mm_dekad = AETI_mm_day × number_of_days_in_dekad`

Important: the third dekad is not always 10 days.

---

## Step 2 — Agricultural mask

V1 uses ESA WorldCover 2021 v200 as a structural cropland mask.

Important interpretation:

WorldCover 2021 indicates which pixels were classified as cropland in 2021.

It does **not** provide:

- annual crop history for 2018–2024
- irrigation records
- crop type history
- proof that every cropland pixel was irrigated

The intended processing is:

10 m cropland classification
→ binary cropland raster
→ average aggregation to WaPOR grid
→ fractional cropland coverage per WaPOR pixel

Agricultural AETI is then computed using cropland-fraction weighting instead of averaging the entire geographic rectangle.

---

## Step 3 — Reference evapotranspiration

Verified WaPOR mapset:

`L1-RET-D`

Metadata:

- measure: Reference Evapotranspiration
- unit: mm/day
- scale: 0.1
- offset: 0.0

Conversion:

`RET_mm_day = raw_RET × 0.1`

`RET_mm_dekad = RET_mm_day × number_of_days_in_dekad`

RET is treated as atmospheric demand, not as irrigation requirement.

Candidate diagnostics:

- AETI / RET
- RET - AETI

These are diagnostic features only.

---

## Step 4 — Dekadal water-state dataset

V1 is moving all major variables onto the same dekadal timeline.

Planned/constructed components:

- CHIRPS v3 dekadal precipitation
- ERA5-Land soil moisture
  - 0–7 cm
  - 7–28 cm
  - 28–100 cm
- ERA5-Land 2 m temperature
- WaPOR agricultural AETI
- WaPOR RET

Conceptually:

precipitation
+ soil-water storage
+ atmospheric demand
+ actual agricultural water use
→ water-state representation

This dataset is a feature/state dataset, not yet ground truth.

---

## Step 5 — Sentinel-2 vegetation response

Goal:

Test whether water-state deterioration occurs before vegetation condition deteriorates.

Chosen inputs:

- Sentinel-2 Level-2A
- Red
- NIR
- Scene Classification Layer (SCL)

NDVI:

`NDVI = (NIR - RED) / (NIR + RED)`

### Discovery result

January 2018 returned zero L2A scenes for the provisional study box.

Q1 2018 returned 14 scenes.

This established an important methodological rule:

**zero search results do not prove data absence.**

A broader search recovered valid imagery.

### First successful scene

`S2B_37SBS_20180302_0_L2A`

Date:

2018-03-02

Cloud metadata:

0.267599

Assets confirmed:

- red
- nir
- scl

### Bug 12 — CRS mismatch

Initial failure:

`Invalid dataset dimensions: 0 x 0`

Cause:

The study bbox was specified in EPSG:4326 longitude/latitude, while the Sentinel raster used projected UTM coordinates.

Fix:

EPSG:4326 bbox
→ `transform_bounds()`
→ Sentinel CRS
→ `from_bounds()`

Research lesson:

Same geographic area does not imply the same coordinate numbers.

### Bug 13 — tile footprint mismatch

The transformed study box extended outside the selected Sentinel tile.

Requested projected bounds began at approximately:

150,408 m east

but the tile began at:

199,980 m east

The raster read was silently clipped while the original window transform was retained, causing red/NIR/SCL grid disagreement.

Fix:

study bbox
→ project to scene CRS
→ intersect with raster bounds
→ compute clipped window
→ use that exact target grid

### Successful NDVI extraction

For the actual tile intersection:

- target shape: 10044 × 204
- valid RED pixels: 884,912
- valid NIR pixels: 884,912
- good SCL pixels: 867,656
- combined valid pixels: 867,656
- valid fraction: 0.42346
- NDVI min: -0.98413
- NDVI mean: 0.56355
- NDVI median: 0.63584
- NDVI max: 0.99840

The NDVI range is physically valid.

The negative minimum is not automatically a problem because the tile has not yet been restricted to cropland; water, bare ground and other surfaces remain present.

---

## Current next step

A single Sentinel tile is not the study region.

The next processing stage is:

same acquisition date
→ identify all intersecting Sentinel-2 tiles
→ cloud-mask each tile
→ calculate NDVI
→ reproject to common WaPOR grid
→ mosaic valid observations
→ apply cropland-fraction weighting
→ calculate agricultural NDVI
→ assign the observation to its dekad

Missing satellite observations will remain missing rather than being invented or interpolated as if observed.

---

## Research philosophy

Terminal = evidence collection.

Notebook = reasoning.

Working chain:

QUESTION
→ SEARCH
→ SOURCE
→ VERIFICATION
→ EXTRACTION
→ COMPARISON
→ INFERENCE
→ FALSIFICATION
→ RESEARCH GAP

Important rules:

- finding a dataset is not verifying a dataset
- a script running is not proof of scientific validity
- zero search results do not prove absence
- missing data should not be silently converted into zero
- future information must not leak into prediction features
- proxy variables must remain labeled as proxies
- predictive performance must be compared with temporal baselines
- physical interpretation comes before model complexity

## Status

V1 is currently in data construction and physical-validation mode.

No V1 predictive model has been trained yet.

That is deliberate.
