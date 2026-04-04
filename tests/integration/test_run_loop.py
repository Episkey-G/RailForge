from pathlib import Path

from railforge.adapters.mock import build_default_mock_services, build_repeated_failure_services
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import WorkspaceLayout
from railforge.orchestrator.run_loop import RailForgeHarness


def test_run_loop_completes_default_scenario(tmp_path: Path) -> None:
    harness = RailForgeHarness(
        workspace=tmp_path,
        services=build_default_mock_services(),
    )

    result = harness.run(project="todo-app", request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。")

    assert result.state == RunState.DONE
    assert len(result.commit_log) == 3
    store = ArtifactStore(WorkspaceLayout(tmp_path))
    backlog = store.load_backlog()
    assert all(item["status"] == "done" for item in backlog["items"])


def test_run_loop_blocks_then_resume_completes(tmp_path: Path) -> None:
    services = build_repeated_failure_services()
    harness = RailForgeHarness(workspace=tmp_path, services=services)

    blocked = harness.run(project="todo-app", request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。")

    assert blocked.state == RunState.BLOCKED

    services.allow_recovery()
    resumed = harness.resume(reason="manual_override", note="人工确认后继续")

    assert resumed.state == RunState.DONE
