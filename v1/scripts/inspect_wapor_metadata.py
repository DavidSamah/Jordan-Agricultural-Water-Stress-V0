import json
import requests
from pathlib import Path

MAPSET = "L2-AETI-D"
RASTER = "WAPOR-3.L2-AETI-D.2018-01-D1"

base = (
    "https://data.apps.fao.org/gismgr/api/v2/"
    "catalog/workspaces/WAPOR-3/mapsets"
)

urls = {
    "mapset": f"{base}/{MAPSET}",
    "raster": f"{base}/{MAPSET}/rasters/{RASTER}",
}

Path("v1/data/wapor/logs").mkdir(parents=True, exist_ok=True)

for name, url in urls.items():
    print("\n" + "=" * 70)
    print(name.upper())
    print(url)

    r = requests.get(url, timeout=120)
    print("HTTP:", r.status_code)
    r.raise_for_status()

    data = r.json()

    out = Path(f"v1/data/wapor/logs/{name}-metadata.json")
    out.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(data, indent=2)[:12000])
    print("\nSaved:", out)

print("\nPASS: WaPOR metadata retrieved")
