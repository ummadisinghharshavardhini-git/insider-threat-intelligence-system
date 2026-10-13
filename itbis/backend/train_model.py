import os
import joblib
from sklearn.ensemble import IsolationForest

from app.ml_features import build_feature_table


# Build feature table
df = build_feature_table()

if df.empty:
    print("No feature data available for training.")
    exit()

# Features used by the ML model
FEATURE_COLUMNS = [
    "avg_login_hour",
    "file_activity_count",
    "total_data_volume",
    "unique_devices",
    "unique_applications",
    "total_events"
]

X = df[FEATURE_COLUMNS]

# Train Isolation Forest
model = IsolationForest(
    n_estimators=100,
    contamination=0.10,
    random_state=42
)

model.fit(X)

# Create models directory
os.makedirs("models", exist_ok=True)

# Save trained model
model_path = "models/isolation_forest.pkl"
joblib.dump(model, model_path)

print("Model training completed.")
print("Training records:", len(X))
print("Model saved to:", model_path)