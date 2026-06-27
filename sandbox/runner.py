"""沙箱执行器 (契约占位, 后置 Sprint 实现)。

在受限环境内执行已通过 AST 校验的用户因子代码:
仅注入 pandas/numpy 与只读行情, 施加超时 / 内存 / 输出限制, 返回因子 Series。
"""

# def run_user_factor(source: str, ohlcv) -> "pd.Series": ...
