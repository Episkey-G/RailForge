from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import yaml

from railforge.adapters.mock import build_default_mock_services, build_hosted_smoke_services, build_repeated_failure_services
from railforge.artifacts.store import ArtifactStore
from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import TaskItem, WorkspaceLayout
from railforge.openspec_bridge import OpenSpecBridge
from railforge.orchestrator.run_loop import RailForgeHarness
from railforge.planner.change_renderer import render_design, render_proposal, render_spec, render_tasks
from railforge.planner.contract_builder import build_contract
from railforge.planner.planning_contract import load_planning_contract
from railforge.infra.checkpoint_store import FileCheckpointStore
from railforge.infra.langgraph_bridge import LangGraphBridge
from railforge.infra.runtime_recovery import RuntimeRecovery


def build_services(profile: str, scenario: str, workspace: Path) -> Any:
    if scenario == "hosted-smoke":
        return build_hosted_smoke_services()
    if profile == "real":
        try:
            from railforge.adapters.base import HarnessServices
            from railforge.adapters.claude_cli_adapter import ClaudeCliSpecialistAdapter
            from railforge.adapters.codeagent_wrapper import CodeagentWrapper
            from railforge.adapters.codex_cli_adapter import CodexCliLeadWriterAdapter
            from railforge.adapters.gemini_cli_adapter import GeminiCliSpecialistAdapter
            from railforge.adapters.git import DryRunGitAdapter
            from railforge.adapters.hosted_codex_adapter import HostedCodexAdapter
            from railforge.adapters.playwright import NoopPlaywrightAdapter
            from railforge.adapters.role_router import RoleRouter, load_role_backends
            from railforge.adapters.shell import LocalShellAdapter
        except Exception:
            return build_default_mock_services()
        router = RoleRouter(role_backends=load_role_backends(workspace))
        wrapper = CodeagentWrapper(dry_run=False)
        return HarnessServices(
            lead_writer=HostedCodexAdapter(),
            backend_specialist=ClaudeCliSpecialistAdapter(role_name="backend_specialist", role_router=router, wrapper=wrapper),
            frontend_specialist=GeminiCliSpecialistAdapter(role_name="frontend_specialist", role_router=router, wrapper=wrapper),
            git=DryRunGitAdapter(),
            shell=LocalShellAdapter(),
            playwright=NoopPlaywrightAdapter(),
            backend_evaluator=ClaudeCliSpecialistAdapter(role_name="backend_evaluator", role_router=router, wrapper=wrapper),
            frontend_evaluator=GeminiCliSpecialistAdapter(role_name="frontend_evaluator", role_router=router, wrapper=wrapper),
        )
    if scenario == "repeated-failure":
        return build_repeated_failure_services()
    return build_default_mock_services()


def _load_run_state(workspace: Path) -> dict[str, Any]:
    store = ArtifactStore(WorkspaceLayout(workspace))
    try:
        return store.load_run_state().to_dict()
    except ArtifactNotFoundError:
        return {"state": "BOOTSTRAP", "workspace": str(workspace)}


def _prepare_resume_services(args, workspace: Path, allow_recovery: bool = False):
    services = build_services(args.profile, args.scenario, workspace)
    if allow_recovery and args.scenario == "repeated-failure" and hasattr(services, "allow_recovery"):
        services.allow_recovery()
    return services


def _load_product_spec(store: ArtifactStore):
    try:
        return store.load_product_spec()
    except ArtifactNotFoundError:
        return store.load_product_spec(draft=True)


def _load_questions(store: ArtifactStore) -> dict[str, Any]:
    try:
        return store.load_questions()
    except ArtifactNotFoundError:
        return {"questions": [], "unresolved": []}


def _load_decisions(store: ArtifactStore) -> dict[str, Any]:
    try:
        return store.load_decisions()
    except ArtifactNotFoundError:
        return {"decisions": []}


def _has_unresolved_questions(store: ArtifactStore) -> bool:
    return bool(_load_questions(store).get("unresolved", []))


def handle_spec_research(args) -> int:
    workspace = Path(args.workspace)
    services = build_services(args.profile, args.scenario, workspace)
    harness = RailForgeHarness(workspace=workspace, services=services)
    store = ArtifactStore(WorkspaceLayout(workspace))
    project = args.project or workspace.name
    result = harness.run(project=project, request_text=args.request)
    bridge = OpenSpecBridge(workspace)
    bridge.write_proposal(
        project,
        render_proposal(
            change_id=project,
            request_text=args.request,
            spec=_load_product_spec(store),
            questions=_load_questions(store).get("unresolved") or _load_questions(store).get("questions", []),
            decisions=_load_decisions(store).get("decisions", []),
            result_state=result.state.value,
        ),
    )
    print(result.state.value)
    return 0


def handle_spec_init(args) -> int:
    workspace = Path(args.workspace)
    store = ArtifactStore(WorkspaceLayout(workspace))
    store.init_workspace()
    openspec_root = workspace / "openspec"
    (openspec_root / "changes").mkdir(parents=True, exist_ok=True)
    (openspec_root / "specs").mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "workspace": str(workspace),
                "openspec": str(openspec_root),
                "runtime": str(WorkspaceLayout(workspace).runtime),
                "status": "READY",
            },
            ensure_ascii=False,
        )
    )
    return 0


def handle_answer(args) -> int:
    workspace = Path(args.workspace)
    store = ArtifactStore(WorkspaceLayout(workspace))
    store.init_workspace()
    payload = yaml.safe_load(Path(args.file).read_text(encoding="utf-8")) or {}
    current = {}
    try:
        current = store.load_answers()
    except ArtifactNotFoundError:
        current = {"answers": {}}
    current_answers = dict(current.get("answers", {}))
    current_answers.update(payload.get("answers", {}))
    store.save_answers({"answers": current_answers})
    print("ANSWERS_CAPTURED")
    return 0


def handle_approve(args) -> int:
    workspace = Path(args.workspace)
    store = ArtifactStore(WorkspaceLayout(workspace))
    store.init_workspace()
    store.save_approval(
        target=args.target,
        approved_by=args.approved_by or "human",
        note=args.note or "",
        task_id=args.task_id or "",
    )
    print("APPROVED")
    return 0


def handle_status(args) -> int:
    workspace = Path(args.workspace)
    layout = WorkspaceLayout(workspace)
    store = ArtifactStore(layout)
    recovery = RuntimeRecovery(
        layout=layout,
        store=store,
        checkpoints=FileCheckpointStore(layout),
        langgraph=LangGraphBridge(layout),
    )
    snapshot = recovery.recover()
    if snapshot.run_meta is None:
        payload = _load_run_state(workspace)
    else:
        payload = snapshot.run_meta.to_dict()
        payload["checkpoint_consistent"] = snapshot.checkpoint_consistent
        payload["issues"] = snapshot.issues
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def handle_resume(args) -> int:
    workspace = Path(args.workspace)
    services = _prepare_resume_services(args, workspace, allow_recovery=True)
    harness = RailForgeHarness(workspace=workspace, services=services)
    result = harness.resume(reason=args.reason, note=args.note)
    print(result.state.value)
    return 0


def handle_spec_plan(args) -> int:
    workspace = Path(args.workspace)
    store = ArtifactStore(WorkspaceLayout(workspace))
    if _has_unresolved_questions(store):
        print("BLOCKED")
        return 0
    if not store.has_approval("spec"):
        print("BLOCKED")
        return 0
    try:
        spec = store.load_product_spec()
    except ArtifactNotFoundError:
        print("BLOCKED")
        return 0
    services = _prepare_resume_services(args, workspace)
    harness = RailForgeHarness(workspace=workspace, services=services)
    result = harness.resume(reason=args.reason or "spec_plan", note=args.note or "continue to backlog planning")
    if result.blocked_reason in {"clarification_required", "spec_approval_required"}:
        print(result.state.value)
        return 0
    run_state = store.load_run_state()
    project = run_state.project_name or workspace.name
    bridge = OpenSpecBridge(workspace)
    questions = _load_questions(store)
    decisions = _load_decisions(store)
    layout = WorkspaceLayout(workspace)
    backlog = store.load_backlog(draft=not layout.backlog_path.exists())
    tasks = [TaskItem.from_dict(item) for item in backlog.get("items", [])]
    planning_contract = load_planning_contract(workspace)
    for task in tasks:
        store.save_contract(build_contract(task, planning_contract=planning_contract if planning_contract and planning_contract.is_ready else None))
    bridge.write_design(project, render_design(spec, tasks, decisions.get("decisions", [])))
    bridge.write_tasks(project, render_tasks(tasks))
    bridge.write_spec(
        project,
        "harness-core",
        render_spec(spec, tasks, questions.get("unresolved", []), decisions.get("decisions", [])),
    )
    print(result.state.value)
    return 0


def handle_execute(args) -> int:
    workspace = Path(args.workspace)
    store = ArtifactStore(WorkspaceLayout(workspace))
    if not store.has_approval("backlog"):
        print("BLOCKED")
        return 0
    services = _prepare_resume_services(args, workspace)
    harness = RailForgeHarness(workspace=workspace, services=services)
    result = harness.resume(reason=args.reason or "execute", note=args.note or "continue execution")
    print(result.state.value)
    return 0


def handle_spec_impl(args) -> int:
    return handle_execute(args)


def handle_prepare_execution(args) -> int:
    workspace = Path(args.workspace)
    store = ArtifactStore(WorkspaceLayout(workspace))
    if not store.has_approval("backlog"):
        print(json.dumps({"state": "BLOCKED", "reason": "backlog_approval_required"}, ensure_ascii=False))
        return 0
    services = _prepare_resume_services(args, workspace)
    harness = RailForgeHarness(workspace=workspace, services=services)
    payload = harness.prepare_execution_payload(
        reason=args.reason or "prepare_execution",
        note=args.note or "prepare hosted codex execution",
    )
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def handle_record_execution(args) -> int:
    workspace = Path(args.workspace)
    payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
    services = _prepare_resume_services(args, workspace)
    harness = RailForgeHarness(workspace=workspace, services=services)
    result = harness.record_execution_result(payload)
    print(result.state.value)
    return 0


def handle_review(args) -> int:
    workspace = Path(args.workspace)
    payload = _load_run_state(workspace)
    store = ArtifactStore(WorkspaceLayout(workspace))
    task_id = payload.get("current_task_id")
    if task_id:
        try:
            report = store.load_qa_report(task_id)
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            return 0
        except ArtifactNotFoundError:
            pass
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def handle_spec_review(args) -> int:
    workspace = Path(args.workspace)
    services = _prepare_resume_services(args, workspace, allow_recovery=True)
    harness = RailForgeHarness(workspace=workspace, services=services)
    payload = harness.run_spec_review()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0
