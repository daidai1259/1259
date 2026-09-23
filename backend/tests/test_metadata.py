from pathlib import Path
import fitz
from app.metadata import extract_pdf_page_metadata, infer_page_metadata

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
