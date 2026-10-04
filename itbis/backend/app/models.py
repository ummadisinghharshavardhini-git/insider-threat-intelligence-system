from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="employee")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    manager_id = Column(String, nullable=True)


# ============================================================
# INCIDENT MODEL
# ============================================================

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        String,
        nullable=False,
        index=True
    )

    status = Column(
        String,
        default="open",
        nullable=False
    )

    severity = Column(
        String,
        nullable=False
    )

    summary = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


# ============================================================
# EVIDENCE MODEL
# ============================================================

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)

    incident_id = Column(
        Integer,
        ForeignKey("incidents.id"),
        nullable=False,
        index=True
    )

    note = Column(
        Text,
        nullable=False
    )

    added_by = Column(
        String,
        nullable=False
    )

    added_at = Column(
        DateTime,
        server_default=func.now()
    )

# ============================================================
# ALERT MODEL
# ============================================================


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        String,
        nullable=False,
        index=True
    )

    severity = Column(
        String,
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    status = Column(
        String,
        default="open",
        nullable=False
    )

    assigned_to = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )
