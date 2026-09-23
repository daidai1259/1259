from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

SUPPORTED_SUFFIXES = {".pdf": "pdf", ".jpg": "image", ".jpeg": "image", ".png": "image"}
ALLOWED_MIME_TYPES = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}

class FileInspectionError(ValueError):
    """Raised when a drawing file cannot be safely inspected."""

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()

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

def _inspect_image(path: Path) -> dict:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            image_format = (image.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise FileInspectionError("图片文件损坏或无法解析") from exc

    if image_format not in {"JPEG", "PNG"}:
        raise FileInspectionError("图片实际格式不是受支持的 JPG/PNG")
    return {
        "kind": "image",
        "page_count": 1,
        "width": width,
        "height": height,
        "format": image_format,
    }

def _inspect_pdf(path: Path) -> dict:
    try:
        reader = PdfReader(str(path), strict=True)
        if reader.is_encrypted:
            raise FileInspectionError("暂不支持加密 PDF")
        page_count = len(reader.pages)
    except FileInspectionError:
        raise
    except Exception as exc:
        raise FileInspectionError("PDF 文件损坏或无法解析") from exc

    if page_count < 1:
        raise FileInspectionError("PDF 不包含有效页面")
    return {"kind": "pdf", "page_count": page_count, "width": None, "height": None, "format": "PDF"}

def inspect_file(path: Path, original_name: str, mime_type: str | None = None) -> dict:
    if not path.is_file():
        raise FileInspectionError("文件不存在")
    if path.stat().st_size == 0:
        raise FileInspectionError("文件为空")

    suffix = path.suffix.lower()
    expected_mime = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(suffix)
    if not expected_mime:
        raise FileInspectionError("不支持的图纸格式")
    if mime_type and mime_type != expected_mime:
        raise FileInspectionError("文件扩展名与 MIME 类型不一致")

    result = _inspect_pdf(path) if SUPPORTED_SUFFIXES[suffix] == "pdf" else _inspect_image(path)
    result.update({
        "sha256": sha256_file(path),
        "discipline": classify_drawing(original_name),
        "suffix": suffix,
    })
    return result
