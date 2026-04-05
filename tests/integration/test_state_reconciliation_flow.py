import json
import subprocess
import sys
from pathlib import Path

from railforge.adapters.mock import build_default_mock_services
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import WorkspaceLayout
from railforge.orchestrator.run_loop import RailForgeHarness


def test_reconciliation_updates_block_reason_and_clears_interrupts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    harness = RailForgeHarness(workspace=workspace, services=build_default_mock_services())
    store = ArtifactStore(WorkspaceLayout(workspace))

    blocked = harness.run(
        project="todo-app",
        request_text="后端接口必须拒绝过去日期。前端错误提示文案、时区和最终业务口径需要人工确认。",
    )
    assert blocked.state == RunState.BLOCKED
    assert blocked.blocked_reason == "clarification_required"

    store.save_answers({"answers": {"Q-001": "按产品说明", "Q-002": "UTC", "Q-003": "日期不能早于今天"}})
    blocked = harness.resume(reason="clarification_resolved", note="answers captured")
    assert blocked.state == RunState.BLOCKED
    assert blocked.blocked_reason == "spec_approval_required"

    store.save_approval("spec", approved_by="human", note="spec ok")
    blocked = harness.resume(reason="spec_approved", note="continue")
    assert blocked.state == RunState.BLOCKED
    assert blocked.blocked_reason == "backlog_approval_required"

    run_id = store.load_run_state().run_id
    interrupt_path = workspace / ".railforge" / "runtime" / "notes" / run_id / "interrupts" / "blocked_interrupt.json"
    interrupt = json.loads(interrupt_path.read_text(encoding="utf-8"))
    assert interrupt["reason"] == "backlog_approval_required"

    store.save_approval("backlog", approved_by="human", note="backlog ok")
    store.save_approval("contract", approved_by="human", note="contract ok")
    done = harness.resume(reason="backlog_approved", note="continue")
    assert done.state == RunState.DONE
    assert not interrupt_path.exists()

    run_state_path = workspace / ".railforge" / "runtime" / "runs" / run_id / "run_state.json"
    stale = store.load_run_state().to_dict()
    stale["state"] = "BLOCKED"
    stale["blocked_reason"] = "clarification_required"
    stale["resume_from_state"] = "SPEC_EXPANSION"
    stale["checkpoint_index"] = 0
    run_state_path.write_text(json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")

    status = subprocess.run(
        [sys.executable, "-m", "railforge", "status", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(status.stdout)

    assert status.returncode == 0
    assert payload["state"] == "DONE"
    assert payload["blocked_reason"] is None
    assert "run_state_reconciled_from_checkpoint" in payload["issues"]
