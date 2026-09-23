from pathlib import Path
from typing import Optional

SUPPORTED_SUFFIXES = {".pdf": "pdf", ".jpg": "image", ".jpeg": "image", ".png": "image"}

def classify_drawing(filename: str) -> Optional[str]:
    name = filename.lower()
    rules = [
        ("建筑", ("建筑", "arch", "a-")),
        ("结构", ("结构", "struct", "s-")),
        ("给排水", ("给排水", "plumb", "p-")),
        ("电气", ("电气", "elect", "e-")),
        ("暖通", ("暖通", "hvac", "m-")),
    ]
    for discipline, terms in rules:
        if any(term in name for term in terms):
            return discipline
    return None

def inspect_file(path: Path, original_name: str) -> dict:
    suffix = path.suffix.lower()
    kind = SUPPORTED_SUFFIXES.get(suffix)
    if not kind:
        raise ValueError("不支持的图纸格式")
    return {"kind": kind, "discipline": classify_drawing(original_name), "page_count": None}
