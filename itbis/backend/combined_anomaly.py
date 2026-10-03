from pymongo import MongoClient


# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["itbis"]

# Collections
rule_anomalies = db["anomaly_logs"]
ml_anomalies = db["ml_anomaly_logs"]
combined_anomalies = db["combined_anomaly_logs"]


# Get rule-based anomalies
rule_results = list(
    rule_anomalies.find({"anomaly": True})
)


# Get ML anomalies
ml_results = list(
    ml_anomalies.find({"ml_prediction": -1})
)


# Clear only previous combined results
combined_anomalies.delete_many({})


# Store rule-based anomalies
for item in rule_results:

    combined_anomalies.insert_one({
        "employee_id": item["employee_id"],
        "date": item.get("detected_at"),
        "source": "rule_based",
        "anomaly": True
    })


# Store ML anomalies
for item in ml_results:

    combined_anomalies.insert_one({
        "employee_id": item["employee_id"],
        "date": item.get("date"),
        "source": "machine_learning",
        "anomaly": True
    })


print("Combined anomaly results stored successfully.")
print("Rule-based anomalies:", len(rule_results))
print("ML anomalies:", len(ml_results))
print(
    "Total combined anomalies:",
    combined_anomalies.count_documents({})
)
