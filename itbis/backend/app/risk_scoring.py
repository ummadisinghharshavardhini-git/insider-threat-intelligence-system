from datetime import datetime, timezone
from pymongo import MongoClient


# =========================================================
# MONGODB CONNECTION
# =========================================================

client = MongoClient("mongodb://localhost:27017")

db = client["itbis"]

anomaly_logs = db["anomaly_logs"]
numeric_anomalies = db["numeric_anomalies"]
set_membership_anomalies = db["set_membership_anomalies"]
ml_anomaly_logs = db["ml_anomaly_logs"]
risk_scores = db["risk_scores"]


# =========================================================
# RISK SCORE CALCULATION
# =========================================================

def calculate_risk_score(employee_id):

    # -----------------------------------------------------
    # 1. Existing behavioral anomalies
    # -----------------------------------------------------

    old_anomalies = list(
        anomaly_logs.find(
            {
                "employee_id": employee_id,
                "anomaly": True
            }
        )
    )

    # -----------------------------------------------------
    # 2. Numeric anomalies - Day 15
    # -----------------------------------------------------

    numeric_anomalies_list = list(
        numeric_anomalies.find(
            {
                "employee_id": employee_id,
                "anomaly": True
            }
        )
    )

    # -----------------------------------------------------
    # 3. Set-membership anomalies - Day 16
    # -----------------------------------------------------

    set_anomalies_list = list(
        set_membership_anomalies.find(
            {
                "employee_id": employee_id,
                "anomaly": True
            }
        )
    )

    # -----------------------------------------------------
    # 4. ML anomalies - Day 18
    # -----------------------------------------------------

    ml_anomalies_list = list(
        ml_anomaly_logs.find(
            {
                "employee_id": employee_id,
                "ml_prediction": -1
            }
        )
    )

    # -----------------------------------------------------
    # 5. Count all anomalies
    # -----------------------------------------------------

    old_count = len(old_anomalies)

    numeric_count = len(numeric_anomalies_list)

    set_count = len(set_anomalies_list)

    ml_count = len(ml_anomalies_list)

    total_anomaly_count = (
        old_count
        + numeric_count
        + set_count
        + ml_count
    )

    # -----------------------------------------------------
    # 6. Calculate risk score
    # -----------------------------------------------------

    # Each anomaly contributes 25 points
    risk_score = min(
        total_anomaly_count * 25,
        100
    )

    # -----------------------------------------------------
    # 7. Determine risk level
    # -----------------------------------------------------

    if risk_score >= 75:

        risk_level = "high"

    elif risk_score >= 50:

        risk_level = "medium"

    else:

        risk_level = "low"

    # -----------------------------------------------------
    # 8. Create result
    # -----------------------------------------------------

    result = {

        "employee_id": employee_id,

        "risk_score": risk_score,

        "risk_level": risk_level,

        "anomaly_count": total_anomaly_count,

        "old_anomalies": old_count,

        "numeric_anomalies": numeric_count,

        "set_membership_anomalies": set_count,

        "ml_anomalies": ml_count,

        "calculated_at":
            datetime.now(timezone.utc)
    }

    # -----------------------------------------------------
    # 9. Save risk score
    # -----------------------------------------------------

    risk_scores.update_one(

        {"employee_id": employee_id},

        {"$set": result},

        upsert=True
    )

    return result


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    result = calculate_risk_score("EMP001")

    print("Risk Scoring Result:")
    print(result)
