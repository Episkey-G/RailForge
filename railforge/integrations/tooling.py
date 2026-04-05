from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from railforge.providers.role_profiles import RoleRuntimeProfile, load_role_profiles


@dataclass(frozen=True)
class RoleToolingProfile:
    role: str
    allowed_tools: tuple[str, ...]
    write_roots: tuple[str, ...]
    read_only: bool


class IntegrationBoundary:
    def __init__(self, role_profiles: dict[str, RoleRuntimeProfile]) -> None:
        self.role_profiles = role_profiles

    def tooling_for_role(self, role: str) -> RoleToolingProfile:
        profile = self.role_profiles[role]
        return RoleToolingProfile(
            role=role,
            allowed_tools=profile.allowed_tools,
            write_roots=profile.write_roots,
            read_only=profile.read_only,
        )


def load_integration_boundary(workspace: Path) -> IntegrationBoundary:
    return IntegrationBoundary(load_role_profiles(workspace))
