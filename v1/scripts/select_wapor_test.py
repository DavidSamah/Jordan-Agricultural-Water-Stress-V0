import requests
from pathlib import Path

BASE = (
    "https://data.apps.fao.org/gismgr/api/v2/"
    "catalog/workspaces/WAPOR-3/mapsets/"
    "L2-AETI-D/rasters"
)

data = {
    "links": [
        {"rel": "next", "href": BASE}
    ]
}

selected = None

while "next" in [
    x["rel"] for x in data["links"]
]:

    url = [
        x["href"]
        for x in data["links"]
        if x["rel"] == "next"
    ][0]

    r = requests.get(url, timeout=120)
    r.raise_for_status()

    data = r.json()["response"]

    for item in data["items"]:
        if (
            item.get("code")
            == "WAPOR-3.L2-AETI-D.2018-01-D1"
        ):
            selected = item
            break

    if selected:
        break

if selected is None:
    raise SystemExit(
        "STOP: test raster not found"
    )

url = selected.get("downloadUrl")

if not url:
    raise SystemExit(
        "STOP: raster has no downloadUrl"
    )

Path(
    "v1/data/wapor/logs/"
    "aeti-test-url.txt"
).write_text(
    url + "\n",
    encoding="utf-8"
)

print("Raster:", selected["code"])
print("URL:", url)
print("\nPASS: test raster selected")
