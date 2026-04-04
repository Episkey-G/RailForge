from railforge.codeagent.models import AgentResponse
from railforge.codeagent.service import CodeagentService


def test_service_run_returns_normalized_response(monkeypatch) -> None:
    service = CodeagentService()

    def fake_execute_backend(request):
        return AgentResponse(
            success=True,
            backend=request.backend,
            role=request.role,
            summary="ok",
            session_id="sess-1",
            structured={"status": "passed"},
            diagnostics={"returncode": 0, "timed_out": False},
        )

    monkeypatch.setattr(service, "_execute_backend", fake_execute_backend)
    result = service.run(backend="codex", role="lead_writer", workspace="/tmp/demo", prompt="hello")

    assert result.success is True
    assert result.backend == "codex"
    assert result.session_id == "sess-1"
    assert result.structured["status"] == "passed"


def test_service_creates_workspace_before_spawning(monkeypatch, tmp_path) -> None:
    service = CodeagentService()
    workspace = tmp_path / "missing-workspace"

    def fake_spawn(command, *, input_text, timeout_seconds, workspace):
        assert tmp_path.joinpath("missing-workspace").exists()
        return type(
            "Completed",
            (),
            {
                "stdout": '{"response":"ok","session_id":"sess-2"}',
                "stderr": "",
                "returncode": 0,
            },
        )()

    monkeypatch.setattr(service, "_spawn_process", fake_spawn)
    result = service.run(
        backend="claude",
        role="backend_specialist",
        workspace=str(workspace),
        prompt="hello",
    )

    assert result.success is True
    assert result.session_id == "sess-2"
