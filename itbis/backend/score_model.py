import joblib

from app.ml_features import build_feature_table


MODEL_PATH = "models/isolation_forest.pkl"

FEATURE_COLUMNS = [
    "avg_login_hour",
    "file_activity_count",
    "total_data_volume",
    "unique_devices",
    "unique_applications",
    "total_events"
]


# Load trained model
model = joblib.load(MODEL_PATH)

# Build current feature table
df = build_feature_table()

if df.empty:
    print("No data available for scoring.")
    exit()

# Prepare features
X = df[FEATURE_COLUMNS]

# Predict anomaly
df["ml_prediction"] = model.predict(X)

# Isolation Forest score
df["ml_score"] = model.decision_function(X)

# Convert prediction to readable label
df["ml_anomaly"] = df["ml_prediction"].apply(
    lambda x: True if x == -1 else False
)

print("ML Scoring Result:")
print(
    df[
        [
            "employee_id",
            "date",
            "ml_score",
            "ml_prediction",
            "ml_anomaly"
        ]
    ].to_string(index=False)
)