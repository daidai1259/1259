from pathlib import Path
from PIL import Image
from app.processing import FileInspectionError, inspect_file, sha256_file

def make_pdf(path: Path):
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with path.open("wb") as output:
        writer.write(output)

def make_png(path: Path):
    Image.new("RGB", (1200, 800), "white").save(path, format="PNG")

def test_valid_pdf(tmp_path: Path):
    path = tmp_path / "A-101建筑.pdf"; make_pdf(path)
    result = inspect_file(path, path.name, "application/pdf")
    assert result["kind"] == "pdf" and result["page_count"] == 1
    assert len(result["sha256"]) == 64 and result["discipline"] == "建筑"

def test_valid_png(tmp_path: Path):
    path = tmp_path / "S-101结构.png"; make_png(path)
    result = inspect_file(path, path.name, "image/png")
    assert result["kind"] == "image" and result["width"] == 1200 and result["height"] == 800
    assert result["discipline"] == "结构"

def test_empty_file_rejected(tmp_path: Path):
    path = tmp_path / "empty.pdf"; path.touch()
    try: inspect_file(path, path.name, "application/pdf"); assert False
    except FileInspectionError as exc: assert "为空" in str(exc)

def test_corrupt_pdf_rejected(tmp_path: Path):
    path = tmp_path / "bad.pdf"; path.write_bytes(b"not a pdf")
    try: inspect_file(path, path.name, "application/pdf"); assert False
    except FileInspectionError: pass

def test_corrupt_png_rejected(tmp_path: Path):
    path = tmp_path / "bad.png"; path.write_bytes(b"not an image")
    try: inspect_file(path, path.name, "image/png"); assert False
    except FileInspectionError: pass

def test_sha256_is_stable(tmp_path: Path):
    path = tmp_path / "file.png"; make_png(path)
    assert sha256_file(path) == sha256_file(path)

def test_mime_extension_mismatch_rejected(tmp_path: Path):
    path = tmp_path / "drawing.png"; make_png(path)
    try: inspect_file(path, path.name, "image/jpeg"); assert False
    except FileInspectionError as exc: assert "扩展名" in str(exc)

def test_jpeg_is_accepted_without_imghdr(tmp_path: Path):
    path = tmp_path / "drawing.jpg"
    Image.new("RGB", (800, 600), "white").save(path, format="JPEG")
    result = inspect_file(path, path.name, "image/jpeg")
    assert result["format"] == "JPEG" and result["width"] == 800
