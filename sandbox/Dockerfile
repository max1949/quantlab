# 沙箱执行镜像 (与主后端物理隔离)。
# 运行时务必配合: --network none / 只读根文件系统 / 非 root / seccomp / cgroup 资源限制。
FROM python:3.12-slim

RUN useradd -m -u 10001 sandbox
WORKDIR /sandbox

RUN pip install --no-cache-dir pandas==2.2.3 numpy==2.2.1

COPY . /sandbox
USER sandbox

# 实际入口在 Sprint 落地; 骨架阶段仅声明镜像。
CMD ["python", "-c", "print('quantlab sandbox image ready')"]
