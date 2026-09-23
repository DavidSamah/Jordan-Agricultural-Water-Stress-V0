import requests

BASE = (
    "https://data.apps.fao.org/gismgr/api/v2/"
    "catalog/workspaces/WAPOR-3/mapsets"
)

MAPSET = "L2-AETI-D"
URL = f"{BASE}/{MAPSET}/rasters"

def collect_responses(url):
    data = {
        "links": [
            {"rel": "next", "href": url}
        ]
    }

    output = []

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

        output.extend(data["items"])

    return output


rasters = collect_responses(URL)

print("\nTotal rasters:", len(rasters))

matches = [
    r for r in rasters
    if "2018-01" in r.get("code", "")
]

print("\n2018 January AETI rasters:")

for r in matches:
    print(
        r.get("code"),
        r.get("downloadUrl")
    )

if not matches:
    raise SystemExit(
        "STOP: no January 2018 AETI rasters found"
    )

print("\nPASS: WaPOR AETI catalog discovery")
