from pathlib import Path
import fitz
from PIL import Image
from app.rendering import RenderingError, render_pdf, validate_image_dimensions

def make_pdf(path: Path, pages: int = 2):
    document = fitz.open()
    for _ in range(pages):
        document.new_page(width=595, height=842)
    document.save(str(path))
    document.close()

def test_render_pdf_creates_one_image_per_page(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"; out = tmp_path / "pages"; make_pdf(pdf, 2)
    result = render_pdf(pdf, out, dpi=72)
    assert len(result) == 2
    assert (out / "page-0001.png").exists()
    assert (out / "page-0002.png").exists()

def test_render_pdf_rejects_invalid_dpi(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"; make_pdf(pdf, 1)
    try: render_pdf(pdf, tmp_path / "pages", dpi=50); assert False
    except RenderingError: pass

def test_render_pdf_rejects_corrupt_pdf(tmp_path: Path):
    pdf = tmp_path / "bad.pdf"; pdf.write_bytes(b"not pdf")
    try: render_pdf(pdf, tmp_path / "pages"); assert False
    except RenderingError: pass

def test_validate_image_dimensions(tmp_path: Path):
    image_path = tmp_path / "page.png"
    Image.new("RGB", (100, 200), "white").save(image_path)
    assert validate_image_dimensions(image_path) == (100, 200)
