from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable
from typing import Iterable
import re
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

def _has_text(page: DrawingPage) -> bool:
    return bool((page.extracted_text or "").strip())

def _scale_is_invalid(page: DrawingPage) -> bool:
    value = (page.scale_text or "").replace("：", ":").strip()
    if not value:
        return False
    return re.fullmatch(r"\d+\s*:\s*\d+", value) is None and re.fullmatch(r"\d+倍", value) is None

RULES: tuple[ReviewRule, ...] = (
    ReviewRule(
        "META-DWG-001", "图签", "medium", "未识别到图号",
        "当前页面未从文字层或 OCR 识别到可靠图号。请结合图签人工确认。",
        lambda p: not p.drawing_number,
        lambda p: 0.65 if _has_text(p) else 0.35,
    ),
    ReviewRule(
        "META-SCALE-001", "图签", "medium", "未识别到比例",
        "当前页面未识别到比例信息。请结合图签或设计说明人工确认。",
        lambda p: not p.scale_text,
        lambda p: 0.65 if _has_text(p) else 0.35,
    ),
    ReviewRule(
        "META-TITLE-001", "图签", "low", "未识别到图名",
        "当前页面未识别到明确图名。请检查图签或页面标题。",
        lambda p: not p.drawing_title,
        lambda p: 0.60 if _has_text(p) else 0.30,
    ),
    ReviewRule(
        "META-SCALE-002", "图签", "low", "比例格式异常",
        "已识别到比例文本，但格式无法按当前识别规则确认。请人工核对原图图签。",
        _scale_is_invalid,
        lambda p: 0.75,
    ),
)

def run_registered_rules(page: DrawingPage, review_id: int, db: Session) -> int:
    return run_page_rules(page, review_id, db)


def run_page_rules(page: DrawingPage, review_id: int, db: Session) -> int:
    created = 0
    evidence = (page.extracted_text or "").strip()[:1000] or None
    for rule in RULES:
        if not rule.predicate(page):
            continue
        db.add(ReviewIssue(
            review_id=review_id,
            page_id=page.id,
            rule_id=rule.rule_id,
            category=rule.category,
            severity=rule.severity,
            title=rule.title,
            description=rule.description,
            evidence=evidence,
            confidence=rule.confidence(page),
            coordinate_space="normalized",
        ))
        created += 1
    return created


def run_duplicate_drawing_number_rules(
    pages: Iterable[DrawingPage], review_id: int, db: Session
) -> int:
    groups: dict[str, list[DrawingPage]] = {}
    for page in pages:
        number = (page.drawing_number or "").strip().upper()
        if number:
            groups.setdefault(number, []).append(page)

    created = 0
    for number, matches in groups.items():
        if len(matches) < 2:
            continue
        page_list = "、".join(str(p.page_number) for p in matches)
        for page in matches:
            db.add(ReviewIssue(
                review_id=review_id,
                page_id=page.id,
                rule_id="META-DWG-002",
                category="图签一致性",
                severity="medium",
                title="图号重复",
                description=f"审核范围内发现图号 {number} 出现在多个页面。请核对是否为重复图纸或图号识别错误。",
                evidence=f"重复图号：{number}；涉及页面：{page_list}",
                confidence=0.90,
                coordinate_space="normalized",
            ))
            created += 1
    return created
