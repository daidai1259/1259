from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import os
import shutil

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
    return (
        max(0.0, min(1.0, word.x0 / width)),
        max(0.0, min(1.0, word.y0 / height)),
        max(0.0, min(1.0, word.x1 / width)),
        max(0.0, min(1.0, word.y1 / height)),
    )

class OCRProvider(Protocol):
    name: str
    def recognize(self, image_path: Path) -> OCRResult: ...

class NoopOCRProvider:
    name = "noop"
    def recognize(self, image_path: Path) -> OCRResult:
        from PIL import Image
        with Image.open(image_path) as image:
            width, height = image.size
        return OCRResult(words=[], width=width, height=height, source=self.name)

class TesseractOCRProvider:
    name = "tesseract"
    def __init__(self, lang: str = "eng"):
        if shutil.which("tesseract") is None:
            raise RuntimeError("OCR_PROVIDER=tesseract 但系统未安装 tesseract")
        try:
            import pytesseract
        except ImportError as exc:
            raise RuntimeError("OCR_PROVIDER=tesseract 但未安装 pytesseract") from exc
        self._pytesseract = pytesseract
        self.lang = lang

    def recognize(self, image_path: Path) -> OCRResult:
        from PIL import Image
        with Image.open(image_path) as image:
            width, height = image.size
            data = self._pytesseract.image_to_data(
                image, lang=self.lang, output_type=self._pytesseract.Output.DICT
            )
        words: list[OCRWord] = []
        for i, raw_text in enumerate(data.get("text", [])):
            text = str(raw_text).strip()
            if not text:
                continue
            try:
                confidence = float(data["conf"][i])
                if confidence < 0:
                    confidence = None
            except (KeyError, TypeError, ValueError, IndexError):
                confidence = None
            x = int(data["left"][i])
            y = int(data["top"][i])
            w = int(data["width"][i])
            h = int(data["height"][i])
            words.append(OCRWord(text, x, y, x + w, y + h, confidence))
        return OCRResult(words=words, width=width, height=height, source=self.name)

def get_ocr_provider() -> OCRProvider:
    provider = os.getenv("OCR_PROVIDER", "noop").strip().lower()
    if provider == "tesseract":
        return TesseractOCRProvider(os.getenv("OCR_LANG", "eng"))
    if provider in {"", "noop", "none"}:
        return NoopOCRProvider()
    raise RuntimeError(f"不支持的 OCR_PROVIDER: {provider}")
