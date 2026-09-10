from fastapi.testclient import TestClient
from app.main import app

def test_login_user_a():
    with TestClient(app) as client:
        response = client.post("/auth/login", json={
            "email": "usera@test.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

def test_login_user_b():
    with TestClient(app) as client:
        response = client.post("/auth/login", json={
            "email": "userb@test.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

def test_user_a_assignment():
    with TestClient(app) as client:
        res = client.post("/auth/login", json={"email": "usera@test.com", "password": "password123"})
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/me/assignment", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "usera@test.com"
        assert data["route"]["name"] == "Route A"
        assert data["vehicle"]["vehicle_number"] == "BUS-001"

def test_authorization_enforcement_user_a_cannot_access_bus_002():
    with TestClient(app) as client:
        res = client.post("/auth/login", json={"email": "usera@test.com", "password": "password123"})
        token_a = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token_a}"}
        
        # User A requesting BUS-002 (assigned to User B) must fail with 403 Forbidden
        response = client.get("/vehicles/BUS-002/location", headers=headers)
        assert response.status_code == 403
        assert "Access Denied" in response.json()["detail"]

def test_user_a_can_access_own_vehicle_bus_001():
    with TestClient(app) as client:
        res = client.post("/auth/login", json={"email": "usera@test.com", "password": "password123"})
        token_a = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token_a}"}
        
        response = client.get("/vehicles/BUS-001/location", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["vehicle_number"] == "BUS-001"
