from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import RunMeta, TaskItem, WorkspaceLayout
from railforge.infra.checkpoint_store import FileCheckpointStore
from railforge.infra.langgraph_bridge import LangGraphBridge


TASK_REQUIRED_STATES = {
    RunState.CONTRACT_NEGOTIATION,
    RunState.IMPLEMENTING,
    RunState.STATIC_REVIEW,
    RunState.RUNTIME_QA,
    RunState.REPAIRING,
    RunState.READY_TO_COMMIT,
    RunState.COMMITTED,
}


@dataclass
class RecoverySnapshot:
    run_meta: Optional[RunMeta]
    backlog: Dict[str, Any]
    current_task: Optional[TaskItem]
    langgraph: Dict[str, Any] = field(default_factory=dict)
    git: Dict[str, Any] = field(default_factory=dict)
    checkpoint_consistent: bool = True
    issues: List[str] = field(default_factory=list)
    failure_reason: Optional[str] = None


class RuntimeRecovery:
    def __init__(
        self,
        layout: WorkspaceLayout,
        store: ArtifactStore,
        checkpoints: FileCheckpointStore,
        langgraph: LangGraphBridge,
        git_adapter: Any = None,
    ) -> None:
        self.layout = layout
        self.store = store
        self.checkpoints = checkpoints
        self.langgraph = langgraph
        self.git_adapter = git_adapter

    def inspect_git_state(self) -> Dict[str, Any]:
        if self.git_adapter is not None and hasattr(self.git_adapter, "inspect_workspace"):
            return self.git_adapter.inspect_workspace(self.layout.root)

        git_dir = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(self.layout.root),
            capture_output=True,
            text=True,
        )
        if git_dir.returncode != 0:
            return {
                "available": False,
                "dirty": False,
                "head": None,
                "branch": None,
                "status": [],
                "reason": "not_a_git_repo",
            }

        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.layout.root),
            capture_output=True,
            text=True,
        )
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(self.layout.root),
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(self.layout.root),
            capture_output=True,
            text=True,
        )
        lines = [line for line in status.stdout.splitlines() if line.strip()]
        return {
            "available": True,
            "dirty": bool(lines),
            "head": head.stdout.strip() or None,
            "branch": branch.stdout.strip() or None,
            "status": lines,
        }

    def recover(self) -> RecoverySnapshot:
        git_state = self.inspect_git_state()
        try:
            run_meta = self.store.load_run_state()
        except ArtifactNotFoundError:
            return RecoverySnapshot(
                run_meta=None,
                backlog={"items": []},
                current_task=None,
                git=git_state,
                checkpoint_consistent=False,
                issues=["run_state_missing"],
                failure_reason="run_state_missing",
            )

        backlog = self._load_active_backlog()
        issues: List[str] = []
        current_task_id = run_meta.current_task_id or backlog.get("current_task")
        if current_task_id and current_task_id != run_meta.current_task_id:
            issues.append("current_task_rehydrated")

        if not current_task_id:
            in_progress = [item for item in backlog.get("items", []) if item.get("status") == "in_progress"]
            if len(in_progress) == 1:
                current_task_id = in_progress[0]["id"]
                issues.append("current_task_rehydrated")

        current_task = self._load_current_task(current_task_id, backlog)
        if current_task is not None:
            run_meta.current_task_id = current_task.id

        checkpoint = self.checkpoints.load_latest_or_none()
        checkpoint_consistent = True
        langgraph_ref: Dict[str, Any] = {}
        if checkpoint is not None:
            checkpoint_state = checkpoint.get("run_state", {})
            checkpoint_task = (checkpoint.get("current_task") or {}).get("id")
            checkpoint_consistent = (
                checkpoint_state.get("run_id") == run_meta.run_id
                and checkpoint_state.get("state") == run_meta.state.value
                and checkpoint_task == run_meta.current_task_id
            )
            if checkpoint_consistent:
                langgraph_ref = dict(checkpoint.get("langgraph", {}))
            else:
                issues.append("checkpoint_mismatch")

        if not langgraph_ref and checkpoint_consistent:
            langgraph_ref = self.langgraph.load_latest(run_meta.run_id)

        if checkpoint_consistent:
            run_meta.thread_id = langgraph_ref.get("thread_id") or run_meta.thread_id
            run_meta.checkpoint_ref = langgraph_ref.get("checkpoint_ref") or run_meta.checkpoint_ref
        else:
            run_meta.checkpoint_ref = None

        failure_reason = self._failure_reason(run_meta, current_task)
        if failure_reason:
            run_meta.state = RunState.FAILED
            run_meta.blocked_reason = "recovery_failed"
            run_meta.resume_from_state = None
            run_meta.checkpoint_ref = None
            issues.append(failure_reason)

        return RecoverySnapshot(
            run_meta=run_meta,
            backlog=backlog,
            current_task=current_task,
            langgraph=langgraph_ref,
            git=git_state,
            checkpoint_consistent=checkpoint_consistent,
            issues=issues,
            failure_reason=failure_reason,
        )

    def _load_active_backlog(self) -> Dict[str, Any]:
        if self.layout.backlog_path.exists():
            return self.store.load_backlog()
        if self.layout.backlog_draft_path.exists():
            return self.store.load_backlog(draft=True)
        return {"items": []}

    def _load_current_task(self, task_id: Optional[str], backlog: Dict[str, Any]) -> Optional[TaskItem]:
        if not task_id:
            return None
        try:
            return self.store.load_task(task_id)
        except ArtifactNotFoundError:
            for item in backlog.get("items", []):
                if item.get("id") == task_id:
                    task = TaskItem.from_dict(item)
                    self.store.save_task(task)
                    return task
        return None

    def _failure_reason(self, run_meta: RunMeta, current_task: Optional[TaskItem]) -> Optional[str]:
        if run_meta.state == RunState.BLOCKED and not run_meta.resume_from_state:
            return "blocked_without_resume"
        if run_meta.state in TASK_REQUIRED_STATES and current_task is None:
            return "current_task_missing"
        if run_meta.state == RunState.BLOCKED and run_meta.resume_from_state in {
            RunState.CONTRACT_NEGOTIATION.value,
            RunState.IMPLEMENTING.value,
            RunState.STATIC_REVIEW.value,
            RunState.RUNTIME_QA.value,
            RunState.REPAIRING.value,
            RunState.READY_TO_COMMIT.value,
        } and current_task is None:
            return "current_task_missing"
        return None
