from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


@dataclass(frozen=True)
class RoleRuntimeProfile:
    role: str
    backend: str
    model: str = ""
    read_only: bool = True
    write_roots: tuple[str, ...] = field(default_factory=tuple)
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "backend": self.backend,
            "model": self.model,
            "read_only": self.read_only,
            "write_roots": list(self.write_roots),
            "allowed_tools": list(self.allowed_tools),
            "summary": self.summary,
        }


DEFAULT_ROLE_PROFILES: dict[str, RoleRuntimeProfile] = {
    "lead_writer": RoleRuntimeProfile(
        role="lead_writer",
        backend="hosted_codex",
        model="hosted_codex",
        read_only=False,
        write_roots=(
            "railforge/",
            "tests/",
            "docs/",
            "openspec/changes/",
            ".railforge/runtime/runs/",
            ".railforge/runtime/execution_requests/",
            ".railforge/runtime/execution_results/",
            ".railforge/runtime/traces/",
            ".railforge/runtime/notes/",
        ),
        allowed_tools=("shell", "git", "playwright"),
        summary="Default source-code writer for approved RailForge implementation work.",
    ),
    "clarification_analyst": RoleRuntimeProfile(
        role="clarification_analyst",
        backend="hosted_codex",
        model="hosted_codex",
        read_only=True,
        write_roots=(".railforge/runtime/", "docs/product-specs/", "openspec/changes/"),
        allowed_tools=("shell", "search"),
        summary="Structured clarification analyst that emits research and planning ambiguity payloads.",
    ),
    "backend_specialist": RoleRuntimeProfile(
        role="backend_specialist",
        backend="claude_cli",
        model="claude_cli",
        read_only=True,
        write_roots=(".railforge/runtime/reviews/", ".railforge/runtime/proposals/"),
        allowed_tools=("shell", "search"),
        summary="Read-only backend reviewer that emits review and proposal artifacts.",
    ),
    "frontend_specialist": RoleRuntimeProfile(
        role="frontend_specialist",
        backend="gemini_cli",
        model="gemini_cli",
        read_only=True,
        write_roots=(".railforge/runtime/reviews/", ".railforge/runtime/proposals/"),
        allowed_tools=("shell", "playwright", "search"),
        summary="Read-only frontend reviewer that emits review and proposal artifacts.",
    ),
    "backend_evaluator": RoleRuntimeProfile(
        role="backend_evaluator",
        backend="claude_cli",
        model="claude_cli",
        read_only=True,
        write_roots=(".railforge/runtime/reviews/", ".railforge/runtime/proposals/"),
        allowed_tools=("shell", "search"),
        summary="Independent backend evaluator for post-deterministic compliance review.",
    ),
    "frontend_evaluator": RoleRuntimeProfile(
        role="frontend_evaluator",
        backend="gemini_cli",
        model="gemini_cli",
        read_only=True,
        write_roots=(".railforge/runtime/reviews/", ".railforge/runtime/proposals/"),
        allowed_tools=("shell", "playwright", "search"),
        summary="Independent frontend evaluator for post-deterministic compliance review.",
    ),
}


def _profile_from_toml(path: Path) -> RoleRuntimeProfile | None:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    role = str(payload.get("role") or "").strip()
    backend = str(payload.get("backend") or payload.get("model") or "").strip()
    if not role or not backend:
        return None
    return RoleRuntimeProfile(
        role=role,
        backend=backend,
        model=str(payload.get("model") or backend).strip(),
        read_only=bool(payload.get("read_only", True)),
        write_roots=tuple(str(item) for item in payload.get("write_roots", []) if str(item).strip()),
        allowed_tools=tuple(str(item) for item in payload.get("allowed_tools", []) if str(item).strip()),
        summary=str(payload.get("summary") or "").strip(),
    )


def load_role_profiles(workspace: Path) -> dict[str, RoleRuntimeProfile]:
    from railforge.core.models import WorkspaceLayout

    layout = WorkspaceLayout(workspace)
    result = dict(DEFAULT_ROLE_PROFILES)
    for path in sorted(layout.codex_agents_dir.glob("*.toml")):
        profile = _profile_from_toml(path)
        if profile:
            result[profile.role] = profile
    if not layout.models_path.exists():
        return result
    payload = yaml.safe_load(layout.models_path.read_text(encoding="utf-8")) or {}
    roles = payload.get("roles", {})
    for role, config in roles.items():
        existing = result.get(role, RoleRuntimeProfile(role=role, backend=""))
        backend = str(config.get("driver") or config.get("adapter") or existing.backend).strip()
        if not backend:
            continue
        result[role] = RoleRuntimeProfile(
            role=role,
            backend=backend,
            model=str(config.get("model") or existing.model or backend).strip(),
            read_only=existing.read_only,
            write_roots=existing.write_roots,
            allowed_tools=existing.allowed_tools,
            summary=existing.summary,
        )
    return result


def load_role_backends(workspace: Path) -> dict[str, str]:
    return {role: profile.backend for role, profile in load_role_profiles(workspace).items()}
