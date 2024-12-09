from fastapi.testclient import TestClient
from ..main import app
from ..database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_vehicle_detection():
    response = client.post(
        "/api/vehicle/",
        json={
            "camera_id": "test_camera",
            "timestamp": datetime.now().isoformat(),
            "vehicle_type": "car",
            "confidence": 0.95,
            "bbox": "[100, 100, 200, 200]"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_type"] == "car"
    assert "id" in data

def test_read_vehicle_detections():
    response = client.get("/api/vehicle/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)