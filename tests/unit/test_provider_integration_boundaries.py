from pathlib import Path

from railforge.adapters.codeagent_wrapper import CodeagentWrapper as CompatCodeagentWrapper
from railforge.adapters.git import DryRunGitAdapter as CompatGitAdapter
from railforge.adapters.role_router import RoleRouter as CompatRoleRouter
from railforge.integrations import CodeagentWrapper, DryRunGitAdapter, load_integration_boundary
from railforge.providers import RoleRouter, load_role_profiles


def test_providers_load_role_profiles_from_codex_agents(tmp_path: Path) -> None:
    agents_dir = tmp_path / ".codex" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "backend-specialist.toml").write_text(
        '\n'.join(
            [
                'role = "backend_specialist"',
                'backend = "claude_cli"',
                'model = "claude_cli"',
                "read_only = true",
                'write_roots = [".railforge/runtime/reviews/"]',
                'allowed_tools = ["shell", "search"]',
                'summary = "backend reviewer"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = load_role_profiles(tmp_path)

    profile = profiles["backend_specialist"]
    assert profile.backend == "claude_cli"
    assert profile.read_only is True
    assert profile.write_roots == (".railforge/runtime/reviews/",)
    assert profile.allowed_tools == ("shell", "search")


def test_integration_boundary_uses_provider_role_policy(tmp_path: Path) -> None:
    agents_dir = tmp_path / ".codex" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "frontend-specialist.toml").write_text(
        '\n'.join(
            [
                'role = "frontend_specialist"',
                'backend = "gemini_cli"',
                'model = "gemini_cli"',
                "read_only = true",
                'write_roots = [".railforge/runtime/proposals/"]',
                'allowed_tools = ["shell", "playwright", "search"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    tooling = load_integration_boundary(tmp_path).tooling_for_role("frontend_specialist")

    assert tooling.read_only is True
    assert tooling.allowed_tools == ("shell", "playwright", "search")
    assert tooling.write_roots == (".railforge/runtime/proposals/",)


def test_compatibility_layers_reexport_new_boundaries() -> None:
    assert CompatRoleRouter is RoleRouter
    assert CompatCodeagentWrapper is CodeagentWrapper
    assert CompatGitAdapter is DryRunGitAdapter
