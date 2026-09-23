from pystac_client import Client
import planetary_computer
import json
from pathlib import Path

BBOX = [35.3, 32.0, 35.8, 33.3]

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1"
)

search = catalog.search(
    collections=["esa-worldcover"],
    bbox=BBOX,
    datetime="2021-01-01/2021-12-31"
)

items = list(search.items())

print("Items found:", len(items))

if not items:
    raise SystemExit("STOP: no WorldCover items found")

Path("v1/data/worldcover/logs").mkdir(
    parents=True,
    exist_ok=True
)

for i, item in enumerate(items, start=1):
    signed = planetary_computer.sign(item)

    print("\nITEM", i)
    print("ID:", signed.id)
    print("BBox:", signed.bbox)

    print("Assets:")
    for key, asset in signed.assets.items():
        print(" ", key, "->", asset.href)

    Path(
        f"v1/data/worldcover/logs/item_{i}.json"
    ).write_text(
        json.dumps(signed.to_dict(), indent=2),
        encoding="utf-8"
    )

print("\nPASS: WorldCover discovery")
