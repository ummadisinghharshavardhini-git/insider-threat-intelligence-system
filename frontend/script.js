// ============================================
// ITBIS SECURITY DASHBOARD
// ============================================

// ============================================
// LOGIN PROTECTION
// ============================================

const isLoggedIn = localStorage.getItem("itbisLoggedIn");

if (isLoggedIn !== "true") {
    window.location.href = "login.html";
}


// ============================================
// API CONFIGURATION
// ============================================

const API_URL = "http://127.0.0.1:8000";


// ============================================
// BACKEND HEALTH CHECK
// ============================================

async function checkBackend() {
    try {
        const response = await fetch(API_URL + "/health");

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        console.log("ITBIS Backend Connected");

    } catch (error) {
        console.error("Backend connection error:", error);
    }
}


// ============================================
// RISK LEVEL
// ============================================

function getRiskLevel(score) {
    score = Number(score || 0);

    if (score >= 75) {
        return "high";
    }

    if (score >= 50) {
        return "medium";
    }

    return "low";
}


// ============================================
// LOAD EMPLOYEES
// ============================================

async function loadEmployees() {
    try {
        const response = await fetch(API_URL + "/employees/");

        if (!response.ok) {
            throw new Error("Failed to load employees");
        }

        const employees = await response.json();

        console.log("Employees:", employees);

        const employeeCount =
            document.getElementById("employeeCount");

        if (employeeCount) {
            employeeCount.textContent = employees.length;
        }

        await loadAllEmployeeRisk(employees);
        await loadEmployeesTable(employees);

    } catch (error) {
        console.error("Employee loading error:", error);
    }
}


// ============================================
// EMPLOYEES TABLE
// ============================================

async function loadEmployeesTable(employees) {

    const table =
        document.getElementById("employeesTable");

    if (!table) {
        return;
    }

    table.innerHTML = "";

    if (!employees || employees.length === 0) {

        table.innerHTML =
            "<tr>" +
            "<td colspan='5'>No employees found</td>" +
            "</tr>";

        return;
    }

    employees.forEach(function (employee) {

        const row =
            document.createElement("tr");

        row.innerHTML =
            "<td>" +
            (employee.employee_id || "-") +
            "</td>" +

            "<td>" +
            (employee.name || "-") +
            "</td>" +

            "<td>" +
            (employee.department || "-") +
            "</td>" +

            "<td>" +
            (employee.designation || "-") +
            "</td>" +

            "<td>" +
            (employee.manager_id || "-") +
            "</td>";

        table.appendChild(row);
    });

    console.log("Employee table loaded");
}


// ============================================
// LOAD EMPLOYEE RISK
// ============================================

async function loadEmployeeRisk(employeeId) {

    try {

        const response =
            await fetch(
                API_URL + "/risk/" + employeeId
            );

        if (!response.ok) {
            throw new Error("Failed to load risk");
        }

        const data =
            await response.json();

        console.log(
            "Risk data for " + employeeId + ":",
            data
        );

        return data;

    } catch (error) {

        console.error(
            "Risk loading error for " +
            employeeId +
            ":",
            error
        );

        return {
            employee_id: employeeId,
            risk_score: 0,
            risk_level: "low",
            anomaly_count: 0
        };
    }
}


// ============================================
// LOAD ALL EMPLOYEE RISK
// ============================================

async function loadAllEmployeeRisk(employees) {

    let highRisk = 0;
    let mediumRisk = 0;
    let lowRisk = 0;

    for (const employee of employees) {

        const risk =
            await loadEmployeeRisk(
                employee.employee_id
            );

        const score =
            Number(risk.risk_score || 0);

        const level =
            getRiskLevel(score);

        if (level === "high") {
            highRisk++;
        }
        else if (level === "medium") {
            mediumRisk++;
        }
        else {
            lowRisk++;
        }
    }


    // High Risk Count

    const highRiskCount =
        document.getElementById(
            "highRiskCount"
        );

    if (highRiskCount) {
        highRiskCount.textContent =
            highRisk;
    }


    // Risk Overview

    const highRiskElement =
        document.getElementById("highRisk");

    const mediumRiskElement =
        document.getElementById("mediumRisk");

    const lowRiskElement =
        document.getElementById("lowRisk");

    if (highRiskElement) {
        highRiskElement.textContent =
            highRisk;
    }

    if (mediumRiskElement) {
        mediumRiskElement.textContent =
            mediumRisk;
    }

    if (lowRiskElement) {
        lowRiskElement.textContent =
            lowRisk;
    }


    // Progress Bars

    const total =
        highRisk +
        mediumRisk +
        lowRisk;

    const highProgress =
        document.getElementById(
            "highProgress"
        );

    const mediumProgress =
        document.getElementById(
            "mediumProgress"
        );

    const lowProgress =
        document.getElementById(
            "lowProgress"
        );

    if (total > 0) {

        if (highProgress) {
            highProgress.style.width =
                (highRisk / total * 100) + "%";
        }

        if (mediumProgress) {
            mediumProgress.style.width =
                (mediumRisk / total * 100) + "%";
        }

        if (lowProgress) {
            lowProgress.style.width =
                (lowRisk / total * 100) + "%";
        }

    } else {

        if (highProgress) {
            highProgress.style.width = "0%";
        }

        if (mediumProgress) {
            mediumProgress.style.width = "0%";
        }

        if (lowProgress) {
            lowProgress.style.width = "0%";
        }
    }


    await loadEmployeeRiskMonitoring(
        employees
    );
}


// ============================================
// EMPLOYEE RISK MONITORING
// ============================================

async function loadEmployeeRiskMonitoring(
    employees
) {

    const container =
        document.querySelector(
            ".employee-list"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    for (const employee of employees) {

        const risk =
            await loadEmployeeRisk(
                employee.employee_id
            );

        const score =
            Number(risk.risk_score || 0);

        const level =
            getRiskLevel(score);

        const row =
            document.createElement("div");

        row.className = "employee-row";


        let initials = "EM";

        if (employee.name) {

            const parts =
                employee.name.split(" ");

            initials =
                parts
                    .map(function (part) {
                        return part.charAt(0);
                    })
                    .join("")
                    .substring(0, 2)
                    .toUpperCase();
        }


        row.innerHTML =
            "<div class='employee-info'>" +

            "<div class='employee-avatar'>" +
            initials +
            "</div>" +

            "<div>" +
            "<strong>" +
            (employee.name || "Unknown Employee") +
            "</strong>" +

            "<small>" +
            employee.employee_id +
            "</small>" +
            "</div>" +

            "</div>" +

            "<div class='risk-score'>" +

            "<strong>" +
            score +
            "</strong>" +

            "<span>Risk Score</span>" +

            "</div>" +

            "<div class='employee-risk-badge'>" +

            "<span class='badge " +
            level +
            "'>" +

            level.toUpperCase() +

            "</span>" +

            "</div>";

        container.appendChild(row);
    }
}


// ============================================
// LOAD ACTIVITY LOGS
// ============================================

async function loadActivities() {

    const table =
        document.getElementById(
            "activityTable"
        );

    try {

        const response =
            await fetch(
                API_URL + "/activity/"
            );

        if (!response.ok) {
            throw new Error(
                "Failed to load activities"
            );
        }

        const activities =
            await response.json();

        console.log(
            "Activities:",
            activities
        );


        // Activity Count

        const activityCount =
            document.getElementById(
                "activityCount"
            );

        if (activityCount) {
            activityCount.textContent =
                activities.length;
        }


        if (!table) {
            return;
        }

        table.innerHTML = "";


        if (activities.length === 0) {

            table.innerHTML =
                "<tr>" +
                "<td colspan='6'>" +
                "No activity records found" +
                "</td>" +
                "</tr>";

            return;
        }


        activities.forEach(
            function (activity) {

                const row =
                    document.createElement("tr");

                const score =
                    Number(
                        activity.risk_score || 0
                    );

                const level =
                    getRiskLevel(score);

                row.innerHTML =

                    "<td>" +
                    (activity.employee_id || "-") +
                    "</td>" +

                    "<td>" +
                    (activity.activity || "-") +
                    "</td>" +

                    "<td>" +
                    (activity.device || "-") +
                    "</td>" +

                    "<td>" +
                    (activity.application || "-") +
                    "</td>" +

                    "<td>" +
                    (activity.data_volume ?? 0) +
                    "</td>" +

                    "<td>" +

                    "<span class='badge " +
                    level +
                    "'>" +

                    level.toUpperCase() +

                    "</span>" +

                    "</td>";

                table.appendChild(row);
            }
        );

    } catch (error) {

        console.error(
            "Activity loading error:",
            error
        );

        if (table) {

            table.innerHTML =
                "<tr>" +
                "<td colspan='6'>" +
                "Unable to load activity data" +
                "</td>" +
                "</tr>";
        }
    }
}


// ============================================
// LOAD ANOMALIES
// ============================================

async function loadAnomalies() {

    const table =
        document.getElementById(
            "anomalyTable"
        );

    if (!table) {
        return;
    }

    try {

        const response =
            await fetch(
                API_URL + "/anomalies/"
            );

        if (!response.ok) {
            throw new Error(
                "Failed to load anomalies"
            );
        }

        const anomalies =
            await response.json();

        console.log(
            "Anomalies:",
            anomalies
        );

        table.innerHTML = "";


        // Count only TRUE anomalies

        const realAnomalies =
            anomalies.filter(
                function (anomaly) {
                    return anomaly.anomaly === true;
                }
            );

        const anomalyCount =
            document.getElementById(
                "anomalyCount"
            );

        if (anomalyCount) {
            anomalyCount.textContent =
                realAnomalies.length;
        }


        if (anomalies.length === 0) {

            table.innerHTML =
                "<tr>" +
                "<td colspan='6'>" +
                "No anomaly records found" +
                "</td>" +
                "</tr>";

            return;
        }


        anomalies.forEach(
            function (anomaly) {

                const row =
                    document.createElement("tr");

                const isAnomaly =
                    anomaly.anomaly === true;

                const status =
                    isAnomaly
                        ? "ANOMALY"
                        : "NORMAL";

                const statusClass =
                    isAnomaly
                        ? "detected"
                        : "normal";


                let baseline = "-";

                if (
                    anomaly.baseline_average !== null &&
                    anomaly.baseline_average !== undefined
                ) {
                    baseline =
                        Number(
                            anomaly.baseline_average
                        ).toFixed(2);
                }


                let threshold = "-";

                if (
                    anomaly.threshold !== null &&
                    anomaly.threshold !== undefined
                ) {
                    threshold =
                        Number(
                            anomaly.threshold
                        ).toFixed(2);
                }


                row.innerHTML =

                    "<td>" +
                    (anomaly.employee_id || "-") +
                    "</td>" +

                    "<td>" +
                    (anomaly.activity || "-") +
                    "</td>" +

                    "<td>" +
                    (
                        anomaly.login_time_minutes ??
                        "-"
                    ) +
                    "</td>" +

                    "<td>" +
                    baseline +
                    "</td>" +

                    "<td>" +
                    threshold +
                    "</td>" +

                    "<td>" +

                    "<span class='anomaly-status " +
                    statusClass +
                    "'>" +

                    status +

                    "</span>" +

                    "</td>";

                table.appendChild(row);
            }
        );

    } catch (error) {

        console.error(
            "Anomaly loading error:",
            error
        );

        table.innerHTML =
            "<tr>" +
            "<td colspan='6'>" +
            "Unable to load anomaly data" +
            "</td>" +
            "</tr>";
    }
}


// ============================================
// LOAD COMPLETE DASHBOARD
// ============================================

async function loadDashboard() {

    console.log(
        "Loading ITBIS Dashboard..."
    );

    await checkBackend();

    await loadEmployees();

    await loadActivities();

    await loadAnomalies();

    console.log(
        "ITBIS Dashboard Loaded"
    );
}


// ============================================
// LOGOUT
// ============================================

function logout() {

    localStorage.removeItem(
        "itbisLoggedIn"
    );

    localStorage.removeItem(
        "itbisUser"
    );

    localStorage.removeItem(
        "itbisRole"
    );

    window.location.href =
        "login.html";
}


// ============================================
// START DASHBOARD
// ============================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadDashboard();

    }
);