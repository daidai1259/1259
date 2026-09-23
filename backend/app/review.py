from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session, selectinload
from .models import DrawingPage, ReviewTask
from .review_rules import run_duplicate_drawing_number_rules, run_registered_rules

def utcnow():
    return datetime.now(timezone.utc)

def run_review(review_id: int, db: Session) -> None:
    task = db.get(ReviewTask, review_id)
    if not task or task.status not in {"queued", "retry"}:
        return
    task.status = "processing"
    task.progress = 5
    task.attempts += 1
    task.started_at = utcnow()
    task.finished_at = None
    task.error = None
    db.commit()
    try:
        pages = (
            db.query(DrawingPage)
            .options(selectinload(DrawingPage.text_items))
            .join(DrawingPage.drawing)
            .filter(DrawingPage.drawing.has(project_id=task.project_id))
            .order_by(DrawingPage.id)
            .all()
        )
        total = max(len(pages), 1)
        for index, page in enumerate(pages, start=1):
            run_registered_rules(page, task.id, db)
            task.progress = min(90, 5 + int(index / total * 80))
            db.commit()
        run_duplicate_drawing_number_rules(pages, task.id, db)
        run_cross_page_consistency_rules, run_discipline_consistency_rules, run_drawing_number_structure_rules, run_cross_discipline_reference_rules, run_drawing_reference_rules, run_reference_discipline_rules, run_drawing_set_completeness_rules(pages, task.id, db)
        db.commit()
        task.status = "completed"
        task.progress = 100
        task.finished_at = utcnow()
        db.commit()
    except Exception:
        db.rollback()
        task = db.get(ReviewTask, review_id)
        if task:
            task.status = "failed"
            task.progress = 100
            task.error = "审核任务执行失败"
            task.finished_at = utcnow()
            db.commit()
        raise
