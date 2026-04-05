from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import yaml

from railforge.application.bootstrap import ensure_codex_project_files
from railforge.application.phase_context import build_phase_context, load_run_state
from railforge.application.runtime_services import build_services, prepare_resume_services
from railforge.artifacts.store import ArtifactStore
from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import TaskItem, WorkspaceLayout
from railforge.infra.checkpoint_store import FileCheckpointStore
from railforge.infra.langgraph_bridge import LangGraphBridge
from railforge.infra.runtime_recovery import RuntimeRecovery
from railforge.openspec_bridge import OpenSpecBridge
from railforge.orchestrator.run_loop import RailForgeHarness
from railforge.planner.change_renderer import render_design, render_proposal, render_spec, render_tasks
from railforge.planner.contract_builder import build_contract
from railforge.planner.planning_contract import contract_approval_required, draft_planning_contract, load_planning_contract
from railforge.workflow.assets import WorkflowAssetResolver


class WorkflowCommandService:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.layout = WorkspaceLayout(workspace)
        self.store = ArtifactStore(self.layout)
        self.assets = WorkflowAssetResolver()

    def spec_research(self, args: Any) -> str:
        ensure_codex_project_files(self.workspace)
        services = build_services(args.profile, args.scenario, self.workspace)
        harness = RailForgeHarness(workspace=self.workspace, services=services)
        project = args.project or self.workspace.name
        result = harness.run(project=project, request_text=args.request)
        bridge = OpenSpecBridge(self.workspace)
        questions = self._load_questions()
        bridge.write_proposal(
            project,
            render_proposal(
                change_id=project,
                request_text=args.request,
                spec=self._load_product_spec(),
                questions=questions.get("unresolved") or questions.get("questions", []),
                decisions=self._load_decisions().get("decisions", []),
                result_state=result.state.value,
            ),
        )
        build_phase_context(
            self.workspace,
            phase="spec-research",
            run_meta=result.to_dict(),
            extra={"project": project, "request_text": args.request},
        )
        return result.state.value

    def spec_init(self, _args: Any) -> dict[str, Any]:
        self.store.init_workspace()
        ensure_codex_project_files(self.workspace)
        openspec_root = self.workspace / "openspec"
        (openspec_root / "changes").mkdir(parents=True, exist_ok=True)
        (openspec_root / "specs").mkdir(parents=True, exist_ok=True)
        build_phase_context(self.workspace, phase="spec-init")
        return {
            "workspace": str(self.workspace),
            "openspec": str(openspec_root),
            "runtime": str(self.layout.runtime),
            "codex": str(self.layout.codex_dir),
            "status": "READY",
        }

    def answer(self, args: Any) -> str:
        self.store.init_workspace()
        payload = yaml.safe_load(Path(args.file).read_text(encoding="utf-8")) or {}
        try:
            current = self.store.load_answers()
        except ArtifactNotFoundError:
            current = {"answers": {}}
        current_answers = dict(current.get("answers", {}))
        current_answers.update(payload.get("answers", {}))
        self.store.save_answers({"answers": current_answers})
        return "ANSWERS_CAPTURED"

    def approve(self, args: Any) -> str:
        self.store.init_workspace()
        self.store.save_approval(
            target=args.target,
            approved_by=args.approved_by or "human",
            note=args.note or "",
            task_id=args.task_id or "",
        )
        return "APPROVED"

    def status(self) -> dict[str, Any]:
        recovery = RuntimeRecovery(
            layout=self.layout,
            store=self.store,
            checkpoints=FileCheckpointStore(self.layout),
            langgraph=LangGraphBridge(self.layout),
        )
        snapshot = recovery.recover()
        if snapshot.run_meta is None:
            return load_run_state(self.workspace)
        payload = snapshot.run_meta.to_dict()
        payload["checkpoint_consistent"] = snapshot.checkpoint_consistent
        payload["issues"] = snapshot.issues
        return payload

    def resume(self, args: Any) -> str:
        services = prepare_resume_services(args, self.workspace, allow_recovery=True)
        harness = RailForgeHarness(workspace=self.workspace, services=services)
        build_phase_context(
            self.workspace,
            phase="resume",
            run_meta=load_run_state(self.workspace),
            extra={"reason": args.reason, "note": args.note},
        )
        result = harness.resume(reason=args.reason, note=args.note)
        return result.state.value

    def spec_plan(self, args: Any) -> str:
        ensure_codex_project_files(self.workspace)
        if self._has_unresolved_questions() or not self.store.has_approval("spec"):
            return "BLOCKED"
        try:
            spec = self.store.load_product_spec()
        except ArtifactNotFoundError:
            return "BLOCKED"
        services = prepare_resume_services(args, self.workspace)
        harness = RailForgeHarness(workspace=self.workspace, services=services)
        build_phase_context(
            self.workspace,
            phase="spec-plan",
            run_meta=load_run_state(self.workspace),
            extra={"reason": args.reason, "note": args.note},
        )
        result = harness.resume(
            reason=args.reason or "spec_plan",
            note=args.note or "continue to backlog planning",
        )
        if result.blocked_reason in {"clarification_required", "spec_approval_required"}:
            return result.state.value
        run_state = self.store.load_run_state()
        project = run_state.project_name or self.workspace.name
        questions = self._load_questions()
        decisions = self._load_decisions()
        backlog = self.store.load_backlog(draft=not self.layout.backlog_path.exists())
        tasks = [TaskItem.from_dict(item) for item in backlog.get("items", [])]
        planning_contract = load_planning_contract(self.workspace)
        for task in tasks:
            self.store.save_contract(
                build_contract(
                    task,
                    planning_contract=planning_contract if planning_contract and planning_contract.is_ready else None,
                    run_id=run_state.run_id,
                )
            )
        if planning_contract is None or not planning_contract.is_ready:
            self.store.write_yaml(
                self.layout.planning_contract_path,
                draft_planning_contract(
                    workspace=self.workspace,
                    project=project,
                    tasks=tasks,
                    decisions=decisions.get("decisions", []),
                    template=self.assets.load_planning_contract_template(),
                ),
            )
        bridge = OpenSpecBridge(self.workspace)
        bridge.write_design(project, render_design(spec, tasks, decisions.get("decisions", [])))
        bridge.write_tasks(project, render_tasks(tasks))
        bridge.write_spec(
            project,
            "harness-core",
            render_spec(spec, tasks, questions.get("unresolved", []), decisions.get("decisions", [])),
        )
        return result.state.value

    def execute(self, args: Any) -> str:
        if not self.store.has_approval("backlog"):
            return "BLOCKED"
        if contract_approval_required(
            self.workspace,
            backlog_approved=True,
            contract_approved=self.store.has_approval("contract"),
        ):
            return "BLOCKED"
        services = prepare_resume_services(args, self.workspace)
        harness = RailForgeHarness(workspace=self.workspace, services=services)
        build_phase_context(
            self.workspace,
            phase="spec-impl",
            run_meta=load_run_state(self.workspace),
            extra={"reason": args.reason, "note": args.note},
        )
        result = harness.resume(
            reason=args.reason or "execute",
            note=args.note or "continue execution",
        )
        return result.state.value

    def prepare_execution(self, args: Any) -> dict[str, Any]:
        if not self.store.has_approval("backlog"):
            return {"state": "BLOCKED", "reason": "backlog_approval_required"}
        if contract_approval_required(
            self.workspace,
            backlog_approved=True,
            contract_approved=self.store.has_approval("contract"),
        ):
            return {"state": "BLOCKED", "reason": "contract_approval_required"}
        services = prepare_resume_services(args, self.workspace)
        harness = RailForgeHarness(workspace=self.workspace, services=services)
        payload = harness.prepare_execution_payload(
            reason=args.reason or "prepare_execution",
            note=args.note or "prepare hosted codex execution",
        )
        payload["context_pack"] = build_phase_context(
            self.workspace,
            phase="spec-impl",
            run_meta=load_run_state(self.workspace),
            task_id=payload.get("task_id"),
            extra={"reason": args.reason, "note": args.note},
        )
        payload["context_pack_path"] = str(self.layout.context_pack_path("spec-impl"))
        return payload

    def record_execution(self, args: Any) -> str:
        payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
        services = prepare_resume_services(args, self.workspace)
        harness = RailForgeHarness(workspace=self.workspace, services=services)
        result = harness.record_execution_result(payload)
        return result.state.value

    def review(self) -> dict[str, Any]:
        payload = load_run_state(self.workspace)
        task_id = payload.get("current_task_id")
        if task_id:
            try:
                return self.store.load_qa_report(task_id).to_dict()
            except ArtifactNotFoundError:
                pass
        return payload

    def spec_review(self, args: Any) -> dict[str, Any]:
        services = prepare_resume_services(args, self.workspace, allow_recovery=True)
        harness = RailForgeHarness(workspace=self.workspace, services=services)
        build_phase_context(
            self.workspace,
            phase="spec-review",
            run_meta=load_run_state(self.workspace),
        )
        return harness.run_spec_review()

    def _load_product_spec(self) -> dict[str, Any]:
        try:
            return self.store.load_product_spec()
        except ArtifactNotFoundError:
            return self.store.load_product_spec(draft=True)

    def _load_questions(self) -> dict[str, Any]:
        try:
            return self.store.load_questions()
        except ArtifactNotFoundError:
            return {"questions": [], "unresolved": []}

    def _load_decisions(self) -> dict[str, Any]:
        try:
            return self.store.load_decisions()
        except ArtifactNotFoundError:
            return {"decisions": []}

    def _has_unresolved_questions(self) -> bool:
        return bool(self._load_questions().get("unresolved", []))


def create_workflow_command_service(workspace: Path) -> WorkflowCommandService:
    return WorkflowCommandService(workspace)
