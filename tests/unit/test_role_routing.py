import pytest

from railforge.providers import ClaudeCliSpecialistAdapter, CodexCliLeadWriterAdapter, GeminiCliSpecialistAdapter, RoleRouter


def test_role_router_maps_expected_backends() -> None:
    router = RoleRouter()

    assert router.driver_for_role("lead_writer") == "hosted_codex"
    assert router.backend_for_role("backend_specialist") == "claude_cli"
    assert router.driver_for_role("frontend_specialist") == "gemini_cli"


def test_role_router_rejects_unknown_role() -> None:
    router = RoleRouter()

    with pytest.raises(KeyError):
        router.driver_for_role("unknown_role")


def test_role_router_exposes_role_policy() -> None:
    router = RoleRouter()

    assert router.read_only_for_role("backend_specialist") is True
    assert router.allowed_tools_for_role("frontend_specialist") == ("shell", "playwright", "search")
    assert ".railforge/runtime/runs/" in router.write_roots_for_role("lead_writer")


@pytest.mark.parametrize(
    ("adapter", "role", "backend"),
    [
        (CodexCliLeadWriterAdapter(role_router=RoleRouter({"lead_writer": "codex_cli"})), "lead_writer", "codex_cli"),
        (ClaudeCliSpecialistAdapter(), "backend_specialist", "claude_cli"),
        (GeminiCliSpecialistAdapter(), "frontend_specialist", "gemini_cli"),
    ],
)
def test_cli_adapters_use_codeagent_wrapper(adapter, role, backend) -> None:
    result = adapter.invoke(
        role=role,
        workspace="/tmp/railforge",
        task={"id": "T-001"},
        contract={"task_id": "T-001"},
    )

    assert result.success is True
    assert result.metadata["invocation"]["backend"] == backend
    command = result.metadata["invocation"]["command"]
    assert command[:4] == ["python", "-m", "railforge.codeagent", "run"]
    assert backend in command
    assert "/tmp/railforge" in command
    assert result.metadata["invocation"]["role"] == role
    assert result.metadata["invocation"]["payload"]["role_policy"]["backend"] == backend
