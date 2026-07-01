"""公式因子引擎 (Sprint 10, L2)。

让用户用一行表达式定义因子, 例如:
    (close - sma(close, 20)) / std(close, 20)
    rsi(close, 14) - 50
    mom(close, 20) * -1

安全性是核心: **绝不 eval 用户输入**。这里用 ast 解析成语法树, 只放行白名单内的
节点 / 变量 / 函数, 其余一律拒绝。函数全部作用在 pandas.Series 上 (向量化),
窗口参数必须是常量整数。
"""

from __future__ import annotations

import ast

import numpy as np
import pandas as pd

# 允许引用的行情列 (变量名)
ALLOWED_VARS = ("open", "high", "low", "close", "volume", "open_interest")


class FormulaError(ValueError):
    """公式非法 (语法/非白名单/计算错误)。"""


# --- 白名单函数 (全部 Series -> Series) ---
def _as_window(n) -> int:
    try:
        w = int(n)
    except (TypeError, ValueError):
        raise FormulaError("窗口参数必须是整数")
    if w < 1 or w > 500:
        raise FormulaError("窗口参数需在 1..500 之间")
    return w


def _sma(x, n):
    return pd.Series(x).rolling(_as_window(n)).mean()


def _ema(x, n):
    return pd.Series(x).ewm(span=_as_window(n), adjust=False).mean()


def _std(x, n):
    return pd.Series(x).rolling(_as_window(n)).std()


def _ret(x, n=1):
    return pd.Series(x).pct_change(_as_window(n))


def _delay(x, n):
    return pd.Series(x).shift(_as_window(n))


def _mom(x, n):
    s = pd.Series(x)
    return s / s.shift(_as_window(n)) - 1.0


def _zscore(x, n):
    s = pd.Series(x)
    w = _as_window(n)
    m = s.rolling(w).mean()
    sd = s.rolling(w).std()
    return (s - m) / sd


def _rolling_max(x, n):
    return pd.Series(x).rolling(_as_window(n)).max()


def _rolling_min(x, n):
    return pd.Series(x).rolling(_as_window(n)).min()


def _rsi(x, n):
    s = pd.Series(x)
    delta = s.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    w = _as_window(n)
    roll_up = up.rolling(w).mean()
    roll_down = down.rolling(w).mean()
    rs = roll_up / roll_down.replace(0.0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def _corr(x, y, n):
    return pd.Series(x).rolling(_as_window(n)).corr(pd.Series(y))


def _abs(x):
    return pd.Series(x).abs()


def _log(x):
    return np.log(pd.Series(x))


def _sign(x):
    return np.sign(pd.Series(x))


FUNCS = {
    "sma": _sma,
    "ema": _ema,
    "std": _std,
    "ret": _ret,
    "delay": _delay,
    "ref": _delay,  # 别名
    "mom": _mom,
    "zscore": _zscore,
    "max": _rolling_max,
    "min": _rolling_min,
    "rsi": _rsi,
    "corr": _corr,
    "abs": _abs,
    "log": _log,
    "sign": _sign,
}

# 文档目录 (前端帮助面板)
FUNC_DOCS = [
    {"name": "sma(x, n)", "desc": "n 期简单移动平均"},
    {"name": "ema(x, n)", "desc": "n 期指数移动平均"},
    {"name": "std(x, n)", "desc": "n 期滚动标准差"},
    {"name": "ret(x, n)", "desc": "n 期收益率 (pct_change)"},
    {"name": "delay(x, n)", "desc": "前移 n 期 (历史值), 别名 ref"},
    {"name": "mom(x, n)", "desc": "n 期动量 x/delay(x,n)-1"},
    {"name": "zscore(x, n)", "desc": "n 期滚动 z 分数"},
    {"name": "max(x, n)", "desc": "n 期滚动最大值"},
    {"name": "min(x, n)", "desc": "n 期滚动最小值"},
    {"name": "rsi(x, n)", "desc": "n 期相对强弱指标 (0-100)"},
    {"name": "corr(x, y, n)", "desc": "x 与 y 的 n 期滚动相关系数"},
    {"name": "abs(x) / log(x) / sign(x)", "desc": "绝对值 / 自然对数 / 符号"},
]

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)


def validate(expr: str) -> set[str]:
    """静态校验表达式; 返回用到的变量名集合。非法即抛 FormulaError。"""
    expr = (expr or "").strip()
    if not expr:
        raise FormulaError("公式不能为空")
    if len(expr) > 500:
        raise FormulaError("公式过长 (上限 500 字符)")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"语法错误: {exc.msg}")

    used_vars: set[str] = set()

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, _ALLOWED_BINOPS):
                raise FormulaError("不支持的运算符")
            walk(node.left)
            walk(node.right)
            return
        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, _ALLOWED_UNARYOPS):
                raise FormulaError("不支持的一元运算符")
            walk(node.operand)
            return
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)) or isinstance(node.value, bool):
                raise FormulaError("只允许数字常量")
            return
        if isinstance(node, ast.Name):
            if node.id not in ALLOWED_VARS:
                raise FormulaError(
                    f"未知变量 '{node.id}', 只能用: {', '.join(ALLOWED_VARS)}"
                )
            used_vars.add(node.id)
            return
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCS:
                fname = getattr(node.func, "id", "?")
                raise FormulaError(f"未知函数 '{fname}'")
            if node.keywords:
                raise FormulaError("函数不支持关键字参数")
            for arg in node.args:
                walk(arg)
            return
        raise FormulaError("表达式包含不允许的语法")

    walk(tree)
    if not used_vars:
        raise FormulaError("公式必须引用至少一个行情变量 (如 close)")
    return used_vars


def compute(df: pd.DataFrame, expr: str) -> pd.Series:
    """在给定 OHLCV 上计算公式, 返回与 df 对齐的 Series。"""
    validate(expr)
    tree = ast.parse(expr.strip(), mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in df.columns:
                raise FormulaError(f"行情缺少列: {node.id}")
            return df[node.id].astype(float)
        if isinstance(node, ast.UnaryOp):
            v = ev(node.operand)
            return +v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            op = node.op
            if isinstance(op, ast.Add):
                return a + b
            if isinstance(op, ast.Sub):
                return a - b
            if isinstance(op, ast.Mult):
                return a * b
            if isinstance(op, ast.Div):
                return a / b
            if isinstance(op, ast.Pow):
                return a ** b
            if isinstance(op, ast.Mod):
                return a % b
        if isinstance(node, ast.Call):
            args = [ev(a) for a in node.args]
            try:
                return FUNCS[node.func.id](*args)
            except FormulaError:
                raise
            except TypeError as exc:
                raise FormulaError(f"函数 {node.func.id} 参数错误: {exc}")
        raise FormulaError("无法计算的表达式")

    try:
        result = ev(tree)
    except FormulaError:
        raise
    except Exception as exc:  # 计算期意外
        raise FormulaError(f"计算失败: {exc}")

    if np.isscalar(result):
        raise FormulaError("公式结果是常数, 不是随时间变化的因子")
    series = pd.Series(result, index=df.index).replace([np.inf, -np.inf], np.nan)
    return series
