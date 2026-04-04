from railforge.commands import build_services
from railforge.core.enums import RunState
from railforge.orchestrator.run_loop import RailForgeHarness


def test_real_services_use_hosted_codex_prepare_path(tmp_path) -> None:
    services = build_services(profile="real", scenario="default", workspace=tmp_path)
    harness = RailForgeHarness(workspace=tmp_path, services=services)

    blocked = harness.run(project="demo", request_text="最小 hosted smoke")

    assert blocked.state == RunState.BLOCKED
    assert blocked.blocked_reason in {"clarification_required", "spec_approval_required"}
