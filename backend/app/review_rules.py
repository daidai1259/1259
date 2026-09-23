from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable
from typing import Iterable
import re
from sqlalchemy.orm import Session
from .models import DrawingPage, ReviewIssue
from .coordinates import normalize_box

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


def _text_box(page: DrawingPage, needle: str) -> tuple[float, float, float, float] | None:
    needle = needle.strip().lower()
    if not needle or not page.width or not page.height:
        return None
    for item in page.text_items:
        text = (item.text or "").strip().lower()
        if text == needle or needle in text:
            box = normalize_box(item.x0, item.y0, item.x1, item.y1, page.width, page.height)
            return (box.x0, box.y0, box.x1, box.y1)
    return None


def _issue_kwargs(page: DrawingPage, needle: str | None = None) -> dict:
    if not needle:
        return {}
    box = _text_box(page, needle)
    if not box:
        return {}
    return {"x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3]}

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
            **_issue_kwargs(page, page.scale_text if rule.rule_id == "META-SCALE-002" else None),
        ))
        created += 1
    return created


def _normalized_value(value: str | None) -> str:
    return re.sub(r"\s+", "", (value or "").strip().upper())


def run_cross_page_consistency_rules(pages: Iterable[DrawingPage], review_id: int, db: Session) -> int:
    pages = list(pages)
    groups: dict[str, list[DrawingPage]] = {}
    for page in pages:
        title = _normalized_value(page.drawing_title)
        if title:
            groups.setdefault(title, []).append(page)
    created = 0
    for title, matches in groups.items():
        numbers = {_normalized_value(p.drawing_number) for p in matches if _normalized_value(p.drawing_number)}
        if len(numbers) <= 1:
            continue
        page_list = "、".join(str(p.page_number) for p in matches)
        for page in matches:
            db.add(ReviewIssue(
                review_id=review_id, page_id=page.id, rule_id="META-CONSIST-001",
                category="跨页一致性", severity="medium", title="同名图纸图号不一致",
                description="检测到相同图名对应多个图号，请核对图签及图号识别结果。",
                evidence=f"图名：{page.drawing_title}；涉及页面：{page_list}",
                confidence=0.82, coordinate_space="normalized",
                **_issue_kwargs(page, page.drawing_title),
            ))
            created += 1
    return created


def run_drawing_number_structure_rules(pages: Iterable[DrawingPage], review_id: int, db: Session) -> int:
    pattern = re.compile(r"^([A-Z]+)[-_]?(\d{3})$", re.IGNORECASE)
    groups: dict[str, list[tuple[DrawingPage, int]]] = {}
    for page in pages:
        value = _normalized_value(page.drawing_number)
        match = pattern.fullmatch(value)
        if match:
            prefix = match.group(1).upper()
            number = int(match.group(2))
            groups.setdefault(prefix, []).append((page, number))
    created = 0
    for prefix, entries in groups.items():
        by_number: dict[int, list[DrawingPage]] = {}
        for page, number in entries:
            by_number.setdefault(number, []).append(page)
        numbers = sorted(by_number)
        for left, right in zip(numbers, numbers[1:]):
            if right - left <= 1:
                continue
            for missing in range(left + 1, right):
                sample = by_number[left][0]
                db.add(ReviewIssue(
                    review_id=review_id, page_id=sample.id, rule_id="META-DWG-003",
                    category="图号连续性", severity="low", title="图号序列存在间隔",
                    description=f"检测到 {prefix} 图号从 {left:03d} 跳到 {right:03d}，中间存在未发现的编号。请确认是否存在漏图、分册或编号规则。",
                    evidence=f"相邻检测图号：{prefix}-{left:03d}、{prefix}-{right:03d}；疑似缺失：{prefix}-{missing:03d}",
                    confidence=0.70, coordinate_space="normalized",
                    **_issue_kwargs(sample, sample.drawing_number),
                ))
                created += 1
    return created


def run_discipline_consistency_rules(pages: Iterable[DrawingPage], review_id: int, db: Session) -> int:
    pages = list(pages)
    groups: dict[str, list[DrawingPage]] = {}
    for page in pages:
        number = _normalized_value(page.drawing_number)
        if number and page.detected_discipline:
            groups.setdefault(number, []).append(page)
    created = 0
    for number, matches in groups.items():
        disciplines = {_normalized_value(p.detected_discipline) for p in matches}
        if len(disciplines) <= 1:
            continue
        page_list = "、".join(str(p.page_number) for p in matches)
        for page in matches:
            db.add(ReviewIssue(
                review_id=review_id, page_id=page.id, rule_id="META-CONSIST-002",
                category="跨页一致性", severity="medium", title="同图号专业识别不一致",
                description="相同图号在审核范围内被识别为不同专业，请核对图签、文件归类或专业识别结果。",
                evidence=f"图号：{page.drawing_number}；涉及页面：{page_list}",
                confidence=0.78, coordinate_space="normalized",
                **_issue_kwargs(page, page.drawing_number),
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
                **_issue_kwargs(page, number),
            ))
            created += 1
    return created
