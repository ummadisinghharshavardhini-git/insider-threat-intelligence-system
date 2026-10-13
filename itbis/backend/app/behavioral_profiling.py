from datetime import datetime, timezone
from pymongo import MongoClient
from collections import Counter, defaultdict
import statistics


# MongoDB connection
client = MongoClient("mongodb://localhost:27017")

db = client["itbis"]

behavior_logs = db["behavior_logs"]
behavior_baselines = db["behavior_baselines"]


# Get all activity logs for one employee
def get_employee_logs(employee_id):
    return list(
        behavior_logs.find(
            {"employee_id": employee_id}
        ).sort("timestamp", 1)
    )


# Calculate behavioral baseline
def calculate_baseline(employee_id):

    logs = get_employee_logs(employee_id)

    if not logs:
        return {
            "employee_id": employee_id,
            "message": "No activity logs found"
        }

    # 1. Login Times
    login_times = []

    # 2. Resource Access Frequency
    resource_access_by_day = defaultdict(int)

    # 3. Device Usage
    devices = []

    # 4. Application Usage
    applications = []

    # 5. Data Transfer Volume
    data_transfer = []

    # 6. Communication Patterns
    communication_count = 0

    # Process every activity log
    for log in logs:

        activity = log.get("activity", "")
        timestamp = log.get("timestamp")

        # Login Times
        if activity == "login" and timestamp:
            login_times.append(
                timestamp.hour * 60 + timestamp.minute
            )

        # Resource Access Frequency
        if activity in [
            "file_access",
            "system_access",
            "resource_access"
        ] and timestamp:
            day = timestamp.date()
            resource_access_by_day[day] += 1

        # Device Usage
        if log.get("device"):
            devices.append(
                log.get("device")
            )

        # Application Usage
        if activity in [
            "app_usage",
            "application_access"
        ]:
            applications.append(
                log.get("application", "unknown")
            )

        # Data Transfer Volume
        if activity in [
            "file_upload",
            "file_download"
        ]:
            data_transfer.append(
                log.get("data_volume", 0)
            )

        # Communication Patterns
        if activity in [
            "email_sent",
            "message_sent"
        ]:
            communication_count += 1

    # Create baseline
    baseline = {

        "employee_id": employee_id,

        # Login Time Baseline
        "login_times": {
            "average_minutes": (
                statistics.mean(login_times)
                if len(login_times) >= 5 else None
            ),
            "standard_deviation": (
                statistics.stdev(login_times)
                if len(login_times) >= 5 else None
            ),
            "sample_size": len(login_times),
            "status": (
                "baseline_ready"
                if len(login_times) >= 5
                else "insufficient_data"
            )
        },

        # Resource Access Baseline
        "resource_access": {
            "average_per_day": (
                statistics.mean(
                    list(resource_access_by_day.values())
                )
                if resource_access_by_day else 0
            ),
            "standard_deviation": (
                statistics.stdev(
                    list(resource_access_by_day.values())
                )
                if len(resource_access_by_day) > 1 else 0
            ),
            "sample_size": len(resource_access_by_day),
            "total": sum(resource_access_by_day.values())
        },

        "device_usage": {
            "typical_device": (
                Counter(devices).most_common(1)[0][0]
                if devices else "unknown"
            ),
            "device_usage_count": len(devices),
            "unique_devices": len(set(devices)),
            "sample_size": len(devices),
            "status": (
                "baseline_ready"
                if len(devices) >= 5
                else "insufficient_data"
            )
        },

        # Application Usage Baseline
        "application_usage": {
            "typical_application": (
                Counter(applications).most_common(1)[0][0]
                if applications else "unknown"
            ),
            "application_usage_count": len(applications),
            "unique_applications": len(set(applications)),
            "sample_size": len(applications),
            "status": (
                "baseline_ready"
                if len(applications) >= 5
                else "insufficient_data"
            )
        },

        # Data Transfer Baseline
        "data_transfer": {
            "average_data_volume": (
                statistics.mean(data_transfer)
                if len(data_transfer) >= 5 else None
            ),
            "standard_deviation": (
                statistics.stdev(data_transfer)
                if len(data_transfer) >= 5 else None
            ),
            "sample_size": len(data_transfer),
            "status": (
                "baseline_ready"
                if len(data_transfer) >= 5
                else "insufficient_data"
            )
        },

        # Communication Patterns Baseline
        "communication_patterns": {
            "average_per_day": communication_count / 7,
            "sample_size": communication_count,
            "status": (
                "baseline_ready"
                if communication_count >= 5
                else "insufficient_data"
            )
        },

        "total_activities": len(logs),

        # Current UTC time
        "created_at": datetime.now(timezone.utc)
    }

    # Save baseline to MongoDB
    behavior_baselines.update_one(
        {"employee_id": employee_id},
        {"$set": baseline},
        upsert=True
    )

    return baseline


# Test the baseline calculation
if __name__ == "__main__":
    result = calculate_baseline("EMP001")
    print(result)
