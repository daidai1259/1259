from pathlib import Path

from PIL import Image
from pypdf import PdfWriter

from app.processing import FileInspectionError, inspect_file, sha256_file

def make_pdf(path: Path):
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with path.open("wb") as output:
        writer.write(output)

def make_png(path: Path):
    Image.new("RGB", (1200, 800), "white").save(path, format="PNG")

def test_valid_pdf(tmp_path: Path):
    path = tmp_path / "A-101建筑.pdf"
    make_pdf(path)
    result = inspect_file(path, path.name, "application/pdf")
    assert result["kind"] == "pdf"
    assert result["page_count"] == 1
    assert len(result["sha256"]) == 64
    assert result["discipline"] == "建筑"

def test_valid_png(tmp_path: Path):
    path = tmp_path / "S-101结构.png"
    make_png(path)
    result = inspect_file(path, path.name, "image/png")
    assert result["kind"] == "image"
    assert result["page_count"] == 1
    assert result["width"] == 1200
    assert result["height"] == 800
    assert result["discipline"] == "结构"

def test_empty_file_rejected(tmp_path: Path):
    path = tmp_path / "empty.pdf"
    path.touch()
    try:
        inspect_file(path, path.name, "application/pdf")
        assert False
    except FileInspectionError as exc:
        assert "为空" in str(exc)

def test_corrupt_pdf_rejected(tmp_path: Path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"not a pdf")
    try:
        inspect_file(path, path.name, "application/pdf")
        assert False
    except FileInspectionError:
        pass

def test_corrupt_png_rejected(tmp_path: Path):
    path = tmp_path / "bad.png"
    path.write_bytes(b"not an image")
    try:
        inspect_file(path, path.name, "image/png")
        assert False
    except FileInspectionError:
        pass

def test_sha256_is_stable(tmp_path: Path):
    path = tmp_path / "file.png"
    make_png(path)
    assert sha256_file(path) == sha256_file(path)
