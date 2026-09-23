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


def test_drawing_issues_uses_latest_completed_review_even_when_empty():
    from app.db import get_db
    from app.models import Project, Drawing, DrawingPage, ReviewTask, ReviewIssue
    db = next(get_db())
    project = Project(name="最新审核语义测试")
    db.add(project); db.commit(); db.refresh(project)
    drawing = Drawing(project_id=project.id, original_name="test.pdf", stored_name="test.pdf", mime_type="application/pdf", size_bytes=1, sha256="e"*64, status="ready")
    db.add(drawing); db.commit(); db.refresh(drawing)
    page = DrawingPage(drawing_id=drawing.id, page_number=1, image_name="p.png", width=100, height=100, dpi=150, status="ready")
    db.add(page); db.commit(); db.refresh(page)
    old = ReviewTask(project_id=project.id, status="completed", progress=100)
    db.add(old); db.commit(); db.refresh(old)
    db.add(ReviewIssue(review_id=old.id, page_id=page.id, rule_id="OLD", category="测试", severity="low", title="旧问题", description="旧问题"))
    db.commit()
    latest = ReviewTask(project_id=project.id, status="completed", progress=100)
    db.add(latest); db.commit(); db.refresh(latest)
    response = client.get(f"/api/drawings/{drawing.id}/issues")
    assert response.status_code == 200
    assert response.json() == []
