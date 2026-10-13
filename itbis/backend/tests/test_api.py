from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


def test_admin_dashboard_allowed():
    response = client.get("/dashboard/admin?role=admin")
    assert response.status_code == 200


def test_admin_dashboard_blocked_for_employee():
    response = client.get("/dashboard/admin?role=employee")
    assert response.status_code == 403


def test_admin_dashboard_blocked_for_unknown_role():
    response = client.get("/dashboard/admin?role=guest")
    assert response.status_code == 403
