from pathlib import Path

from railforge.commands import build_services
from railforge.providers import HostedCodexAdapter, RoleRouter


def test_role_router_defaults_lead_writer_to_hosted_codex() -> None:
    router = RoleRouter()

    assert router.driver_for_role("lead_writer") == "hosted_codex"


def test_role_router_keeps_external_runners_for_review_roles() -> None:
    router = RoleRouter()

    assert router.driver_for_role("backend_specialist") == "claude_cli"
    assert router.driver_for_role("frontend_specialist") == "gemini_cli"


def test_build_services_real_uses_hosted_codex_adapter(tmp_path: Path) -> None:
    services = build_services(profile="real", scenario="default", workspace=tmp_path)

    assert isinstance(services.lead_writer, HostedCodexAdapter)
