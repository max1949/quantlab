"""沙箱执行器 — 在受限命名空间内运行已通过 AST 校验的用户因子。"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pandas as pd

from sandbox.ast_guard import validate_source

DEFAULT_TIMEOUT_SEC = 15.0
MAX_OUTPUT_ROWS = 2_000_000


class SandboxError(ValueError):
    pass


_SAFE_BUILTINS: dict[str, Any] = {
    "True": True,
    "False": False,
    "None": None,
    "int": int,
    "float": float,
    "bool": bool,
    "len": len,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "sum": sum,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
}


def _call_with_timeout(fn, arg, timeout_sec: float):
    box: dict[str, Any] = {}
    err: list[BaseException] = []

    def target() -> None:
        try:
            box["result"] = fn(arg)
        except BaseException as exc:  # noqa: BLE001
            err.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)
    if thread.is_alive():
        raise SandboxError(f"执行超时 (>{timeout_sec}s)")
    if err:
        raise SandboxError(f"计算失败: {err[0]}")
    if "result" not in box:
        raise SandboxError("compute 未返回结果")
    return box["result"]


def run_user_factor(
    source: str,
    ohlcv: pd.DataFrame,
    *,
    timeout_sec: float | None = None,
) -> pd.Series:
    """执行用户代码中的 compute(ohlcv), 返回因子 Series。"""
    from backend.app.core.config import get_settings

    if timeout_sec is None:
        timeout_sec = get_settings().sandbox_timeout_sec
    ok, errors = validate_source(source)
    if not ok:
        raise SandboxError("; ".join(errors))

    if ohlcv is None or ohlcv.empty:
        raise SandboxError("行情为空")

    ns: dict[str, Any] = {
        "pd": pd,
        "np": np,
    }
    exec(  # noqa: S102 — 已通过 AST 白名单; 仅注入 pd/np
        compile(source.strip(), "<user_factor>", "exec"),
        {"__builtins__": _SAFE_BUILTINS},
        ns,
    )
    compute_fn = ns.get("compute")
    if not callable(compute_fn):
        raise SandboxError("必须定义 compute(ohlcv) 函数")

    result = _call_with_timeout(compute_fn, ohlcv.copy(), timeout_sec)

    if isinstance(result, pd.DataFrame):
        if result.shape[1] != 1:
            raise SandboxError("返回 DataFrame 必须只有一列")
        series = result.iloc[:, 0]
    elif isinstance(result, pd.Series):
        series = result
    elif isinstance(result, (np.ndarray, list, tuple)):
        series = pd.Series(result, index=ohlcv.index[: len(result)])
    else:
        raise SandboxError("compute 必须返回 pandas Series (或单列 DataFrame)")

    if len(series) > MAX_OUTPUT_ROWS:
        raise SandboxError("输出过长")

    series = pd.Series(series, index=ohlcv.index).replace([np.inf, -np.inf], np.nan)
    if series.isna().all():
        raise SandboxError("因子结果全为空")
    return series.astype(float)
