from pystac_client import Client

BBOX = [35.3, 32.0, 35.8, 33.3]

catalog = Client.open(
    "https://earth-search.aws.element84.com/v1"
)

tests = [
    ("2018-01", "2018-01-01/2018-01-31"),
    ("2018-Q1", "2018-01-01/2018-03-31"),
    ("2018-full", "2018-01-01/2018-12-31"),
]

for label, period in tests:

    print("\n" + "=" * 70)
    print("TEST:", label)
    print("PERIOD:", period)

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=BBOX,
        datetime=period
    )

    items = list(search.items())

    print("Items found:", len(items))

    if items:

        items.sort(
            key=lambda item:
            item.properties.get(
                "eo:cloud_cover",
                100
            )
        )

        for item in items[:5]:

            print("\nID:", item.id)

            print(
                "Datetime:",
                item.datetime
            )

            print(
                "Cloud:",
                item.properties.get(
                    "eo:cloud_cover"
                )
            )

            print(
                "Assets:",
                sorted(
                    item.assets.keys()
                )
            )

        break

else:

    raise SystemExit(
        "STOP: no Sentinel-2 scenes found "
        "even after full-year search"
    )

print(
    "\nPASS: Sentinel-2 archive discovered"
)
