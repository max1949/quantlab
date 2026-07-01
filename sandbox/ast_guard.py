"""AST 白名单静态校验 — 用户 Python 因子代码安全网。"""

from __future__ import annotations

import ast

MAX_SOURCE_LEN = 8000
MAX_NODES = 600

BLOCKED_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
        "globals",
        "locals",
        "vars",
        "dir",
        "help",
        "input",
        "breakpoint",
        "memoryview",
        "bytearray",
        "bytes",
        "staticmethod",
        "classmethod",
        "super",
        "type",
        "object",
        "isinstance",
        "issubclass",
        "hasattr",
        "__builtins__",
        "print",
        "importlib",
        "os",
        "sys",
        "subprocess",
        "socket",
        "pickle",
        "marshal",
    }
)

BLOCKED_ATTRS = frozenset(
    {
        "__class__",
        "__bases__",
        "__subclasses__",
        "__mro__",
        "__globals__",
        "__code__",
        "__reduce__",
        "__reduce_ex__",
        "__getattribute__",
        "__dict__",
        "__loader__",
        "__spec__",
        "__init__",
    }
)

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv)
_ALLOWED_BOOLOPS = (ast.And, ast.Or)
_ALLOWED_CMPOPS = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub, ast.Not)


class SandboxValidationError(ValueError):
    pass


def validate_source(source: str) -> tuple[bool, list[str]]:
    """返回 (是否通过, 违规原因列表)。"""
    errors: list[str] = []
    src = (source or "").strip()
    if not src:
        return False, ["代码不能为空"]
    if len(src) > MAX_SOURCE_LEN:
        return False, [f"代码过长 (上限 {MAX_SOURCE_LEN} 字符)"]

    try:
        tree = ast.parse(src, mode="exec")
    except SyntaxError as exc:
        return False, [f"语法错误: {exc.msg}"]

    compute_fn: ast.FunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name != "compute":
                errors.append("只允许定义 compute(ohlcv) 函数")
                continue
            if compute_fn is not None:
                errors.append("不能定义多个 compute 函数")
            compute_fn = node
        elif isinstance(node, (ast.Expr, ast.Pass)):
            continue
        else:
            errors.append(f"模块顶层不允许: {type(node).__name__}")

    if compute_fn is None:
        errors.append("必须定义 def compute(ohlcv): ...")
    elif len(compute_fn.args.args) != 1 or compute_fn.args.args[0].arg != "ohlcv":
        errors.append("compute 必须且只能有一个参数 ohlcv")
    elif compute_fn.args.defaults or compute_fn.args.kwonlyargs or compute_fn.args.vararg or compute_fn.args.kwarg:
        errors.append("compute 不支持默认参数 / *args / **kwargs")

    node_count = 0

    def reject(msg: str) -> None:
        errors.append(msg)

    def walk(node: ast.AST, *, in_lambda: bool = False) -> None:
        nonlocal node_count
        node_count += 1
        if node_count > MAX_NODES:
            raise SandboxValidationError("代码过于复杂")

        if isinstance(node, ast.Module):
            for child in node.body:
                walk(child)
            return

        if isinstance(node, ast.FunctionDef):
            if node.name != "compute":
                reject(f"不允许嵌套函数 {node.name}")
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    reject("compute 内不允许再定义函数或类")
                    break
            for stmt in node.body:
                walk(stmt)
            return

        blocked_stmt = (
            ast.Import,
            ast.ImportFrom,
            ast.Global,
            ast.Nonlocal,
            ast.ClassDef,
            ast.AsyncFunctionDef,
            ast.With,
            ast.AsyncWith,
            ast.Try,
            ast.Raise,
            ast.Delete,
        )
        if isinstance(node, blocked_stmt):
            reject(f"不允许的语句: {type(node).__name__}")
            return

        if isinstance(node, ast.Lambda):
            if in_lambda:
                reject("不支持的 lambda 嵌套")
            for child in ast.walk(node):
                if child is node:
                    continue
                walk(child, in_lambda=True)
            return

        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in BLOCKED_NAMES:
                reject(f"禁止调用: {fn.id}")
            if isinstance(fn, ast.Attribute) and fn.attr in BLOCKED_NAMES:
                reject(f"禁止调用: {fn.attr}")
            for arg in node.args:
                walk(arg, in_lambda=in_lambda)
            for kw in node.keywords:
                walk(kw.value, in_lambda=in_lambda)
            return

        if isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_ATTRS:
                reject(f"禁止访问属性: {node.attr}")
            walk(node.value, in_lambda=in_lambda)
            return

        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            reject(f"禁止使用名称: {node.id}")
            return

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) or node.value is None:
                return
            if isinstance(node.value, str) and len(node.value) <= 64:
                return
            reject("不允许的常量类型")
            return

        for child in ast.iter_child_nodes(node):
            walk(child, in_lambda=in_lambda)

    try:
        walk(tree)
    except SandboxValidationError as exc:
        errors.append(str(exc))

    return (len(errors) == 0, errors)
