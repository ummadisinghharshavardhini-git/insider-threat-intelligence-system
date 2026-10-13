from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from io import BytesIO
from datetime import datetime

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from app.database import get_db
from app.models import User, Employee, Incident, Alert


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


# ============================================================
# ROLE CHECK
# ============================================================

def check_report_access(role: str):

    if role not in ["admin", "security_manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or security_manager can access reports"
        )


# ============================================================
# GENERATE REPORT DATA
# ============================================================

def generate_report_data(db: Session):

    users = db.query(User).all()
    employees = db.query(Employee).all()
    incidents = db.query(Incident).all()
    alerts = db.query(Alert).all()

    open_incidents = [
        incident
        for incident in incidents
        if incident.status == "open"
    ]

    open_alerts = [
        alert
        for alert in alerts
        if alert.status == "open"
    ]

    role_breakdown = {}

    for user in users:

        role = user.role or "unknown"

        role_breakdown[role] = (
            role_breakdown.get(role, 0) + 1
        )

    return {
        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "summary": {
            "total_users": len(users),
            "total_employees": len(employees),
            "total_incidents": len(incidents),
            "open_incidents": len(open_incidents),
            "total_alerts": len(alerts),
            "open_alerts": len(open_alerts)
        },

        "users_by_role": role_breakdown,

        "employees": employees,

        "incidents": incidents,

        "alerts": alerts
    }


# ============================================================
# REPORT SUMMARY API
# ============================================================

@router.get("/summary")
def report_summary(
    role: str,
    db: Session = Depends(get_db)
):

    check_report_access(role)

    data = generate_report_data(db)

    return {
        "generated_at": data["generated_at"],
        "summary": data["summary"],
        "users_by_role": data["users_by_role"]
    }


# ============================================================
# EXCEL EXPORT
# ============================================================

@router.get("/export/excel")
def export_excel(
    role: str,
    db: Session = Depends(get_db)
):

    check_report_access(role)

    data = generate_report_data(db)

    workbook = Workbook()

    # --------------------------------------------------------
    # SUMMARY SHEET
    # --------------------------------------------------------

    summary_sheet = workbook.active
    summary_sheet.title = "Summary"

    summary_sheet.append([
        "ITBIS Security Report"
    ])

    summary_sheet.append([
        "Generated At",
        data["generated_at"]
    ])

    summary_sheet.append([])

    summary_sheet.append([
        "Metric",
        "Value"
    ])

    for key, value in data["summary"].items():

        summary_sheet.append([
            key.replace("_", " ").title(),
            value
        ])

    summary_sheet.append([])

    summary_sheet.append([
        "Users by Role"
    ])

    summary_sheet.append([
        "Role",
        "Count"
    ])

    for role_name, count in data["users_by_role"].items():

        summary_sheet.append([
            role_name,
            count
        ])

    # --------------------------------------------------------
    # EMPLOYEES SHEET
    # --------------------------------------------------------

    employee_sheet = workbook.create_sheet(
        "Employees"
    )

    employee_sheet.append([
        "Employee ID",
        "Name",
        "Department",
        "Designation",
        "Manager ID"
    ])

    for employee in data["employees"]:

        employee_sheet.append([
            employee.employee_id,
            employee.name,
            employee.department,
            employee.designation,
            employee.manager_id or ""
        ])

    # --------------------------------------------------------
    # INCIDENTS SHEET
    # --------------------------------------------------------

    incident_sheet = workbook.create_sheet(
        "Incidents"
    )

    incident_sheet.append([
        "ID",
        "Employee ID",
        "Status",
        "Severity",
        "Summary",
        "Created At"
    ])

    for incident in data["incidents"]:

        incident_sheet.append([
            incident.id,
            incident.employee_id,
            incident.status,
            incident.severity,
            incident.summary,
            str(incident.created_at)
            if incident.created_at
            else ""
        ])

    # --------------------------------------------------------
    # ALERTS SHEET
    # --------------------------------------------------------

    alert_sheet = workbook.create_sheet(
        "Alerts"
    )

    alert_sheet.append([
        "ID",
        "Employee ID",
        "Severity",
        "Message",
        "Status",
        "Assigned To",
        "Created At"
    ])

    for alert in data["alerts"]:

        alert_sheet.append([
            alert.id,
            alert.employee_id,
            alert.severity,
            alert.message,
            alert.status,
            alert.assigned_to or "",
            str(alert.created_at)
            if alert.created_at
            else ""
        ])

    # --------------------------------------------------------
    # SAVE EXCEL TO MEMORY
    # --------------------------------------------------------

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    filename = (
        "ITBIS_Security_Report.xlsx"
    )

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        }
    )


# ============================================================
# PDF EXPORT
# ============================================================

@router.get("/export/pdf")
def export_pdf(
    role: str,
    db: Session = Depends(get_db)
):

    check_report_access(role)

    data = generate_report_data(db)

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    elements = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "ITBIS Security Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    elements.append(
        Paragraph(
            f"Generated At: {data['generated_at']}",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Security Summary",
            styles["Heading2"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    summary_table_data = [
        ["Metric", "Value"]
    ]

    for key, value in data["summary"].items():

        summary_table_data.append([
            key.replace("_", " ").title(),
            str(value)
        ])

    summary_table = Table(
        summary_table_data,
        colWidths=[300, 100]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.grey
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER"
            )
        ])
    )

    elements.append(summary_table)

    elements.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # USERS BY ROLE
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Users by Role",
            styles["Heading2"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    role_table_data = [
        ["Role", "Count"]
    ]

    for role_name, count in data["users_by_role"].items():

        role_table_data.append([
            role_name,
            str(count)
        ])

    role_table = Table(
        role_table_data,
        colWidths=[300, 100]
    )

    role_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.grey
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER"
            )
        ])
    )

    elements.append(role_table)

    elements.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # EMPLOYEES
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Employees",
            styles["Heading2"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    employee_table_data = [
        [
            "Employee ID",
            "Name",
            "Department",
            "Designation"
        ]
    ]

    for employee in data["employees"]:

        employee_table_data.append([
            employee.employee_id,
            employee.name,
            employee.department,
            employee.designation
        ])

    if len(employee_table_data) == 1:

        employee_table_data.append([
            "No employees",
            "",
            "",
            ""
        ])

    employee_table = Table(
        employee_table_data,
        colWidths=[90, 130, 100, 130]
    )

    employee_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.grey
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            )
        ])
    )

    elements.append(employee_table)

    # --------------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------------

    document.build(elements)

    output.seek(0)

    filename = (
        "ITBIS_Security_Report.pdf"
    )

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        }
    )
# ============================================================
# MILESTONE 4 - RISK SCORES EXCEL EXPORT
# ============================================================

@router.get("/export/risk-scores")
def export_risk_scores(
    role: str = "employee",
    department: str = None,
    db: Session = Depends(get_db)
):
    check_report_access(role)

    from app.risk_scoring import calculate_risk_score

    employees = db.query(Employee).all()

    if department:
        employees = [
            employee for employee in employees
            if employee.department and
            employee.department.lower() == department.lower()
        ]

    employees_with_scores = []

    for employee in employees:
        try:
            risk_data = calculate_risk_score(employee.employee_id)
            employees_with_scores.append((
                employee,
                risk_data
            ))
        except Exception as exc:
            print(
                f"Risk calculation failed for "
                f"{employee.employee_id}: {exc}"
            )

    employees_with_scores.sort(
        key=lambda item: item[1].get("risk_score", 0),
        reverse=True
    )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Risk Scores"

    sheet.append([
        "Employee ID",
        "Name",
        "Department",
        "Risk Score",
        "Risk Level"
    ])

    for employee, risk_data in employees_with_scores:
        sheet.append([
            employee.employee_id,
            employee.name,
            employee.department,
            risk_data.get("risk_score", 0),
            risk_data.get("risk_category", "unknown")
        ])

    for column in sheet.columns:
        max_length = max(
            len(str(cell.value or "")) for cell in column
        )
        sheet.column_dimensions[
            column[0].column_letter
        ].width = min(max_length + 3, 35)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                'attachment; filename="ITBIS_Risk_Scores.xlsx"'
        }
    )

# ============================================================
# MILESTONE 4 - INCIDENTS EXCEL EXPORT
# ============================================================

@router.get("/export/incidents")
def export_incidents(
    role: str = "employee",
    status: str = None,
    db: Session = Depends(get_db)
):
    check_report_access(role)

    incidents = db.query(Incident).all()

    if status:
        incidents = [
            incident for incident in incidents
            if (incident.status or "").lower() == status.lower()
        ]

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Incidents"

    sheet.append([
        "Incident ID",
        "Employee ID",
        "Status",
        "Severity",
        "Summary",
        "Created At",
        "Resolved At"
    ])

    for incident in incidents:
        sheet.append([
            incident.id,
            incident.employee_id,
            incident.status,
            incident.severity,
            incident.summary,
            str(incident.created_at or ""),
            "Not available"
        ])

    for column in sheet.columns:
        max_length = max(
            len(str(cell.value or "")) for cell in column
        )
        sheet.column_dimensions[
            column[0].column_letter
        ].width = min(max_length + 3, 45)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                'attachment; filename="ITBIS_Incidents.xlsx"'
        }
    )

# ============================================================
# MILESTONE 4 - EMPLOYEE RISK ASSESSMENT PDF
# ============================================================

@router.get("/export/risk-assessment/{employee_id}")
def export_risk_assessment_pdf(
    employee_id: str,
    role: str = "employee",
    db: Session = Depends(get_db)
):
    check_report_access(role)

    from app.risk_scoring import (
        calculate_risk_score,
        anomaly_logs,
        numeric_anomalies,
        set_membership_anomalies,
        ml_anomaly_logs
    )

    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    risk_data = calculate_risk_score(employee_id)

    # Collect recent anomalies from the existing MongoDB collections.
    anomaly_documents = []

    collections_and_filters = [
        (anomaly_logs, {"employee_id": employee_id, "anomaly": True}),
        (numeric_anomalies, {"employee_id": employee_id, "anomaly": True}),
        (set_membership_anomalies, {"employee_id": employee_id, "anomaly": True}),
        (ml_anomaly_logs, {"employee_id": employee_id, "ml_prediction": -1})
    ]

    for collection, query in collections_and_filters:
        for document in collection.find(query).limit(50):
            document.pop("_id", None)
            document.pop("employee_id", None)
            document.pop("password", None)
            document.pop("password_hash", None)

            # Keep only scalar values to make the PDF readable.
            clean_document = {}
            for key, value in document.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    clean_document[key] = str(value) if value is not None else ""
                else:
                    clean_document[key] = str(value)

            clean_document["source"] = collection.name
            anomaly_documents.append(clean_document)

    recent_anomalies = anomaly_documents[-10:]

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        title=f"ITBIS Risk Assessment - {employee_id}"
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        "ITBIS Employee Risk Assessment",
        styles["Title"]
    ))
    elements.append(Spacer(1, 12))

    employee_data = [
        ["Employee ID", employee.employee_id],
        ["Employee Name", employee.name],
        ["Department", employee.department],
        ["Designation", employee.designation],
        ["Risk Score", str(risk_data.get("risk_score", 0))],
        ["Risk Category", str(risk_data.get("risk_category", "unknown")).upper()],
        ["Total Anomalies", str(risk_data.get("anomaly_count", 0))],
        ["Report Generated", str(risk_data.get("calculated_at", ""))]
    ]

    employee_table = Table(
        [["Field", "Details"]] + employee_data,
        colWidths=[150, 330]
    )
    employee_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))
    elements.append(employee_table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph(
        "Risk Factor Scores",
        styles["Heading2"]
    ))

    factor_rows = [["Risk Factor", "Score"]]
    for factor, score in risk_data.get("factor_scores", {}).items():
        factor_label = factor.replace("_", " ").title()
        factor_rows.append([factor_label, str(score)])

    factor_table = Table(factor_rows, colWidths=[330, 150])
    factor_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))
    elements.append(factor_table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph(
        "Anomaly Counts",
        styles["Heading2"]
    ))

    count_rows = [
        ["Anomaly Source", "Count"],
        ["Behavioral anomalies", str(risk_data.get("old_anomalies", 0))],
        ["Numeric anomalies", str(risk_data.get("numeric_anomalies", 0))],
        ["Set-membership anomalies", str(risk_data.get("set_membership_anomalies", 0))],
        ["Machine-learning anomalies", str(risk_data.get("ml_anomalies", 0))]
    ]

    count_table = Table(count_rows, colWidths=[330, 150])
    count_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))
    elements.append(count_table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph(
        "Recent Anomalies (up to 10)",
        styles["Heading2"]
    ))

    if recent_anomalies:
        anomaly_rows = [["Source", "Anomaly Details"]]

        for anomaly in recent_anomalies:
            details = "; ".join(
                f"{key}: {value}"
                for key, value in anomaly.items()
            )
            anomaly_rows.append([
                anomaly.get("source", "unknown"),
                Paragraph(details[:1200], styles["BodyText"])
            ])

        anomaly_table = Table(
            anomaly_rows,
            colWidths=[130, 350],
            repeatRows=1
        )
        anomaly_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP")
        ]))
        elements.append(anomaly_table)
    else:
        elements.append(Paragraph(
            "No anomaly records found.",
            styles["BodyText"]
        ))

    document.build(elements)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="ITBIS_Risk_Assessment_{employee_id}.pdf"'
        }
    )

# ============================================================
# MILESTONE 4 - COMPLIANCE REPORT PDF
# ============================================================

@router.get("/export/compliance-pdf")
def export_compliance_pdf(
    role: str = "employee",
    db: Session = Depends(get_db)
):
    check_report_access(role)

    from app.risk_scoring import calculate_risk_score

    employees = db.query(Employee).all()
    incidents = db.query(Incident).all()
    alerts = db.query(Alert).all()

    risk_distribution = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0
    }
    risk_scores = []

    for employee in employees:
        try:
            result = calculate_risk_score(employee.employee_id)
            score = float(result.get("risk_score", 0))
            category = str(
                result.get("risk_category", "low")
            ).lower()

            risk_scores.append(score)

            if category in risk_distribution:
                risk_distribution[category] += 1
        except Exception as exc:
            print(
                f"Could not calculate risk for "
                f"{employee.employee_id}: {exc}"
            )

    total_employees = len(employees)
    average_risk_score = (
        round(sum(risk_scores) / len(risk_scores), 1)
        if risk_scores else 0.0
    )

    total_incidents = len(incidents)
    resolved_incidents = sum(
        1 for item in incidents
        if (item.status or "").lower() == "resolved"
    )
    incident_resolution_rate = (
        round(resolved_incidents / total_incidents * 100, 1)
        if total_incidents else 100.0
    )

    total_alerts = len(alerts)
    resolved_alerts = sum(
        1 for item in alerts
        if (item.status or "").lower() == "resolved"
    )
    alert_resolution_rate = (
        round(resolved_alerts / total_alerts * 100, 1)
        if total_alerts else 100.0
    )

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        title="ITBIS Compliance Report"
    )

    styles = getSampleStyleSheet()
    elements = [
        Paragraph("ITBIS Compliance Report", styles["Title"]),
        Spacer(1, 8),
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"]
        ),
        Spacer(1, 16),
        Paragraph("Organizational Risk Overview", styles["Heading2"])
    ]

    risk_rows = [["Metric", "Value"]] + [
        ["Total Employees", str(total_employees)],
        ["Average Risk Score", str(average_risk_score)],
        ["Low Risk Employees", str(risk_distribution["low"])],
        ["Medium Risk Employees", str(risk_distribution["medium"])],
        ["High Risk Employees", str(risk_distribution["high"])],
        ["Critical Risk Employees", str(risk_distribution["critical"])]
    ]

    risk_table = Table(risk_rows, colWidths=[300, 150])
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))
    elements.append(risk_table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph("Incident Response", styles["Heading2"]))

    incident_rows = [
        ["Metric", "Value"],
        ["Total Incidents", str(total_incidents)],
        ["Resolved Incidents", str(resolved_incidents)],
        ["Incident Resolution Rate", f"{incident_resolution_rate}%"]
    ]
    incident_table = Table(incident_rows, colWidths=[300, 150])
    incident_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))
    elements.append(incident_table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph("Alert Response", styles["Heading2"]))

    alert_rows = [
        ["Metric", "Value"],
        ["Total Alerts", str(total_alerts)],
        ["Resolved Alerts", str(resolved_alerts)],
        ["Alert Resolution Rate", f"{alert_resolution_rate}%"]
    ]
    alert_table = Table(alert_rows, colWidths=[300, 150])
    alert_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))
    elements.append(alert_table)

    document.build(elements)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                'attachment; filename="ITBIS_Compliance_Report.pdf"'
        }
    )

# ============================================================
# MILESTONE 4 - REPORTS CATALOG
# ============================================================

@router.get("/catalog")
def reports_catalog(role: str = "employee"):
    allowed_roles = [
        "admin",
        "security_analyst",
        "security_manager"
    ]

    if role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access the reports catalog"
        )

    return {
        "message": "Available ITBIS reports",
        "reports": [
            {
                "name": "Report Summary",
                "method": "GET",
                "endpoint": "/reports/summary",
                "formats": ["JSON"]
            },
            {
                "name": "General Security Report",
                "method": "GET",
                "endpoint": "/reports/export/excel",
                "formats": ["Excel"]
            },
            {
                "name": "General Security PDF",
                "method": "GET",
                "endpoint": "/reports/export/pdf",
                "formats": ["PDF"]
            },
            {
                "name": "Risk Scores",
                "method": "GET",
                "endpoint": "/reports/export/risk-scores",
                "formats": ["Excel"]
            },
            {
                "name": "Incidents",
                "method": "GET",
                "endpoint": "/reports/export/incidents",
                "formats": ["Excel"]
            },
            {
                "name": "Employee Risk Assessment",
                "method": "GET",
                "endpoint": "/reports/export/risk-assessment/{employee_id}",
                "formats": ["PDF"]
            },
            {
                "name": "Compliance Report",
                "method": "GET",
                "endpoint": "/reports/export/compliance-pdf",
                "formats": ["PDF"]
            }
        ]
    }
