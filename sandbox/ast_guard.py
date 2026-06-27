"""AST 白名单静态校验 (契约占位, 后置 Sprint 实现)。

解析用户因子代码的语法树, 白名单制放行 (仅算术 + pandas/numpy 调用),
拒绝 import / __import__ / open / eval / exec / getattr 等危险节点。
"""

# def validate_source(source: str) -> tuple[bool, list[str]]:
#     """返回 (是否通过, 违规原因列表)。"""
