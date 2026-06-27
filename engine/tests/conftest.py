"""确保仓库根在 sys.path 上, 使 `import engine...` 在任意 pytest 调用方式下可用
(无论 rootdir 是 backend 还是 engine/tests)。"""

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
