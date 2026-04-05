from __future__ import annotations

from pathlib import Path
from typing import Any

from railforge.adapters.mock import (
    build_default_mock_services,
    build_hosted_smoke_services,
    build_repeated_failure_services,
    MockClarificationAnalystAdapter,
)


def build_services(profile: str, scenario: str, workspace: Path) -> Any:
    if scenario == "hosted-smoke":
        return build_hosted_smoke_services()
    if profile == "real":
        try:
            from railforge.adapters.base import HarnessServices
            from railforge.integrations import (
                CodeagentWrapper,
                DryRunGitAdapter,
                IntegrationBoundary,
                LocalShellAdapter,
                NoopPlaywrightAdapter,
                load_integration_boundary,
            )
            from railforge.providers import (
                ClarificationAnalystAdapter,
                ClaudeCliSpecialistAdapter,
                GeminiCliSpecialistAdapter,
                HostedCodexAdapter,
                RoleRouter,
                load_role_profiles,
            )
        except Exception:
            return build_default_mock_services()
        role_profiles = load_role_profiles(workspace)
        router = RoleRouter(role_profiles=role_profiles)
        wrapper = CodeagentWrapper(dry_run=False)
        tooling = load_integration_boundary(workspace)
        _assert_tooling_alignment(tooling, "lead_writer", ("shell", "git", "playwright"))
        _assert_tooling_alignment(tooling, "backend_specialist", ("shell", "search"))
        _assert_tooling_alignment(tooling, "frontend_specialist", ("shell", "playwright", "search"))
        return HarnessServices(
            lead_writer=HostedCodexAdapter(),
            backend_specialist=ClaudeCliSpecialistAdapter(
                role_name="backend_specialist",
                role_router=router,
                wrapper=wrapper,
            ),
            frontend_specialist=GeminiCliSpecialistAdapter(
                role_name="frontend_specialist",
                role_router=router,
                wrapper=wrapper,
            ),
            git=DryRunGitAdapter(),
            shell=LocalShellAdapter(),
            playwright=NoopPlaywrightAdapter(),
            backend_evaluator=ClaudeCliSpecialistAdapter(
                role_name="backend_evaluator",
                role_router=router,
                wrapper=wrapper,
            ),
            frontend_evaluator=GeminiCliSpecialistAdapter(
                role_name="frontend_evaluator",
                role_router=router,
                wrapper=wrapper,
            ),
            clarification_analyst=ClarificationAnalystAdapter(
                delegate=MockClarificationAnalystAdapter(),
                role_router=router,
                wrapper=wrapper,
            ),
        )
    if scenario == "repeated-failure":
        return build_repeated_failure_services()
    return build_default_mock_services()


def prepare_resume_services(args: Any, workspace: Path, allow_recovery: bool = False) -> Any:
    services = build_services(args.profile, args.scenario, workspace)
    if allow_recovery and args.scenario == "repeated-failure" and hasattr(services, "allow_recovery"):
        services.allow_recovery()
    return services


def _assert_tooling_alignment(tooling: Any, role: str, expected: tuple[str, ...]) -> None:
    actual = tooling.tooling_for_role(role).allowed_tools
    if actual != expected:
        raise ValueError("Role %s tooling drifted: %s != %s" % (role, actual, expected))
