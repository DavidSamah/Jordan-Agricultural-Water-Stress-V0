import pandas as pd

df = pd.read_csv(
    "data/processed_v0/model_dataset_lagged.csv",
    parse_dates=["time"]
)

assert df["time"].is_monotonic_increasing
assert not df["time"].duplicated().any()

features = [
    "precipitation_mm",
    "soil_moisture_m3_m3",
    "temperature_2m_c",
    "precipitation_mm_lag1",
    "soil_moisture_m3_m3_lag1",
    "temperature_2m_c_lag1",
    "month_sin",
    "month_cos"
]

for forbidden in [
    "soil_moisture_next_month",
    "target_stress_next_month"
]:
    assert forbidden not in features

train = df[df.time.dt.year <= 2022]
val = df[df.time.dt.year == 2023]
test = df[df.time.dt.year == 2024]

assert train.time.max() < val.time.min()
assert val.time.max() < test.time.min()

print("PASS: temporal ordering")
print("PASS: no target included as feature")
print("PASS: no future soil moisture included as feature")
print("PASS: chronological split")
