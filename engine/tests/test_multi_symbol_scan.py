"""多标的参数扫描测试。"""

from __future__ import annotations

from engine.factor_engine import sample_price_frame
from engine.param_scan import scan_template_multi_symbol


def test_multi_symbol_scan_averages_scores():
    frames = {
        "RB": sample_price_frame(280, seed=1),
        "AU": sample_price_frame(280, seed=2),
    }
    results = scan_template_multi_symbol(frames, "momentum", steps=6)
    assert len(results) >= 4
    assert results[0].get("symbol_breakdown")
    assert "RB" in results[0]["symbol_breakdown"]
    assert "AU" in results[0]["symbol_breakdown"]
