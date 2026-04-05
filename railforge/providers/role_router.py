from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from railforge.adapters.base import AdapterInvocation
from railforge.integrations.codeagent import CodeagentWrapper
from railforge.providers.role_profiles import DEFAULT_ROLE_PROFILES, RoleRuntimeProfile, load_role_backends, load_role_profiles


class RoleRouter:
    DEFAULT_ROLE_BACKENDS = {role: profile.backend for role, profile in DEFAULT_ROLE_PROFILES.items()}

    def __init__(
        self,
        role_backends: Mapping[str, str] | None = None,
        role_profiles: Mapping[str, RoleRuntimeProfile] | None = None,
        wrapper: CodeagentWrapper | None = None,
    ) -> None:
        profiles = dict(DEFAULT_ROLE_PROFILES)
        if role_profiles:
            profiles.update(role_profiles)
        if role_backends:
            for role, backend in role_backends.items():
                existing = profiles.get(role, RoleRuntimeProfile(role=role, backend=backend))
                profiles[role] = RoleRuntimeProfile(
                    role=role,
                    backend=backend,
                    model=existing.model or backend,
                    read_only=existing.read_only,
                    write_roots=existing.write_roots,
                    allowed_tools=existing.allowed_tools,
                    summary=existing.summary,
                )
        self.role_profiles = profiles
        self.wrapper = wrapper or CodeagentWrapper()

    def profile_for_role(self, role: str) -> RoleRuntimeProfile:
        if role not in self.role_profiles:
            raise KeyError(f"Unknown role: {role}")
        return self.role_profiles[role]

    def driver_for_role(self, role: str) -> str:
        return self.profile_for_role(role).backend

    def backend_for_role(self, role: str) -> str:
        return self.driver_for_role(role)

    def allowed_tools_for_role(self, role: str) -> tuple[str, ...]:
        return self.profile_for_role(role).allowed_tools

    def write_roots_for_role(self, role: str) -> tuple[str, ...]:
        return self.profile_for_role(role).write_roots

    def read_only_for_role(self, role: str) -> bool:
        return self.profile_for_role(role).read_only

    def route(
        self,
        *,
        role: str,
        workspace: str | Path,
        payload: Mapping[str, Any] | None = None,
    ) -> AdapterInvocation:
        profile = self.profile_for_role(role)
        return self.wrapper.build_invocation(
            role=role,
            backend=profile.backend,
            workspace=workspace,
            payload=payload,
        )
