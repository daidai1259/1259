from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import DrawingPage, ReviewIssue, ReviewTask

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
            .join(DrawingPage.drawing)
            .filter(DrawingPage.drawing.has(project_id=task.project_id))
            .order_by(DrawingPage.id)
            .all()
        )
        total = max(len(pages), 1)
        for index, page in enumerate(pages, start=1):
            checks = [
                ("META-DWG-001", "图签", "warning", "未识别到图号",
                 "当前页面未从文字层识别到可靠图号。扫描件可能需要 OCR 后重新检查。"),
                ("META-SCALE-001", "图签", "warning", "未识别到比例",
                 "当前页面未识别到比例信息。请结合图签或设计说明人工确认。"),
            ]
            for rule_id, category, severity, title, description in checks:
                if rule_id.endswith("001") and ((rule_id.startswith("META-DWG") and not page.drawing_number)
                    or (rule_id.startswith("META-SCALE") and not page.scale_text)):
                    db.add(ReviewIssue(
                        review_id=task.id, page_id=page.id, rule_id=rule_id,
                        category=category, severity=severity, title=title,
                        description=description, evidence=page.extracted_text[:1000] if page.extracted_text else None,
                        confidence=0.65 if page.extracted_text else 0.35,
                    ))
            task.progress = min(95, 5 + int(index / total * 90))
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
