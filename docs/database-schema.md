# Database Schema

## PostgreSQL Database

PostgreSQL is used for structured and relational data.

### Users
- id
- email
- password_hash
- role

### Employees
- id
- employee_id
- name
- department
- designation
- manager_id

### Incidents
- id
- employee_id
- status
- severity
- created_at

### Alerts
- id
- employee_id
- severity
- message
- created_at

---

## MongoDB Database

MongoDB is used for flexible and document-based data.

### Activity Logs
- employee_id
- event_type
- timestamp
- details

### Behavioral Baselines
- employee_id
- indicator
- typical_value
- last_updated

---

## Why Two Databases?

PostgreSQL stores structured data such as users, employees, incidents, and alerts.

MongoDB stores flexible activity logs and behavioral analytics because different activity events can contain different fields.
