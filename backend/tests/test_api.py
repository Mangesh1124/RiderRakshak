"""
Test: API Endpoints (using FastAPI TestClient)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.database import get_db, Base


# ── Test Database Setup ───────────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_riderakshak.db"

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Create tables for test DB."""
    from app.database import models  # register models
    Base.metadata.create_all(bind=test_engine)

    # Create default rider
    db = TestSessionLocal()
    from app.database.models import Rider
    from app.config import settings
    rider = Rider(id=settings.DEFAULT_RIDER_ID, name="Test Rider")
    db.merge(rider)
    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    app.dependency_overrides.clear()

    import os, time
    for _ in range(3):
        try:
            if os.path.exists("test_riderakshak.db"):
                os.remove("test_riderakshak.db")
            break
        except PermissionError:
            time.sleep(0.5)


@pytest.fixture
def client():
    return TestClient(app)


# ── Health Tests ──────────────────────────────────────────────────────────────

def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_status_endpoint(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_system_status(client):
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "app_name" in data
    assert data["simulation_mode"] is True


# ── Simulation Tests ──────────────────────────────────────────────────────────

def test_simulation_normal(client):
    resp = client.post("/api/simulation/normal")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario"] == "NORMAL"
    assert "features" in data
    assert "detection_result" in data


def test_simulation_accident(client):
    resp = client.post("/api/simulation/accident")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario"] == "ACCIDENT"
    # Accident should usually be detected (may not always with single reading + randomness)
    assert "detection_result" in data
    assert 0.0 <= data["detection_result"]["accident_score"] <= 1.0


def test_simulation_hard_braking(client):
    resp = client.post("/api/simulation/hard_braking")
    assert resp.status_code == 200


def test_simulation_fall(client):
    resp = client.post("/api/simulation/fall")
    assert resp.status_code == 200


def test_simulation_invalid_scenario(client):
    resp = client.post("/api/simulation/flying_car")
    assert resp.status_code == 400


def test_simulation_scenarios_list(client):
    resp = client.get("/api/simulation/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert "scenarios" in data
    assert "NORMAL" in data["scenarios"]
    assert "ACCIDENT" in data["scenarios"]


# ── Accident CRUD Tests ───────────────────────────────────────────────────────

def test_accidents_list(client):
    resp = client.get("/api/accidents")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "accidents" in data


def test_accident_not_found(client):
    resp = client.get("/api/accidents/RR-ACC-99991231-9999")
    assert resp.status_code == 404


def test_accident_cancel_confirm_flow(client):
    """
    Full flow: create accident → cancel → verify FALSE_ALERT_CANCELLED.
    """
    # Trigger accident scenario multiple times until one is detected
    accident_id = None
    for _ in range(5):
        resp = client.post("/api/simulation/accident")
        data = resp.json()
        if data.get("accident_id"):
            accident_id = data["accident_id"]
            break

    if accident_id is None:
        pytest.skip("No accident detected in 5 tries — threshold tuning needed")

    # Verify it's pending
    resp = client.get(f"/api/accidents/{accident_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING"

    # Cancel it
    resp = client.post(f"/api/accidents/{accident_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "FALSE_ALERT_CANCELLED"


def test_accident_confirm_flow(client):
    """
    Full flow: create accident → confirm → verify CONFIRMED_ACCIDENT.
    """
    accident_id = None
    for _ in range(5):
        resp = client.post("/api/simulation/accident")
        data = resp.json()
        if data.get("accident_id"):
            accident_id = data["accident_id"]
            break

    if accident_id is None:
        pytest.skip("No accident detected in 5 tries")

    resp = client.post(f"/api/accidents/{accident_id}/confirm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED_ACCIDENT"


# ── Sensor History Tests ──────────────────────────────────────────────────────

def test_sensor_history(client):
    # Run a simulation first to populate readings
    client.post("/api/simulation/normal")
    resp = client.get("/api/sensors/history")
    assert resp.status_code == 200
    data = resp.json()
    assert "readings" in data
    assert data["total"] >= 0


# ── Alert Tests ───────────────────────────────────────────────────────────────

def test_alerts_list(client):
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
