from pystac_client import Client
import planetary_computer

import rasterio
from rasterio.windows import from_bounds
from rasterio.merge import merge
from rasterio.io import MemoryFile

from pathlib import Path
import numpy as np

WEST = 35.3
SOUTH = 32.0
EAST = 35.8
NORTH = 33.3

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1"
)

search = catalog.search(
    collections=["esa-worldcover"],
    bbox=[WEST, SOUTH, EAST, NORTH],
    datetime="2021-01-01/2021-12-31"
)

items = [
    planetary_computer.sign(item)
    for item in search.items()
]

if not items:
    raise SystemExit("STOP: no WorldCover items")

datasets = []
memfiles = []

for item in items:
    if "map" not in item.assets:
        raise SystemExit(
            f"STOP: item {item.id} has no map asset"
        )

    url = item.assets["map"].href

    print("Opening:", item.id)

    with rasterio.open(url) as src:
        window = from_bounds(
            WEST,
            SOUTH,
            EAST,
            NORTH,
            transform=src.transform
        )

        window = window.round_offsets().round_lengths()

        data = src.read(
            1,
            window=window,
            boundless=True,
            fill_value=src.nodata
        )

        transform = src.window_transform(window)

        profile = src.profile.copy()
        profile.update(
            width=data.shape[1],
            height=data.shape[0],
            transform=transform
        )

        mem = MemoryFile()
        ds = mem.open(**profile)
        ds.write(data, 1)

        memfiles.append(mem)
        datasets.append(ds)

mosaic, transform = merge(
    datasets,
    bounds=(WEST, SOUTH, EAST, NORTH)
)

out = Path(
    "v1/data/worldcover/processed/"
    "worldcover_2021_northern_jordan_valley.tif"
)

out.parent.mkdir(
    parents=True,
    exist_ok=True
)

profile = datasets[0].profile.copy()

profile.update(
    height=mosaic.shape[1],
    width=mosaic.shape[2],
    transform=transform,
    count=1,
    compress="deflate"
)

with rasterio.open(out, "w", **profile) as dst:
    dst.write(mosaic[0], 1)

for ds in datasets:
    ds.close()

for mem in memfiles:
    mem.close()

values, counts = np.unique(
    mosaic[0],
    return_counts=True
)

print("\nClasses present:")

for value, count in zip(values, counts):
    print(
        int(value),
        int(count)
    )

print("\nSaved:", out)
print("PASS: WorldCover subset created")
