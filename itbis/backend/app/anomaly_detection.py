from datetime import datetime, timezone
from pymongo import MongoClient


# =========================================================
# MongoDB CONNECTION
# =========================================================

client = MongoClient("mongodb://localhost:27017")

db = client["itbis"]

behavior_logs = db["behavior_logs"]
behavior_baselines = db["behavior_baselines"]
anomaly_logs = db["anomaly_logs"]
numeric_anomalies = db["numeric_anomalies"]
set_membership_anomalies = db["set_membership_anomalies"]


# =========================================================
# GET EMPLOYEE BASELINE
# =========================================================

def get_baseline(employee_id):
    return behavior_baselines.find_one(
        {"employee_id": employee_id}
    )


# =========================================================
# ORIGINAL LOGIN ANOMALY DETECTION
# =========================================================

def detect_login_anomaly(employee_id, login_time_minutes):

    baseline = get_baseline(employee_id)

    if not baseline:
        return {
            "employee_id": employee_id,
            "anomaly": False,
            "message": "No baseline found"
        }

    login_baseline = baseline.get("login_times", {})

    if login_baseline.get("status") != "baseline_ready":
        return {
            "employee_id": employee_id,
            "anomaly": False,
            "message": "Baseline has insufficient data"
        }

    average = login_baseline.get("average_minutes")
    standard_deviation = login_baseline.get(
        "standard_deviation"
    )

    if average is None or standard_deviation is None:
        return {
            "employee_id": employee_id,
            "anomaly": False,
            "message": "Invalid baseline"
        }

    threshold = average + (2 * standard_deviation)

    is_anomaly = abs(
        login_time_minutes - average
    ) > (2 * standard_deviation)

    result = {
        "employee_id": employee_id,
        "activity": "login",
        "login_time_minutes": login_time_minutes,
        "baseline_average": average,
        "baseline_standard_deviation": standard_deviation,
        "threshold": threshold,
        "anomaly": is_anomaly,
        "detected_at": datetime.now(timezone.utc)
    }

    anomaly_logs.insert_one(result)

    return result


# =========================================================
# SHARED NUMERIC ANOMALY DETECTOR
# =========================================================

def check_numeric_anomaly(employee_id, indicator, new_value):

    baseline = get_baseline(employee_id)

    if not baseline:
        return {
            "employee_id": employee_id,
            "indicator": indicator,
            "anomaly": False,
            "message": "No baseline yet - nothing to compare against"
        }

    # Map indicators to baseline sections
    baseline_map = {

        "login_hour":
            baseline.get("login_times", {}),

        "daily_download_mb":
            baseline.get("data_transfer", {}),

        "daily_transfer_count":
            baseline.get("communication_patterns", {}),

        "daily_resource_count":
            baseline.get("resource_access", {})
    }

    indicator_baseline = baseline_map.get(indicator)

    if not indicator_baseline:
        return {
            "employee_id": employee_id,
            "indicator": indicator,
            "anomaly": False,
            "message": "No baseline found for this indicator"
        }

    # Get typical value and spread
    if indicator == "login_hour":

        typical = indicator_baseline.get(
            "average_minutes"
        )

        spread = indicator_baseline.get(
            "standard_deviation"
        )

    elif indicator == "daily_download_mb":

        typical = indicator_baseline.get(
            "average_data_volume"
        )

        spread = indicator_baseline.get(
            "standard_deviation"
        )

    elif indicator == "daily_transfer_count":

        typical = indicator_baseline.get(
            "average_per_day"
        )

        spread = 0

    elif indicator == "daily_resource_count":

        typical = indicator_baseline.get(
            "average_per_day"
        )

        spread = indicator_baseline.get(
            "standard_deviation"
        )

    else:

        return {
            "employee_id": employee_id,
            "indicator": indicator,
            "anomaly": False,
            "message": "Unsupported indicator"
        }

    if typical is None:

        return {
            "employee_id": employee_id,
            "indicator": indicator,
            "anomaly": False,
            "message": "Invalid baseline"
        }

    # Prevent division by zero
    spread = max(
        float(spread or 0),
        0.1
    )

    deviation_ratio = (
        abs(float(new_value) - float(typical))
        / spread
    )

    # 3x spread = anomaly
    is_anomaly = deviation_ratio >= 3

    # Severity
    if deviation_ratio >= 5:
        severity = "high"

    elif deviation_ratio >= 3:
        severity = "medium"

    else:
        severity = "low"

    result = {

        "employee_id": employee_id,

        "indicator": indicator,

        "observed_value": new_value,

        "typical_value": typical,

        "spread": spread,

        "deviation_ratio": round(
            deviation_ratio,
            2
        ),

        "anomaly": is_anomaly,

        "severity": severity,

        "detected_at":
            datetime.now(timezone.utc)
    }

    # Store numeric anomaly
    numeric_anomalies.insert_one(result)

    return result


# =========================================================
# NUMERIC ANOMALY WRAPPERS
# =========================================================

def detect_login_duration_anomaly(
    employee_id,
    login_hour
):

    return check_numeric_anomaly(
        employee_id,
        "login_hour",
        login_hour
    )


def detect_download_anomaly(
    employee_id,
    daily_download_mb
):

    return check_numeric_anomaly(
        employee_id,
        "daily_download_mb",
        daily_download_mb
    )


def detect_transfer_frequency_anomaly(
    employee_id,
    daily_transfer_count
):

    return check_numeric_anomaly(
        employee_id,
        "daily_transfer_count",
        daily_transfer_count
    )


def detect_resource_access_anomaly(
    employee_id,
    daily_resource_count
):

    return check_numeric_anomaly(
        employee_id,
        "daily_resource_count",
        daily_resource_count
    )


# =========================================================
# SET-MEMBERSHIP ANOMALY DETECTOR
# =========================================================

def check_set_membership_anomaly(
    employee_id,
    field,
    new_value
):

    baseline = get_baseline(employee_id)

    if not baseline:

        return {
            "employee_id": employee_id,
            "field": field,
            "observed_value": new_value,
            "anomaly": False,
            "message": "No baseline yet"
        }

    # Device check
    if field == "device":

        known_value = baseline.get(
            "device_usage",
            {}
        ).get(
            "typical_device"
        )

    # Application check
    elif field == "application":

        known_value = baseline.get(
            "application_usage",
            {}
        ).get(
            "typical_application"
        )

    else:

        return {
            "employee_id": employee_id,
            "field": field,
            "observed_value": new_value,
            "anomaly": False,
            "message": "Unsupported field"
        }

    if known_value is None:

        return {
            "employee_id": employee_id,
            "field": field,
            "observed_value": new_value,
            "anomaly": False,
            "message": "No known value in baseline"
        }

    is_anomaly = new_value != known_value

    result = {

        "employee_id": employee_id,

        "field": field,

        "observed_value": new_value,

        "known_value": known_value,

        "anomaly": is_anomaly,

        "detected_at":
            datetime.now(timezone.utc)
    }

    # Store set-membership anomaly
    set_membership_anomalies.insert_one(result)

    return result


# =========================================================
# TESTING
# =========================================================

if __name__ == "__main__":

    result = detect_login_anomaly(
        employee_id="EMP001",
        login_time_minutes=600
    )

    print("Anomaly Detection Result:")
    print(result)
