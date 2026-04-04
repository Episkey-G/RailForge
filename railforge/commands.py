from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import yaml

from railforge.adapters.mock import build_default_mock_services, build_repeated_failure_services
from railforge.artifacts.store import ArtifactStore
from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import WorkspaceLayout
from railforge.openspec_bridge import OpenSpecBridge
from railforge.orchestrator.run_loop import RailForgeHarness


def build_services(profile: str, scenario: str, workspace: Path) -> Any:
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


def handle_spec_research(args) -> int:
    workspace = Path(args.workspace)
    services = build_services(args.profile, args.scenario, workspace)
    harness = RailForgeHarness(workspace=workspace, services=services)
    project = args.project or workspace.name
    result = harness.run(project=project, request_text=args.request)
    bridge = OpenSpecBridge(workspace)
    bridge.write_proposal(
        project,
        "# Proposal\n\n"
        f"- Change: {project}\n"
        f"- Request: {args.request}\n"
        f"- Result State: {result.state.value}\n",
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
    payload = _load_run_state(workspace)
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
    if not store.has_approval("spec"):
        print("BLOCKED")
        return 0
    services = _prepare_resume_services(args, workspace)
    harness = RailForgeHarness(workspace=workspace, services=services)
    result = harness.resume(reason=args.reason or "spec_plan", note=args.note or "continue to backlog planning")
    run_state = store.load_run_state()
    project = run_state.project_name or workspace.name
    bridge = OpenSpecBridge(workspace)
    spec = store.load_product_spec()
    backlog = store.load_backlog(draft=not WorkspaceLayout(workspace).backlog_path.exists())
    bridge.write_design(
        project,
        "# Design\n\n"
        f"## Summary\n{spec.summary}\n\n"
        "## Acceptance Criteria\n"
        + "\n".join(f"- {item}" for item in spec.acceptance_criteria),
    )
    bridge.write_tasks(
        project,
        "\n".join(f"- [ ] {item['id']} {item['title']}" for item in backlog.get("items", [])),
    )
    bridge.write_spec(
        project,
        "harness-core",
        "# Spec\n\n"
        "## Constraints\n"
        + "\n".join(f"- {item}" for item in spec.constraints),
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
    return handle_review(args)
