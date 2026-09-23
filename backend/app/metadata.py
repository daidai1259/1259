from __future__ import annotations
import re
from pathlib import Path
import fitz

DRAWING_NUMBER_RE = re.compile(r"\b([A-Z]{1,4}[-_]?\d{2,4}(?:[-_]?[A-Z0-9]+)?)\b")
SCALE_RE = re.compile(r"(?:比例|SCALE)\s*[:：]?\s*(\d+\s*[:：]\s*\d+|\d+倍)", re.IGNORECASE)

def clean_text(text: str, limit: int = 12000) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:limit]

def infer_page_metadata(text: str, filename: str = "") -> dict:
    text = clean_text(text)
    number_match = DRAWING_NUMBER_RE.search(text) or DRAWING_NUMBER_RE.search(filename.upper())
    scale_match = SCALE_RE.search(text)
    title = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if any(key in line for key in ("平面图", "立面图", "剖面图", "系统图", "详图", "施工图")):
            title = line[:255]
            break
    discipline = None
    joined = " ".join(lines[:80])
    for name, terms in {
        "建筑": ("建筑", "ARCH"),
        "结构": ("结构", "STRUCT"),
        "给排水": ("给排水", "PLUMB"),
        "电气": ("电气", "ELECT"),
        "暖通": ("暖通", "HVAC"),
    }.items():
        if any(term.lower() in joined.lower() for term in terms):
            discipline = name
            break
    return {
        "drawing_number": number_match.group(1) if number_match else None,
        "drawing_title": title,
        "detected_discipline": discipline,
        "scale_text": scale_match.group(1).replace("：", ":") if scale_match else None,
    }

def extract_pdf_page_metadata(pdf_path: Path, page_number: int, filename: str = "") -> dict:
    document = None
    try:
        document = fitz.open(str(pdf_path))
        page = document.load_page(page_number - 1)
        text = page.get_text("text")
        return {"extracted_text": clean_text(text), **infer_page_metadata(text, filename)}
    finally:
        if document is not None:
            document.close()

def extract_pdf_page_text_items(pdf_path: Path, page_number: int) -> list[dict]:
    document = None
    try:
        document = fitz.open(str(pdf_path))
        page = document.load_page(page_number - 1)
        items = []
        for word in page.get_text("words"):
            x0, y0, x1, y1, text, block_no, line_no, word_no = word[:8]
            text = text.strip()
            if not text:
                continue
            items.append({
                "text": text,
                "x0": float(x0), "y0": float(y0),
                "x1": float(x1), "y1": float(y1),
                "confidence": None,
                "source": "pdf_text",
                "block_no": int(block_no), "line_no": int(line_no), "word_no": int(word_no),
                "coordinate_space": "pdf_points",
            })
        return items
    finally:
        if document is not None:
            document.close()

def extract_image_metadata(image_path: Path, filename: str = "") -> dict:
    return {"extracted_text": None, **infer_page_metadata("", filename)}
