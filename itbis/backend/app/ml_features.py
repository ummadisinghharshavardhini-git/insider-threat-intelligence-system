from datetime import datetime
import pandas as pd

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["itbis"]


def build_feature_table() -> pd.DataFrame:

    # Read all behavior logs from MongoDB
    logs = list(db["behavior_logs"].find({}))
    
    if not logs:
        return pd.DataFrame()

    df = pd.DataFrame(logs)

    # Convert MongoDB timestamp into datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Remove invalid timestamps
    df = df.dropna(subset=["timestamp"])

    # Create date column
    df["date"] = df["timestamp"].dt.date

    # Create login hour
    df["login_hour"] = df.apply(
        lambda row:
        row["timestamp"].hour + row["timestamp"].minute / 60
        if row.get("activity") == "login"
        else None,
        axis=1
    )

    # File-related activities
    file_activities = [
        "file_access",
        "file_upload",
        "file_download"
    ]

    df["file_activity"] = df["activity"].apply(
        lambda x: 1 if x in file_activities else 0
    )

    # Make numeric fields safe
    df["data_volume"] = pd.to_numeric(
        df.get("data_volume", 0),
        errors="coerce"
    ).fillna(0)

    # Create daily employee-level feature table
    features = (
        df.groupby(["employee_id", "date"])
        .agg(
            avg_login_hour=("login_hour", "mean"),
            file_activity_count=("file_activity", "sum"),
            total_data_volume=("data_volume", "sum"),
            unique_devices=("device", "nunique"),
            unique_applications=("application", "nunique"),
            total_events=("activity", "count")
        )
        .reset_index()
    )

    # Replace missing numeric values
    numeric_columns = [
        "avg_login_hour",
        "file_activity_count",
        "total_data_volume",
        "unique_devices",
        "unique_applications",
        "total_events"
    ]

    features[numeric_columns] = (
        features[numeric_columns]
        .fillna(0)
    )

    return features

