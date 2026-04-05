from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


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
            if path.startswith(".railforge/") or path.startswith("openspec/"):
                continue
            paths.append(path)
        return paths


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


def load_planning_contract(workspace: Path) -> Optional[PlanningContract]:
    path = workspace / ".railforge" / "planning" / "contract.yaml"
    if not path.exists():
        return None
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    allowed_paths = [
        normalized
        for raw in payload.get("write_scope", {}).get("allowed_paths", [])
        if (normalized := _normalize_path(str(raw), workspace))
    ]
    return PlanningContract(
        status=str(payload.get("status", "")),
        allowed_paths=allowed_paths,
        deliverables=[str(item).strip() for item in payload.get("deliverables", []) if str(item).strip()],
        locked_decisions=[str(item).strip() for item in payload.get("locked_decisions", []) if str(item).strip()],
    )


def task_scope_within_contract(task_paths: List[str], contract: PlanningContract) -> bool:
    allowed = contract.user_code_paths
    if not allowed:
        return True
    for path in task_paths:
        if path.startswith(".railforge/execution/tasks/"):
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
        if path.startswith(".railforge/execution/tasks/"):
            continue
        if any(path == scope or path.startswith(scope) for scope in allowed):
            continue
        mismatches.append(path)
    return mismatches
