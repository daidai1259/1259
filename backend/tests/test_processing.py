from pathlib import Path
from app.processing import classify_drawing, inspect_file

def test_classify_drawing():
    assert classify_drawing("A-101建筑平面图.png") == "建筑"
    assert classify_drawing("S-202结构平面图.pdf") == "结构"
    assert classify_drawing("E-301电气系统图.png") == "电气"
    assert classify_drawing("unknown.png") is None

def test_inspect_file(tmp_path: Path):
    path = tmp_path / "A-101.png"
    path.write_bytes(b"test")
    result = inspect_file(path, path.name)
    assert result["kind"] == "image"
    assert result["discipline"] == "建筑"
