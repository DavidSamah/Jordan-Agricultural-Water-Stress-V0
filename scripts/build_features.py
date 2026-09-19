import pandas as pd
import numpy as np

PATH = "data/processed_v0/model_dataset.csv"
OUT = "data/processed_v0/model_dataset_lagged.csv"

df = pd.read_csv(PATH, parse_dates=["time"])
df = df.sort_values("time").reset_index(drop=True)

base = [
    "precipitation_mm",
    "soil_moisture_m3_m3",
    "temperature_2m_c"
]

for col in base:
    df[f"{col}_lag1"] = df[col].shift(1)

df["month_sin"] = np.sin(
    2 * np.pi * df["month"] / 12
)

df["month_cos"] = np.cos(
    2 * np.pi * df["month"] / 12
)

df = df.dropna().reset_index(drop=True)

df.to_csv(OUT, index=False)

print(df.head())
print("\nRows:", len(df))
print("\nTarget distribution:")
print(df["target_stress_next_month"].value_counts())

print("\nPASS: lagged feature table created")
