from __future__ import annotations

from pathlib import Path
import fitz
from PIL import Image

class RenderingError(ValueError):
    pass

DEFAULT_DPI = 150
MAX_PAGE_PIXELS = 40_000_000

def render_pdf(pdf_path: Path, output_dir: Path, dpi: int = DEFAULT_DPI) -> list[dict]:
    if dpi < 72 or dpi > 300:
        raise RenderingError("DPI 必须在 72 到 300 之间")
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    document = None
    try:
        document = fitz.open(str(pdf_path))
        if document.is_encrypted:
            raise RenderingError("不支持加密 PDF")
        if document.page_count < 1:
            raise RenderingError("PDF 不包含有效页面")
        scale = dpi / 72
        matrix = fitz.Matrix(scale, scale)
        for index in range(document.page_count):
            page = document.load_page(index)
            width = int(round(page.rect.width * scale))
            height = int(round(page.rect.height * scale))
            if width * height > MAX_PAGE_PIXELS:
                raise RenderingError(f"第 {index + 1} 页像素量过大")
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_name = f"page-{index + 1:04d}.png"
            pixmap.save(str(output_dir / image_name))
            with Image.open(output_dir / image_name) as image:
                actual_width, actual_height = image.size
            results.append({"page_number": index + 1, "image_name": image_name, "width": actual_width, "height": actual_height, "dpi": dpi})
    except RenderingError:
        for item in results:
            (output_dir / item["image_name"]).unlink(missing_ok=True)
        raise
    except Exception as exc:
        for item in results:
            (output_dir / item["image_name"]).unlink(missing_ok=True)
        raise RenderingError("PDF 页面渲染失败") from exc
    finally:
        if document is not None:
            document.close()
    return results

def validate_image_dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
    except Exception as exc:
        raise RenderingError("页面图像损坏或无法读取") from exc
    if width < 1 or height < 1 or width * height > MAX_PAGE_PIXELS:
        raise RenderingError("页面图像尺寸不安全")
    return width, height
