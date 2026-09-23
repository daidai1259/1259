from pathlib import Path
from PIL import Image
from app.ocr import NoopOCRProvider, OCRResult, OCRWord, get_ocr_provider

def test_ocr_data_contract():
    word = OCRWord("A-101", 10, 20, 50, 40, 0.98)
    result = OCRResult([word], 100, 80, "test")
    assert result.words[0].text == "A-101"
    assert result.words[0].x1 > result.words[0].x0

def test_noop_provider_is_explicit(tmp_path: Path):
    image = tmp_path / "page.png"
    Image.new("RGB", (120, 80), "white").save(image)
    result = get_ocr_provider().recognize(image)
    assert isinstance(result, OCRResult)
    assert result.source == "noop"
    assert result.words == []
