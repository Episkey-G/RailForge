import subprocess
import sys
from pathlib import Path


def test_python_module_entry_runs_to_done(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "run",
            "--workspace",
            str(tmp_path / "workspace"),
            "--project",
            "todo-app",
            "--request",
            "用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip().endswith("DONE")
