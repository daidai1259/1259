from pathlib import Path
import fitz
from app.metadata import extract_pdf_page_metadata, extract_pdf_page_text_items, infer_page_metadata

def test_infer_metadata():
    result = infer_page_metadata("建筑平面图\n图号 A-101\n比例 1:100")
    assert result["drawing_number"] == "A-101"
    assert result["drawing_title"] == "建筑平面图"
    assert result["detected_discipline"] == "建筑"
    assert result["scale_text"] == "1:100"

def test_extract_pdf_page_metadata(tmp_path: Path):
    pdf = tmp_path / "drawing.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "结构平面图\n图号 S-201\n比例 1:50")
    doc.save(str(pdf))
    doc.close()
    result = extract_pdf_page_metadata(pdf, 1, pdf.name)
    assert "结构平面图" in result["extracted_text"]
    assert result["drawing_number"] == "S-201"
    assert result["detected_discipline"] == "结构"

def test_extract_pdf_page_text_items_preserves_coordinates(tmp_path: Path):
    pdf = tmp_path / "drawing.pdf"
    doc = fitz.open()
    page = doc.new_page(width=600, height=400)
    page.insert_text((100, 120), "轴线 A-101")
    doc.save(str(pdf))
    doc.close()

    items = extract_pdf_page_text_items(pdf, 1)
    assert items
    item = next(item for item in items if item["text"] == "A-101")
    assert item["source"] == "pdf_text"
    assert item["coordinate_space"] == "pdf_points"
    assert item["x0"] >= 100
    assert item["y0"] < item["y1"]
    assert item["x1"] > item["x0"]
