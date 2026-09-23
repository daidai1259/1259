from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Project, Drawing, DrawingPage, ReviewTask, ReviewIssue
from app.review import run_review
from app.review_rules import RULES

def test_review_worker_creates_metadata_issues():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.db import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    project = Project(name="审图测试")
    db.add(project); db.commit(); db.refresh(project)
    drawing = Drawing(project_id=project.id, original_name="A-101.pdf", stored_name="x.pdf", mime_type="application/pdf", size_bytes=1, sha256="a"*64, status="ready")
    db.add(drawing); db.commit(); db.refresh(drawing)
    page = DrawingPage(drawing_id=drawing.id, page_number=1, image_name="page.png", width=100, height=100, dpi=150, metadata_status="ready")
    db.add(page); db.commit()
    task = ReviewTask(project_id=project.id, status="queued", progress=0)
    db.add(task); db.commit(); db.refresh(task)
    run_review(task.id, db)
    db.refresh(task)
    assert task.status == "completed"
    assert task.progress == 100
    assert task.attempts == 1
    assert db.query(ReviewIssue).filter_by(review_id=task.id).count() == 2


def test_review_rules_are_registered():
    ids = {rule.rule_id for rule in RULES}
    assert "META-DWG-001" in ids
    assert "META-SCALE-001" in ids
