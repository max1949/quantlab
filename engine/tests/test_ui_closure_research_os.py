"""UI closure regression — research OS thin wrap + labels + P0 paper_orders retire."""

from __future__ import annotations

from engine.ui_labels_zh import explain_decision, gate_flags_zh


def test_decision_zh_labels():
    p = explain_decision("PROMOTE", ["ok"])
    assert p["label_zh"] == "建议晋级"
    h = explain_decision("HOLD", ["debt"])
    assert "暂缓" in h["label_zh"]
    k = explain_decision("KILL", ["fail"])
    assert k["label_zh"] == "淘汰"
    assert "实盘" in p["live_note_zh"]


def test_gate_flags_zh():
    g = gate_flags_zh({"oos": "PASS", "walk_forward": "INSUFFICIENT"})
    assert g["oos"]["flag_zh"] == "通过"
    assert g["walk_forward"]["flag_zh"] == "证据不足"


def test_research_os_service_core():
    from backend.app.services import research_os_service as ros

    pkgs = ros.list_strategy_packages()
    assert any(p.get("strategy_id") == "hist_fl_momentum_w20" for p in pkgs if "strategy_id" in p)
    paper = ros.run_factor_sign_paper_api("hist_fl_momentum_w20", bars=120)
    assert paper["PAPER_RUNTIME"] == "CANONICAL"
    assert paper["LEGACY_PAPER_ORDERS_USED"] == "NO"
    assert paper["parity"]["FACTOR_SIGN_SPEC_TO_PAPER_SEMANTIC_PARITY"] == "PASS"
    ready = ros.live_readiness_card()
    assert ready["headline_zh"]
    assert ready["QLN_11_STARTED"] == "NO"
    assert ready["REAL_MONEY"] == "NO"
    assert "≠" in ready["headline_zh"] or "不等于" in ready["headline_zh"]
    gov = ros.portfolio_governor_view()
    assert "分散" in gov.get("warning_zh", "")
    doctrine = ros.doctrine_nav()
    assert "先证明" in doctrine["doctrine_zh"]


def test_create_paper_order_route_gone_message_in_source():
    from pathlib import Path

    src = Path("backend/app/api/v1/routes/execution.py").read_text(encoding="utf-8")
    assert "HTTP_410_GONE" in src
    assert "paper_orders" in src
    assert "正式 PaperRun" in src or "PaperRun" in src
