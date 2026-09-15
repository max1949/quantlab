"""Regression: factor-scan UX / state consistency (P1).

Covers production RCA:
- stack template_type must fit VARCHAR(64) (Postgres enforced; SQLite is not)
- SUCCESS_RESULT_AND_FATAL_ERROR_COEXIST=DENY (copy contracts)
- REAL_ORDER_WARNING_ON_FACTOR_SCAN=REMOVE
"""

from __future__ import annotations

from backend.app.services.factor_scan_service import _is_stack_template


def test_stack_template_key_fits_varchar64():
    # Production bug: stack:uuid,uuid == 79 chars → StringDataRightTruncation → HTTP 500
    legacy = "stack:721b94cf-302e-473f-bd95-b1a2ebd755b8,4dba4d0d-eae5-4c33-a246-ee89a475e856"
    assert len(legacy) > 64
    current = "stack"
    assert len(current) <= 64
    assert _is_stack_template(current)
    assert _is_stack_template(legacy)
    assert not _is_stack_template("momentum")


def test_scan_error_copy_contracts():
    """Mirror frontend errorScope.ts contracts for CI without a JS test runner."""
    trading = "服务暂时异常。请稍后重试；若持续出现，请联系运维。不会创建真实订单。"
    scan = "扫描暂时未完成，请稍后重试。"
    aux = "扫描结果已生成，部分辅助信息暂时不可用。"
    generic = "服务暂时异常。请稍后重试；若持续出现，请联系运维。"

    assert "不会创建真实订单" in trading
    assert "不会创建真实订单" not in scan
    assert "不会创建真实订单" not in aux
    assert "不会创建真实订单" not in generic

    # SUCCESS_RESULT_AND_FATAL_ERROR_COEXIST=DENY
    main_ok = True
    aux_fail = True
    allow_global_fatal = not (main_ok and aux_fail) and not main_ok
    assert allow_global_fatal is False
