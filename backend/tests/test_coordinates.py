import pytest
from app.coordinates import normalize_box, denormalize_box

def test_normalize_box_clamps_and_orders():
    assert normalize_box(120, 80, -20, 40, 1000, 500) == pytest.approx((0.0, 0.08, 0.12, 0.16))

def test_denormalize_box_round_trip():
    box = normalize_box(100, 50, 400, 250, 1000, 500)
    assert denormalize_box(box, 1000, 500) == pytest.approx((100, 50, 400, 250))
