"""成本模型 (Sprint 4 实现)。

手续费 + 滑点是回测一等公民, 而非可选项 —— 否则会产出"虚假高收益"因子,
违背平台定位。本模块纯函数: 输入仓位序列, 输出每期成本序列。

成本发生在"换手"时刻: 当期仓位相对上期发生变化, 按换手量计费。
  turnover_t = |position_t - position_{t-1}|
  cost_t     = turnover_t * (fee_rate + slippage_bps/1e4)
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CostConfig:
    """成本配置。

    fee_rate:     单边手续费率 (小数, 如 0.0005 = 5bp)
    slippage_bps: 单边滑点 (基点 bps, 1bp = 0.01%)
    """

    fee_rate: float = 0.0005
    slippage_bps: float = 1.0

    @property
    def per_turnover_cost(self) -> float:
        return float(self.fee_rate) + float(self.slippage_bps) / 1e4


def turnover(positions: pd.Series) -> pd.Series:
    """每期换手量 |Δposition|。首期按建仓量计。"""
    diff = positions.diff()
    diff.iloc[0] = positions.iloc[0] if len(positions) else 0.0
    return diff.abs()


def apply_costs(positions: pd.Series, config: CostConfig | None = None) -> pd.Series:
    """按仓位换手计算每期交易成本 (收益率口径, 正数表示损耗)。"""
    cfg = config or CostConfig()
    return turnover(positions) * cfg.per_turnover_cost
