"""成本模型 (契约占位, Sprint 4 实现)。

手续费 + 滑点 + 冲击成本。是回测引擎的一等公民, 而非可选项 ——
否则会产出"虚假高收益"因子, 违背平台定位。
"""

# def apply_costs(trades, fee_rate, slippage, ...) -> "pd.Series": ...
