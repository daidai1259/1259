from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class NormalizedBox:
    x0: float
    y0: float
    x1: float
    y1: float

def normalize_box(x0: float, y0: float, x1: float, y1: float, width: float, height: float) -> NormalizedBox:
    if width <= 0 or height <= 0:
        raise ValueError("页面尺寸必须大于 0")
    left, right = sorted((float(x0), float(x1)))
    top, bottom = sorted((float(y0), float(y1)))
    return NormalizedBox(
        max(0.0, min(1.0, left / width)),
        max(0.0, min(1.0, top / height)),
        max(0.0, min(1.0, right / width)),
        max(0.0, min(1.0, bottom / height)),
    )

def denormalize_box(box: NormalizedBox, width: float, height: float) -> tuple[float, float, float, float]:
    if width <= 0 or height <= 0:
        raise ValueError("页面尺寸必须大于 0")
    return box.x0 * width, box.y0 * height, box.x1 * width, box.y1 * height
