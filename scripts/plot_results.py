import pandas as pd
import matplotlib.pyplot as plt

features = pd.read_csv(
    "data/processed_v0/features_complete.csv",
    parse_dates=["time"]
)

pred = pd.read_csv(
    "results/test_predictions_2024.csv",
    parse_dates=["time"]
)

imp = pd.read_csv(
    "results/feature_importance.csv"
)

plt.figure(figsize=(10,5))

plt.plot(
    features["time"],
    features["precipitation_mm"]
)

plt.xlabel("Time")
plt.ylabel("Precipitation (mm/month)")
plt.title(
    "Northern Jordan Valley precipitation, 2018–2024"
)

plt.tight_layout()

plt.savefig(
    "figures/precipitation_2018_2024.png",
    dpi=180
)

plt.close()


plt.figure(figsize=(10,5))

plt.plot(
    features["time"],
    features["soil_moisture_m3_m3"]
)

plt.xlabel("Time")
plt.ylabel("Soil moisture (m³/m³)")
plt.title(
    "Shallow soil moisture, 2018–2024"
)

plt.tight_layout()

plt.savefig(
    "figures/soil_moisture_2018_2024.png",
    dpi=180
)

plt.close()


plt.figure(figsize=(9,5))

plt.barh(
    imp["feature"][::-1],
    imp["importance"][::-1]
)

plt.xlabel(
    "Random Forest feature importance"
)

plt.title(
    "V0 feature importance"
)

plt.tight_layout()

plt.savefig(
    "figures/feature_importance.png",
    dpi=180
)

plt.close()


plt.figure(figsize=(9,5))

plt.plot(
    pred["time"],
    pred["target_stress_next_month"],
    marker="o",
    label="Observed stress"
)

plt.plot(
    pred["time"],
    pred["rf_probability"],
    marker="o",
    label="RF probability"
)

plt.xlabel("Time")
plt.ylabel("Stress / probability")

plt.title(
    "2024 held-out predictions"
)

plt.legend()
plt.tight_layout()

plt.savefig(
    "figures/test_predictions_2024.png",
    dpi=180
)

plt.close()

print(
    "PASS: figures generated"
)
