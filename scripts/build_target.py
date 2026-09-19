import pandas as pd

PATH = "data/processed_v0/features_complete.csv"
OUT = "data/processed_v0/model_dataset.csv"

df = pd.read_csv(PATH, parse_dates=["time"])
df = df.sort_values("time").reset_index(drop=True)

# Learn stress thresholds ONLY from training years.
train_reference = df[df["time"].dt.year <= 2022].copy()

thresholds = (
    train_reference
    .groupby("month")["soil_moisture_m3_m3"]
    .quantile(0.25)
    .rename("stress_threshold")
)

# Apply the training-derived thresholds to every year.
df = df.join(thresholds, on="month")

if df["stress_threshold"].isna().any():
    raise SystemExit("STOP: missing monthly stress thresholds")

df["current_stress"] = (
    df["soil_moisture_m3_m3"]
    < df["stress_threshold"]
).astype(int)

df["target_stress_next_month"] = (
    df["current_stress"].shift(-1)
)

# Diagnostic only — never a model feature.
df["soil_moisture_next_month"] = (
    df["soil_moisture_m3_m3"].shift(-1)
)

df = df.dropna(
    subset=["target_stress_next_month"]
).copy()

df["target_stress_next_month"] = (
    df["target_stress_next_month"].astype(int)
)

df.to_csv(OUT, index=False)

print("TRAINING-DERIVED MONTHLY THRESHOLDS:")
print(thresholds)

print("\nRows:", len(df))
print("Stress events:", int(df["target_stress_next_month"].sum()))
print("Stress rate:", df["target_stress_next_month"].mean())

print("\nStress events by year:")
print(
    df.groupby(df["time"].dt.year)
      ["target_stress_next_month"]
      .agg(["sum", "count", "mean"])
)

print("\nPASS: leakage-safe model_dataset.csv created")
