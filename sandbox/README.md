# sandbox — 用户 Python 因子隔离执行层

> V1 **已开放** Python 因子 (AST 白名单 + 进程内超时沙箱)。
> Docker 容器隔离 (`Dockerfile`) 为增强层, 可按需启用。

## 纵深防御(三层,缺一不可)

1. **AST 静态校验**(`ast_guard.py`):白名单制,禁止 `import`、`__import__`、`open`、`eval`、`exec`、`getattr` 等危险节点。
2. **运行时隔离**(独立容器 `Dockerfile`):`--network none`、只读根文件系统、非 root、`seccomp` 限制系统调用、cgroup 限 CPU/内存。
3. **资源熔断**(`runner.py`):执行硬超时、内存上限、输出大小限制。

只向用户代码注入 `pandas` / `numpy` 和**只读行情 DataFrame**,产出因子 `Series`。
