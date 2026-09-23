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


def test_review_detail_includes_issues():
    from app.db import get_db
    from app.models import ReviewTask, ReviewIssue
    from app.main import app
    db = next(get_db())
    project = db.query(__import__("app.models", fromlist=["Project"]).Project).first()
    task = ReviewTask(project_id=project.id, status="completed", progress=100)
    db.add(task); db.commit(); db.refresh(task)
    db.add(ReviewIssue(review_id=task.id, rule_id="T-001", category="测试", severity="low", title="测试问题", description="测试"))
    db.commit()
    response = client.get(f"/api/reviews/{task.id}")
    assert response.status_code == 200
    assert len(response.json()["issues"]) == 1
