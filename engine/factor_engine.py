"""因子计算 (Sprint 3 实现)。

纯函数库: 只吃 pandas/numpy, 只吐 Series/dict, 不依赖 Web/DB/队列。
支持两类来源:
  1. 模板因子 (template): 平台预置的参数化因子 (动量/均线/RSI/波动率/均值回归)。
  2. 因子组合器 (stack): 把多个因子标准化后按权重线性组合。

约定: 输入行情 DataFrame (至少含 'close' 列, DatetimeIndex), 输出与其索引对齐的因子 Series。
真实行情数据在 Sprint 4 接入 (Parquet); 本模块提供确定性 `sample_price_frame`
用于预览/测试, 保证"可复现"。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 模板因子: 计算函数 (输入 df + 参数, 输出 Series)
# ---------------------------------------------------------------------------
def momentum(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """动量: 过去 window 期的收益率。"""
    return df["close"].pct_change(window)


def sma_ratio(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """价格相对均线偏离: close / SMA(window) - 1。"""
    sma = df["close"].rolling(window).mean()
    return df["close"] / sma - 1.0


def rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """相对强弱指标 (RSI), 取值 0~100。"""
    delta = df["close"].diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def volatility(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """波动率: 收益率的滚动标准差。"""
    return df["close"].pct_change().rolling(window).std()


def mean_reversion(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """均值回归: 价格相对滚动均值的负向 z-score (低于均值时取正, 预期回归)。"""
    close = df["close"]
    mean = close.rolling(window).mean()
    std = close.rolling(window).std()
    return -(close - mean) / std.replace(0.0, np.nan)


@dataclass(frozen=True)
class ParamSpec:
    name: str
    default: int
    min: int
    max: int
    label: str


@dataclass(frozen=True)
class FactorTemplate:
    code: str
    label: str
    description: str
    func: Callable[..., pd.Series]
    params: tuple[ParamSpec, ...]
    requires: tuple[str, ...] = ("close",)


TEMPLATES: dict[str, FactorTemplate] = {
    t.code: t
    for t in (
        FactorTemplate(
            "momentum",
            "动量因子",
            "过去 N 期收益率, 捕捉趋势延续。",
            momentum,
            (ParamSpec("window", 20, 2, 250, "回看窗口"),),
        ),
        FactorTemplate(
            "sma_ratio",
            "均线偏离",
            "价格相对 N 期均线的偏离度。",
            sma_ratio,
            (ParamSpec("window", 20, 2, 250, "均线窗口"),),
        ),
        FactorTemplate(
            "rsi",
            "RSI 强弱",
            "相对强弱指标 (0-100), 衡量超买超卖。",
            rsi,
            (ParamSpec("window", 14, 2, 100, "RSI 窗口"),),
        ),
        FactorTemplate(
            "volatility",
            "波动率",
            "收益率的滚动标准差, 衡量风险水平。",
            volatility,
            (ParamSpec("window", 20, 2, 250, "波动窗口"),),
        ),
        FactorTemplate(
            "mean_reversion",
            "均值回归",
            "价格相对均值的负向 z-score, 预期向均值回归。",
            mean_reversion,
            (ParamSpec("window", 20, 2, 250, "回看窗口"),),
        ),
    )
}


class FactorError(ValueError):
    """因子定义/参数非法。"""


def validate_template_params(factor_type: str, params: dict) -> dict:
    """校验并补全模板参数; 返回清洗后的参数 dict。"""
    tpl = TEMPLATES.get(factor_type)
    if tpl is None:
        raise FactorError(f"未知模板因子: {factor_type}")
    clean: dict = {}
    for spec in tpl.params:
        raw = params.get(spec.name, spec.default)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise FactorError(f"参数 {spec.name} 必须为整数")
        if not (spec.min <= value <= spec.max):
            raise FactorError(
                f"参数 {spec.name} 需在 [{spec.min}, {spec.max}] 之间"
            )
        clean[spec.name] = value
    return clean


def compute_template_factor(
    df: pd.DataFrame, factor_type: str, params: dict | None = None
) -> pd.Series:
    """计算模板因子, 返回与 df 对齐的 Series。"""
    tpl = TEMPLATES.get(factor_type)
    if tpl is None:
        raise FactorError(f"未知模板因子: {factor_type}")
    for col in tpl.requires:
        if col not in df.columns:
            raise FactorError(f"行情缺少必需列: {col}")
    clean = validate_template_params(factor_type, params or {})
    return tpl.func(df, **clean).rename(factor_type)


def standardize(series: pd.Series) -> pd.Series:
    """横截面/时序标准化 (z-score), 让不同量纲的因子可公平组合。"""
    std = series.std()
    if std == 0 or np.isnan(std):
        return series * 0.0
    return (series - series.mean()) / std


def compute_factor_stack(items: Iterable[tuple[pd.Series, float]]) -> pd.Series:
    """因子组合器: 各因子标准化后按权重线性组合。

    items: [(series, weight), ...]。权重自动归一化 (按绝对值之和)。
    """
    items = list(items)
    if not items:
        raise FactorError("组合器至少需要一个因子")
    weights = np.array([w for _, w in items], dtype=float)
    norm = np.abs(weights).sum()
    if norm == 0:
        raise FactorError("组合器权重不能全为 0")
    weights = weights / norm

    combined: pd.Series | None = None
    for (series, _), w in zip(items, weights):
        contrib = standardize(series).fillna(0.0) * w
        combined = contrib if combined is None else combined.add(contrib, fill_value=0.0)
    assert combined is not None
    return combined.rename("stack")


def summarize(series: pd.Series) -> dict:
    """因子序列摘要统计 (JSON 友好, NaN -> None)。"""
    valid = series.dropna()

    def _f(x) -> float | None:
        return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)

    last = [
        _f(v) for v in series.tail(5).tolist()
    ]
    return {
        "count": int(series.shape[0]),
        "valid_count": int(valid.shape[0]),
        "nan_ratio": _f(1 - valid.shape[0] / series.shape[0]) if series.shape[0] else None,
        "mean": _f(valid.mean()) if not valid.empty else None,
        "std": _f(valid.std()) if not valid.empty else None,
        "min": _f(valid.min()) if not valid.empty else None,
        "max": _f(valid.max()) if not valid.empty else None,
        "last": last,
    }


def sample_price_frame(n: int = 252, seed: int = 42, start: float = 100.0) -> pd.DataFrame:
    """确定性样本行情 (随机游走), 用于预览/测试。真数据见 Sprint 4。"""
    rng = np.random.default_rng(seed)
    rets = rng.normal(loc=0.0005, scale=0.02, size=n)
    close = start * np.cumprod(1.0 + rets)
    index = pd.date_range("2024-01-01", periods=n, freq="B")
    volume = rng.integers(1_000, 10_000, size=n)
    return pd.DataFrame({"close": close, "volume": volume}, index=index)
