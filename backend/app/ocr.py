from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass(frozen=True)
class OCRWord:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float | None = None

@dataclass(frozen=True)
class OCRResult:
    words: list[OCRWord]
    width: int
    height: int
    source: str

def normalize_word(word: OCRWord, width: int, height: int) -> tuple[float, float, float, float]:
    if width <= 0 or height <= 0:
        raise ValueError("OCR 页面尺寸必须大于 0")
    return (max(0.0, min(1.0, word.x0 / width)), max(0.0, min(1.0, word.y0 / height)),
            max(0.0, min(1.0, word.x1 / width)), max(0.0, min(1.0, word.y1 / height)))

class OCRProvider(Protocol):
    name: str
    def recognize(self, image_path: Path) -> OCRResult: ...

class NoopOCRProvider:
    """Explicit placeholder for scanned-image OCR until a real provider is configured."""
    name = "noop"

    def recognize(self, image_path: Path) -> OCRResult:
        from PIL import Image
        with Image.open(image_path) as image:
            width, height = image.size
        return OCRResult(words=[], width=width, height=height, source=self.name)

def get_ocr_provider() -> OCRProvider:
    # Keep provider selection centralized so PaddleOCR/Tesseract/cloud OCR
    # can be introduced without changing the ingestion data model.
    return NoopOCRProvider()
