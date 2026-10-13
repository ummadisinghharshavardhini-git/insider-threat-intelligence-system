from pymongo import MongoClient


# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["itbis"]

combined_anomalies = db["combined_anomaly_logs"]


# Get all combined anomalies
anomalies = list(combined_anomalies.find({}))

if not anomalies:
    print("No combined anomalies found.")
    exit()


# Group anomalies by employee
employee_summary = {}

for anomaly in anomalies:

    employee_id = anomaly["employee_id"]
    source = anomaly["source"]

    if employee_id not in employee_summary:
        employee_summary[employee_id] = {
            "rule_based_anomalies": 0,
            "ml_anomalies": 0,
            "total_anomalies": 0
        }

    if source == "rule_based":
        employee_summary[employee_id]["rule_based_anomalies"] += 1

    elif source == "machine_learning":
        employee_summary[employee_id]["ml_anomalies"] += 1

    employee_summary[employee_id]["total_anomalies"] += 1


# Display summary
print("Combined Risk Summary:")
print()

for employee_id, summary in employee_summary.items():

    print("Employee:", employee_id)
    print(
        "Rule-based anomalies:",
        summary["rule_based_anomalies"]
    )
    print(
        "ML anomalies:",
        summary["ml_anomalies"]
    )
    print(
        "Total anomalies:",
        summary["total_anomalies"]
    )
    print()
