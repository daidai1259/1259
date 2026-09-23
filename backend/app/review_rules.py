from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable
from sqlalchemy.orm import Session
from .models import DrawingPage, ReviewIssue

@dataclass(frozen=True)
class ReviewRule:
    rule_id: str
    category: str
    severity: str
    title: str
    description: str
    predicate: Callable[[DrawingPage], bool]
    confidence: Callable[[DrawingPage], float]

RULES: tuple[ReviewRule, ...] = (
    ReviewRule("META-DWG-001","图签","warning","未识别到图号",
        "当前页面未从文字层识别到可靠图号。扫描件可能需要 OCR 后重新检查。",
        lambda p: not p.drawing_number,
        lambda p: 0.65 if p.extracted_text else 0.35),
    ReviewRule("META-SCALE-001","图签","warning","未识别到比例",
        "当前页面未识别到比例信息。请结合图签或设计说明人工确认。",
        lambda p: not p.scale_text,
        lambda p: 0.65 if p.extracted_text else 0.35),
)

def run_registered_rules(page: DrawingPage, review_id: int, db: Session) -> int:
    created = 0
    for rule in RULES:
        if not rule.predicate(page):
            continue
        db.add(ReviewIssue(
            review_id=review_id, page_id=page.id, rule_id=rule.rule_id,
            category=rule.category, severity=rule.severity, title=rule.title,
            description=rule.description,
            evidence=page.extracted_text[:1000] if page.extracted_text else None,
            confidence=rule.confidence(page),
        ))
        created += 1
    return created
