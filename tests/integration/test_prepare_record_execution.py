import json
import subprocess
import sys
from pathlib import Path

from railforge.adapters.base import HarnessServices
from railforge.adapters.hosted_codex_adapter import HostedCodexAdapter
from railforge.adapters.mock import MockSpecialistAdapter
from railforge.adapters.git import DryRunGitAdapter
from railforge.adapters.playwright import NoopPlaywrightAdapter
from railforge.adapters.shell import LocalShellAdapter
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import WorkspaceLayout
from railforge.orchestrator.run_loop import RailForgeHarness


def _hosted_services() -> HarnessServices:
    backend = MockSpecialistAdapter("Backend")
    frontend = MockSpecialistAdapter("Frontend")
    return HarnessServices(
        lead_writer=HostedCodexAdapter(),
        backend_specialist=backend,
        frontend_specialist=frontend,
        git=DryRunGitAdapter(),
        shell=LocalShellAdapter(),
        playwright=NoopPlaywrightAdapter(),
        backend_evaluator=backend,
        frontend_evaluator=frontend,
    )


def _bootstrap_hosted_run(tmp_path: Path, request_text: str) -> tuple[RailForgeHarness, ArtifactStore]:
    workspace = tmp_path / "workspace"
    services = _hosted_services()
    harness = RailForgeHarness(workspace=workspace, services=services)
    store = ArtifactStore(WorkspaceLayout(workspace))

    first = harness.run(project="workspace", request_text=request_text)
    assert first.blocked_reason == "spec_approval_required"

    store.save_approval("spec", approved_by="human", note="spec ok")
    second = harness.resume(reason="spec_approved", note="continue")
    assert second.blocked_reason == "backlog_approval_required"

    store.save_approval("backlog", approved_by="human", note="backlog ok")
    return harness, store


def test_prepare_execution_outputs_hosted_context(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "spec-research",
            "--profile",
            "real",
            "--workspace",
            str(workspace),
            "--request",
            "最小 hosted smoke",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "approve", "--workspace", str(workspace), "--target", "spec"],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "spec-plan", "--profile", "real", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "approve", "--workspace", str(workspace), "--target", "backlog"],
        capture_output=True,
        text=True,
        check=False,
    )

    result = subprocess.run(
        [sys.executable, "-m", "railforge", "prepare-execution", "--profile", "real", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "hosted_codex"
    assert "prompt" in payload
    assert "allowed_paths" in payload


def test_prepare_execution_includes_contract_context_and_writeback(tmp_path: Path) -> None:
    harness, store = _bootstrap_hosted_run(
        tmp_path,
        "后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
    )

    payload = harness.prepare_execution_payload(reason="prepare_execution", note="prepare")
    workspace = store.layout.root

    assert payload["task_id"] == "T-001"
    assert payload["task_context"]
    assert payload["writeback"]["required_fields"] == [
        "task_id",
        "summary",
        "changed_files",
        "verification_notes",
    ]
    assert payload["roles"]["lead_writer"]["read_only"] is False
    assert payload["roles"]["backend_specialist"]["read_only"] is True
    assert payload["roles"]["frontend_specialist"]["read_only"] is True

    trace = json.loads(
        (workspace / ".railforge" / "execution" / "tasks" / "T-001" / "traces" / "hosted_execution_request.json").read_text(
            encoding="utf-8"
        )
    )
    assert trace["task_id"] == "T-001"
    assert trace["writeback"]["result_path"] == ".railforge/runtime/hosted_execution_result.json"


def test_record_execution_advances_to_static_review_or_beyond(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    services = _hosted_services()
    harness = RailForgeHarness(workspace=workspace, services=services)
    store = ArtifactStore(WorkspaceLayout(workspace))

    first = harness.run(project="workspace", request_text="最小 hosted smoke")
    assert first.blocked_reason == "spec_approval_required"

    store.save_approval("spec", approved_by="human", note="spec ok")
    second = harness.resume(reason="spec_approved", note="continue")
    assert second.blocked_reason == "backlog_approval_required"

    store.save_approval("backlog", approved_by="human", note="backlog ok")
    payload = harness.prepare_execution_payload(reason="prepare_execution", note="prepare")
    assert payload["mode"] == "hosted_codex"

    result = harness.record_execution_result(
        {
            "task_id": "T-001",
            "summary": "hosted codex done",
            "changed_files": ["backend/todos.py"],
        }
    )

    assert result.state in {
        RunState.STATIC_REVIEW,
        RunState.RUNTIME_QA,
        RunState.READY_TO_COMMIT,
        RunState.REPAIRING,
        RunState.DONE,
        RunState.BLOCKED,
    }
    if result.state == RunState.BLOCKED:
        assert result.blocked_reason == "hosted_execution_required"


def test_record_execution_persists_specialist_traces_and_finishes_single_task(tmp_path: Path) -> None:
    harness, store = _bootstrap_hosted_run(tmp_path, "后端接口必须拒绝过去日期。")
    payload = harness.prepare_execution_payload(reason="prepare_execution", note="prepare")

    assert payload["task_id"] == "T-001"

    result = harness.record_execution_result(
        {
            "task_id": "T-001",
            "summary": "hosted codex done",
            "changed_files": ["backend/todos.py", "tests/test_backend_flow.py"],
            "verification_notes": ["pytest tests/test_backend_flow.py"],
        }
    )

    workspace = store.layout.root
    backend_trace = json.loads(
        (workspace / ".railforge" / "execution" / "tasks" / "T-001" / "traces" / "backend_specialist.json").read_text(
            encoding="utf-8"
        )
    )
    frontend_trace = json.loads(
        (workspace / ".railforge" / "execution" / "tasks" / "T-001" / "traces" / "frontend_specialist.json").read_text(
            encoding="utf-8"
        )
    )
    execution_trace = json.loads(
        (workspace / ".railforge" / "execution" / "tasks" / "T-001" / "traces" / "hosted_execution_result.json").read_text(
            encoding="utf-8"
        )
    )

    assert backend_trace["read_only"] is True
    assert frontend_trace["read_only"] is True
    assert backend_trace["allowed_write_paths"] == [
        ".railforge/execution/tasks/T-001/reviews/",
        ".railforge/execution/tasks/T-001/proposals/",
    ]
    assert frontend_trace["boundary_violations"] == []
    assert execution_trace["verification_notes"] == ["pytest tests/test_backend_flow.py"]
    assert result.state == RunState.DONE
    assert store.load_run_state().current_task_id is None
    assert store.load_task("T-001").status == "done"


def test_record_execution_advances_to_next_task_after_commit_gate(tmp_path: Path) -> None:
    harness, store = _bootstrap_hosted_run(
        tmp_path,
        "后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
    )
    payload = harness.prepare_execution_payload(reason="prepare_execution", note="prepare")

    assert payload["task_id"] == "T-001"

    result = harness.record_execution_result(
        {
            "task_id": "T-001",
            "summary": "hosted codex done",
            "changed_files": ["backend/todos.py", "tests/test_backend_flow.py"],
            "verification_notes": ["pytest tests/test_backend_flow.py"],
        }
    )

    workspace = store.layout.root
    next_request = json.loads((workspace / ".railforge" / "runtime" / "hosted_execution_request.json").read_text(encoding="utf-8"))
    backlog = store.load_backlog()

    assert result.state == RunState.BLOCKED
    assert result.blocked_reason == "hosted_execution_required"
    assert next_request["task_id"] == "T-002"
    assert next_request["roles"]["frontend_specialist"]["read_only"] is True
    assert backlog["current_task"] == "T-002"
    assert store.load_task("T-001").status == "done"


def test_record_execution_recovers_current_task_from_backlog(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    services = _hosted_services()
    harness = RailForgeHarness(workspace=workspace, services=services)
    store = ArtifactStore(WorkspaceLayout(workspace))

    first = harness.run(project="workspace", request_text="最小 hosted smoke")
    assert first.blocked_reason == "spec_approval_required"

    store.save_approval("spec", approved_by="human", note="spec ok")
    second = harness.resume(reason="spec_approved", note="continue")
    assert second.blocked_reason == "backlog_approval_required"

    store.save_approval("backlog", approved_by="human", note="backlog ok")
    harness.prepare_execution_payload(reason="prepare_execution", note="prepare")

    run_state = store.load_run_state()
    run_state.current_task_id = None
    store.save_run_state(run_state)

    result = harness.record_execution_result(
        {
            "task_id": "T-001",
            "summary": "hosted codex done",
            "changed_files": ["backend/todos.py"],
        }
    )

    assert result.state in {
        RunState.STATIC_REVIEW,
        RunState.RUNTIME_QA,
        RunState.READY_TO_COMMIT,
        RunState.REPAIRING,
        RunState.DONE,
        RunState.BLOCKED,
    }
