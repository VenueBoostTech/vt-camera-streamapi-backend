from fastapi.testclient import TestClient
from ..main import app
from ..database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

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

def test_create_camera():
    response = client.post(
        "/api/camera/",
        json={"camera_id": "test_camera", "rtsp_url": "rtsp://example.com/stream1", "status": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == "test_camera"
    assert "id" in data

def test_read_cameras():
    response = client.get("/api/camera/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_camera():
    response = client.get("/api/camera/test_camera")
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == "test_camera"