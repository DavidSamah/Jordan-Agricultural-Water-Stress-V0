import requests
from pathlib import Path

URL = (
    "https://data.apps.fao.org/gismgr/api/v2/"
    "catalog/workspaces/WAPOR-3/mapsets/"
    "L1-RET-D/rasters"
)

TARGET = "WAPOR-3.L1-RET-D.2018-01-D1"

data = {
    "links": [{"rel": "next", "href": URL}]
}

found = None

while "next" in [
    x["rel"] for x in data["links"]
]:

    next_url = [
        x["href"]
        for x in data["links"]
        if x["rel"] == "next"
    ][0]

    r = requests.get(
        next_url,
        timeout=120
    )

    r.raise_for_status()

    data = r.json()["response"]

    for item in data["items"]:
        if item.get("code") == TARGET:
            found = item
            break

    if found:
        break

if found is None:
    raise SystemExit(
        "STOP: target RET raster not found"
    )

download = found.get("downloadUrl")

if not download:
    raise SystemExit(
        "STOP: RET raster has no download URL"
    )

out = Path(
    "v1/data/wapor_ret/logs/"
    "ret-test-url.txt"
)

out.write_text(
    download + "\n",
    encoding="utf-8"
)

print("Raster:", TARGET)
print("URL:", download)

print("\nPASS: RET test raster selected")
