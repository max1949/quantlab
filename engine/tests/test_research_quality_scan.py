"""扫描发布预览与 IC 序列测试。"""

from __future__ import annotations

from engine.factor_engine import compute_template_factor, sample_price_frame
from engine.factor_metrics import factor_ic
from engine.research_quality import assess_scan_preview


def test_factor_ic_returns_series_and_ir():
    df = sample_price_frame(320)
    sig = compute_template_factor(df, "momentum", {"window": 20})
    ic = factor_ic(sig, df["close"])
    assert ic["n_obs"] > 50
    assert isinstance(ic.get("ic_series"), list)
    assert len(ic["ic_series"]) >= 2
    assert ic.get("ic_std") is not None
    assert ic.get("ic_ir") is not None


def test_assess_scan_preview_promising():
    good = assess_scan_preview(sharpe=1.1, oos_sharpe=0.4, ic_mean=0.05, turnover=20.0)
    assert good.promising is True
    assert good.hints

    weak = assess_scan_preview(sharpe=0.5, oos_sharpe=0.05, ic_mean=0.01, turnover=90.0)
    assert weak.promising is False
    assert any("样本外" in h or "换手" in h or "IC" in h for h in weak.hints)
