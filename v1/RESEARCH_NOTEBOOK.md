
## Step 5B — Multi-tile Sentinel-2 mosaic test

Test date:

2018-03-02

Scenes discovered:

5

Target grid:

FAO WaPOR grid
EPSG:4326
1331 × 512

Results:

- valid mosaic pixels: 672,171
- coverage fraction: 0.98635
- agricultural pixels with valid NDVI: 282,610
- crop-equivalent pixel weight: 144,190.08
- cropland-weighted NDVI: 0.61319
- unweighted agricultural mean NDVI: 0.56620
- median agricultural NDVI: 0.58078

Interpretation:

The study area crosses multiple Sentinel-2 tiles.

Processing all intersecting scenes and projecting them onto
the common WaPOR grid produced almost complete spatial coverage.

Cropland-fraction weighting changes the regional vegetation
signal compared with a simple unweighted mean.

Important:

This is one vegetation observation date only.

It is not yet a time series and is not evidence of irrigation need.

Next step:

Build a Sentinel-2 observation ledger for 2018–2024.

For each actual acquisition date:

discover scenes
→ process all intersecting tiles
→ mosaic valid NDVI
→ apply cropland weighting
→ calculate agricultural NDVI
→ assign observation to dekad

Missing observation dates remain missing.
