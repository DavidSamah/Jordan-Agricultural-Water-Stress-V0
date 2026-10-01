import requests

MAPSET = "L1-RET-D"

BASE = (
    "https://data.apps.fao.org/gismgr/api/v2/"
    "catalog/workspaces/WAPOR-3/mapsets"
)

URL = f"{BASE}/{MAPSET}/rasters"

def collect(url):
    data = {
        "links": [{"rel": "next", "href": url}]
    }

    items = []

    while "next" in [
        x["rel"] for x in data["links"]
    ]:

        next_url = [
            x["href"]
            for x in data["links"]
            if x["rel"] == "next"
        ][0]

        print("Requesting:", next_url)

        r = requests.get(
            next_url,
            timeout=120
        )

        print("HTTP:", r.status_code)
        r.raise_for_status()

        data = r.json()["response"]
        items.extend(data["items"])

    return items


items = collect(URL)

print("\nTotal RET rasters:", len(items))

matches = [
    x for x in items
    if "2018-01" in x.get("code", "")
]

print("\nJanuary 2018:")

for item in matches:
    print(
        item.get("code"),
        item.get("downloadUrl")
    )

if not matches:
    raise SystemExit(
        "STOP: no 2018 RET rasters found"
    )

print("\nPASS: WaPOR RET discovered")
