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
    assert db.query(ReviewIssue).filter_by(review_id=task.id).count() == 3
    assert all(i.coordinate_space == "normalized" for i in db.query(ReviewIssue).filter_by(review_id=task.id).all())


def test_review_rules_are_registered():
    ids = {rule.rule_id for rule in RULES}
    assert "META-DWG-001" in ids
    assert "META-SCALE-001" in ids
    assert "META-TITLE-001" in ids
    assert "META-SCALE-002" in ids


def test_review_rule_localizes_text_evidence():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.db import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    project = Project(name="定位测试")
    db.add(project); db.commit(); db.refresh(project)
    drawing = Drawing(project_id=project.id, original_name="A.pdf", stored_name="x.pdf", mime_type="application/pdf", size_bytes=1, sha256="b"*64, status="ready")
    db.add(drawing); db.commit(); db.refresh(drawing)
    page = DrawingPage(drawing_id=drawing.id, page_number=1, image_name="page.png", width=1000, height=500, dpi=150, metadata_status="ready", scale_text="bad")
    db.add(page); db.commit(); db.refresh(page)
    from app.models import DrawingPageText
    db.add(DrawingPageText(page_id=page.id, text="bad", x0=200, y0=100, x1=300, y1=130, coordinate_space="pixels"))
    db.commit()
    task = ReviewTask(project_id=project.id, status="queued", progress=0)
    db.add(task); db.commit(); db.refresh(task)
    run_review(task.id, db)
    issue = db.query(ReviewIssue).filter_by(review_id=task.id, rule_id="META-SCALE-002").first()
    assert issue is not None
    assert issue.coordinate_space == "normalized"
    assert issue.x0 == 0.2
    assert issue.y0 == 0.2
    assert issue.x1 == 0.3
    assert issue.y1 == 0.26


def test_drawing_number_sequence_gap_rule():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.db import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    project = Project(name="图号序列测试")
    db.add(project); db.commit(); db.refresh(project)
    drawing = Drawing(project_id=project.id, original_name="set.pdf", stored_name="set.pdf", mime_type="application/pdf", size_bytes=1, sha256="c"*64, status="ready")
    db.add(drawing); db.commit(); db.refresh(drawing)
    for n, number in enumerate(["A-101", "A-103"], start=1):
        db.add(DrawingPage(drawing_id=drawing.id, page_number=n, image_name=f"p{n}.png", width=1000, height=500, dpi=150, metadata_status="ready", drawing_number=number))
    db.commit()
    task = ReviewTask(project_id=project.id, status="queued", progress=0)
    db.add(task); db.commit(); db.refresh(task)
    run_review(task.id, db)
    issue = db.query(ReviewIssue).filter_by(review_id=task.id, rule_id="META-DWG-003").first()
    assert issue is not None
    assert "A-102" in issue.evidence


def test_discipline_consistency_rule():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.db import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    project = Project(name="专业一致性测试")
    db.add(project); db.commit(); db.refresh(project)
    drawing = Drawing(project_id=project.id, original_name="set.pdf", stored_name="set.pdf", mime_type="application/pdf", size_bytes=1, sha256="d"*64, status="ready")
    db.add(drawing); db.commit(); db.refresh(drawing)
    for n, discipline in enumerate(["建筑", "结构"], start=1):
        db.add(DrawingPage(drawing_id=drawing.id, page_number=n, image_name=f"p{n}.png", width=1000, height=500, dpi=150, metadata_status="ready", drawing_number="A-101", detected_discipline=discipline))
    db.commit()
    task = ReviewTask(project_id=project.id, status="queued", progress=0)
    db.add(task); db.commit(); db.refresh(task)
    run_review(task.id, db)
    issues = db.query(ReviewIssue).filter_by(review_id=task.id, rule_id="META-CONSIST-002").all()
    assert len(issues) == 2


def test_cross_discipline_reference_rule():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.db import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    project = Project(name="专业交叉引用测试")
    db.add(project); db.commit(); db.refresh(project)
    drawing = Drawing(project_id=project.id, original_name="set.pdf", stored_name="set.pdf", mime_type="application/pdf", size_bytes=1, sha256="f"*64, status="ready")
    db.add(drawing); db.commit(); db.refresh(drawing)
    db.add(DrawingPage(
        drawing_id=drawing.id, page_number=1, image_name="p.png", width=1000, height=500,
        dpi=150, metadata_status="ready", detected_discipline="建筑",
        drawing_title="建筑平面图", extracted_text="详见结构图"
    ))
    db.commit()
    task = ReviewTask(project_id=project.id, status="queued", progress=0)
    db.add(task); db.commit(); db.refresh(task)
    run_review(task.id, db)
    issue = db.query(ReviewIssue).filter_by(review_id=task.id, rule_id="META-XREF-001").first()
    assert issue is not None
    assert "结构" in issue.evidence


def test_drawing_reference_rule():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.db import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    project = Project(name="图号引用测试")
    db.add(project); db.commit(); db.refresh(project)
    drawing = Drawing(project_id=project.id, original_name="set.pdf", stored_name="set.pdf", mime_type="application/pdf", size_bytes=1, sha256="1"*64, status="ready")
    db.add(drawing); db.commit(); db.refresh(drawing)
    db.add(DrawingPage(
        drawing_id=drawing.id, page_number=1, image_name="p.png", width=1000, height=500,
        dpi=150, metadata_status="ready", drawing_number="A-101", detected_discipline="建筑",
        extracted_text="详见结构图 S-201"
    ))
    db.commit()
    task = ReviewTask(project_id=project.id, status="queued", progress=0)
    db.add(task); db.commit(); db.refresh(task)
    run_review(task.id, db)
    issue = db.query(ReviewIssue).filter_by(review_id=task.id, rule_id="META-XREF-002").first()
    assert issue is not None
    assert "S-201" in issue.evidence
