"""卡密格式归一化单元测试。"""

from __future__ import annotations

from backend.app.services.card_pool_service import (
    is_bkta_code,
    normalize_card_code,
)


def test_normalize_card_code():
    assert normalize_card_code("bkta-abcd-efgh") == "BKTA-ABCD-EFGH"
    assert normalize_card_code("BKTAABCD EFGH") == "BKTA-ABCD-EFGH"
    assert is_bkta_code("BKTA-1234-5678")
    assert not is_bkta_code("QL-ABCDEF01")
