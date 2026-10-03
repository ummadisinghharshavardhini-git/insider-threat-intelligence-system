from sklearn.ensemble import IsolationForest

from app.ml_features import build_feature_table


FEATURE_COLUMNS = [
    "avg_login_hour",
    "file_activity_count",
    "total_data_volume",
    "unique_devices",
    "unique_applications",
    "total_events"
]

df = build_feature_table()

if df.empty:
    print("No feature data available.")
    exit()

X = df[FEATURE_COLUMNS]

# Test contamination against the current rule-based output
model = IsolationForest(
    n_estimators=100,
    contamination=0.20,
    random_state=42
)

model.fit(X)

df["ml_prediction"] = model.predict(X)
df["ml_anomaly"] = df["ml_prediction"].apply(
    lambda x: x == -1
)

print("Tuned ML Result:")
print(
    df[
        [
            "employee_id",
            "date",
            "ml_prediction",
            "ml_anomaly"
        ]
    ].to_string(index=False)
)

print("\nTotal ML anomalies:", df["ml_anomaly"].sum())
print("Rule-based anomalies: 2")