import os
from pathlib import Path
from fastapi.testclient import TestClient

TEST_DB = Path("/tmp/1259-api-test.db")
TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from app.db import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_project_and_reject_empty():
    response = client.post("/api/projects", json={"name": "  测试项目  "})
    assert response.status_code == 201
    assert response.json()["name"] == "测试项目"
    response = client.post("/api/projects", json={"name": "   "})
    assert response.status_code == 422

def test_review_requires_drawing():
    project = client.post("/api/projects", json={"name": "无图纸项目"}).json()
    response = client.post(f"/api/projects/{project['id']}/reviews")
    assert response.status_code == 400
