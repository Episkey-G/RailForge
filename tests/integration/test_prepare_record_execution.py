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
