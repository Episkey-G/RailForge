from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from railforge.core.models import WorkspaceLayout


@dataclass
class PlanningContract:
    status: str
    allowed_paths: List[str]
    deliverables: List[str]
    locked_decisions: List[str]

    @property
    def is_ready(self) -> bool:
        return self.status in {"ready_for_impl", "approved", "ready"}

    @property
    def user_code_paths(self) -> List[str]:
        paths = []
        for path in self.allowed_paths:
            if path.startswith(".railforge/") or path.startswith("openspec/") or path.startswith("docs/exec-plans/"):
                continue
            paths.append(path)
        return paths


@dataclass
class PlanningContractTruth:
    contract: Optional[PlanningContract]
    payload: Dict[str, Any]
    source_path: Optional[Path]
    truth_path: Path

    @property
    def source(self) -> str:
        if self.source_path is None:
            return "missing"
        if self.source_path == self.truth_path:
            return "docs"
        return "legacy"


def _normalize_path(path: str, workspace: Path) -> str:
    value = path.strip()
    if not value:
        return value
    if value.endswith("/**"):
        value = value[:-3]
    if value.endswith("/*"):
        value = value[:-2]

    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(workspace)
        except ValueError:
            return value
        value = candidate.as_posix()
    else:
        value = candidate.as_posix()

    if value.startswith("./"):
        value = value[2:]
    if value and not value.endswith("/"):
        value += "/"
    return value


def load_planning_contract_truth(workspace: Path) -> PlanningContractTruth:
    layout = WorkspaceLayout(workspace)
    truth_path = layout.planning_contract_path
    source_path = next(
        (
            path
            for path in (
                truth_path,
                layout.legacy_planning_dir / "contract.yaml",
            )
            if path.exists()
        ),
        None,
    )
    if source_path is None:
        return PlanningContractTruth(
            contract=None,
            payload={},
            source_path=None,
            truth_path=truth_path,
        )

    payload = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    allowed_paths = [
        normalized
        for raw in payload.get("write_scope", {}).get("allowed_paths", [])
        if (normalized := _normalize_path(str(raw), workspace))
    ]
    return PlanningContractTruth(
        contract=PlanningContract(
            status=str(payload.get("status", "")),
            allowed_paths=allowed_paths,
            deliverables=[str(item).strip() for item in payload.get("deliverables", []) if str(item).strip()],
            locked_decisions=[str(item).strip() for item in payload.get("locked_decisions", []) if str(item).strip()],
        ),
        payload=payload,
        source_path=source_path,
        truth_path=truth_path,
    )


def load_planning_contract(workspace: Path) -> Optional[PlanningContract]:
    return load_planning_contract_truth(workspace).contract


def load_effective_planning_contract(
    workspace: Path,
    *,
    contract_approved: bool,
) -> Optional[PlanningContract]:
    contract = load_planning_contract(workspace)
    if contract is None:
        return None
    if contract.is_ready or not contract_approved:
        return contract
    return PlanningContract(
        status="approved",
        allowed_paths=list(contract.allowed_paths),
        deliverables=list(contract.deliverables),
        locked_decisions=list(contract.locked_decisions),
    )


def contract_approval_required(
    workspace: Path,
    *,
    backlog_approved: bool,
    contract_approved: bool,
) -> bool:
    if not backlog_approved:
        return False
    contract = load_effective_planning_contract(workspace, contract_approved=contract_approved)
    if contract is None or not contract.is_ready:
        return True
    return False


def planning_contract_gate_state(
    workspace: Path,
    *,
    backlog_approved: bool,
    contract_approved: bool,
) -> Dict[str, Any]:
    truth = load_planning_contract_truth(workspace)
    contract = load_effective_planning_contract(workspace, contract_approved=contract_approved)
    return {
        "truth_path": str(truth.truth_path.relative_to(workspace)),
        "source_path": str(truth.source_path.relative_to(workspace)) if truth.source_path else None,
        "source": truth.source,
        "exists": truth.source_path is not None,
        "status": truth.contract.status if truth.contract else "",
        "effective_status": contract.status if contract else "",
        "ready_for_impl": bool(contract and contract.is_ready),
        "backlog_approved": backlog_approved,
        "contract_approved": contract_approved,
        "approval_required": contract_approval_required(
            workspace,
            backlog_approved=backlog_approved,
            contract_approved=contract_approved,
        ),
    }


def draft_planning_contract(
    *,
    workspace: Path,
    project: str,
    tasks: List[Any],
    decisions: List[Dict[str, Any]],
    template: Dict[str, Any],
) -> Dict[str, Any]:
    layout = WorkspaceLayout(workspace)
    allowed_paths = sorted(
        {
            *[path for task in tasks for path in getattr(task, "allowed_paths", [])],
            f"openspec/changes/{project}/",
            str(layout.planning_dir.relative_to(layout.root)) + "/",
        }
    )
    payload = dict(template)
    payload["change"] = project
    payload["write_scope"] = {"allowed_paths": allowed_paths}
    payload["deliverables"] = [getattr(task, "title", "") for task in tasks]
    payload["locked_decisions"] = [
        item.get("topic", "")
        for item in decisions
        if item.get("topic")
    ]
    return payload


def task_scope_within_contract(task_paths: List[str], contract: PlanningContract) -> bool:
    allowed = contract.user_code_paths
    if not allowed:
        return True
    for path in task_paths:
        if path.startswith(".railforge/runtime/"):
            continue
        if any(path == scope or path.startswith(scope) for scope in allowed):
            continue
        return False
    return True


def task_scope_mismatches(task_paths: List[str], contract: PlanningContract) -> List[str]:
    mismatches = []
    allowed = contract.user_code_paths
    if not allowed:
        return mismatches
    for path in task_paths:
        if path.startswith(".railforge/runtime/"):
            continue
        if any(path == scope or path.startswith(scope) for scope in allowed):
            continue
        mismatches.append(path)
    return mismatches
