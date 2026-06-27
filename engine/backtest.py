"""回测 (契约占位, Sprint 4 实现)。

输入: 因子信号 + 行情 + 成本配置。
输出: 收益 (AnnualReturn/TotalReturn) + 风险 (MaxDrawdown/Sharpe/Volatility)
      + 交易 (TradeCount/WinRate/Turnover) + 净值曲线。
纯函数: 不读数据库, 不发网络请求。
"""

# def run_backtest(signal, ohlcv, cost_config) -> dict: ...
