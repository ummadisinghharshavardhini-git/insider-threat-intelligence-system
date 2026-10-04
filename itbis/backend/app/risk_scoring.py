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
# MILESTONE 3 - RISK WEIGHTS
# =========================================================

WEIGHTS = {
    "behavioral_anomalies": 0.35,
    "privilege_misuse": 0.25,
    "data_access_violations": 0.20,
    "access_pattern_deviations": 0.10,
    "historical_security_events": 0.10
}


# =========================================================
# RISK SCORE CALCULATION
# =========================================================

def calculate_risk_score(employee_id):

    # -----------------------------------------------------
    # 1. Existing behavioral anomalies
    # -----------------------------------------------------

    old_anomalies = list(
        anomaly_logs.find({
            "employee_id": employee_id,
            "anomaly": True
        })
    )

    # -----------------------------------------------------
    # 2. Numeric anomalies
    # -----------------------------------------------------

    numeric_anomaly_list = list(
        numeric_anomalies.find({
            "employee_id": employee_id,
            "anomaly": True
        })
    )

    # -----------------------------------------------------
    # 3. Set-membership anomalies
    # -----------------------------------------------------

    set_anomaly_list = list(
        set_membership_anomalies.find({
            "employee_id": employee_id,
            "anomaly": True
        })
    )

    # -----------------------------------------------------
    # 4. ML anomalies
    # -----------------------------------------------------

    ml_anomaly_list = list(
        ml_anomaly_logs.find({
            "employee_id": employee_id,
            "ml_prediction": -1
        })
    )

    # -----------------------------------------------------
    # 5. Counts
    # -----------------------------------------------------

    old_count = len(old_anomalies)
    numeric_count = len(numeric_anomaly_list)
    set_count = len(set_anomaly_list)
    ml_count = len(ml_anomaly_list)

    total_anomaly_count = (
        old_count
        + numeric_count
        + set_count
        + ml_count
    )

    # =====================================================
    # 6. FIVE RISK FACTORS
    # =====================================================

    # Behavioral anomalies
    behavioral_score = min(
        old_count * 10 + ml_count * 15,
        100
    )

    # Privilege misuse
    privilege_score = min(
        sum(
            1 for anomaly in old_anomalies
            if "privilege" in str(
                anomaly.get("anomaly_type", "")
            ).lower()
        ) * 40,
        100
    )

    # Data access violations
    data_access_score = min(
        sum(
            1 for anomaly in old_anomalies
            if "exfiltration" in str(
                anomaly.get("anomaly_type", "")
            ).lower()
        ) * 50,
        100
    )

    # Access pattern deviations
    access_pattern_score = min(
        sum(
            1 for anomaly in old_anomalies
            if "unusual" in str(
                anomaly.get("anomaly_type", "")
            ).lower()
        ) * 15,
        100
    )

    # Historical security events
    historical_score = min(
        total_anomaly_count * 2,
        100
    )

    # =====================================================
    # 7. STORE FACTOR SCORES
    # =====================================================

    factor_scores = {
        "behavioral_anomalies": behavioral_score,
        "privilege_misuse": privilege_score,
        "data_access_violations": data_access_score,
        "access_pattern_deviations": access_pattern_score,
        "historical_security_events": historical_score
    }

    # =====================================================
    # 8. WEIGHTED RISK SCORE
    # =====================================================

    weighted_total = sum(
        factor_scores[factor] * WEIGHTS[factor]
        for factor in WEIGHTS
    )

    risk_score = round(weighted_total, 1)

    # =====================================================
    # 9. RISK CATEGORY
    # =====================================================

    if risk_score >= 75:
        risk_category = "critical"

    elif risk_score >= 50:
        risk_category = "high"

    elif risk_score >= 25:
        risk_category = "medium"

    else:
        risk_category = "low"

    # =====================================================
    # 10. FINAL RESULT
    # =====================================================

    result = {
        "employee_id": employee_id,

        "factor_scores": factor_scores,

        "risk_score": risk_score,

        "risk_category": risk_category,

        "anomaly_count": total_anomaly_count,

        "old_anomalies": old_count,

        "numeric_anomalies": numeric_count,

        "set_membership_anomalies": set_count,

        "ml_anomalies": ml_count,

        "calculated_at": datetime.now(timezone.utc)
    }

    # =====================================================
    # 11. SAVE TO MONGODB
    # =====================================================

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

    print("\n===================================")
    print("MILESTONE 3 RISK SCORING RESULT")
    print("===================================")

    print(result)
