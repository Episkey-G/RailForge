import subprocess

from railforge.codeagent.service import CodeagentService


def test_codex_request_never_emits_xhigh() -> None:
    service = CodeagentService()
    request = service.build_request(
        backend="codex",
        role="lead_writer",
        workspace="/tmp/demo",
        prompt="hello",
        payload={"reasoning_effort": "xhigh"},
    )

    command = service._command_for(request)
    joined = " ".join(command)
    assert "xhigh" not in joined
    assert 'model_reasoning_effort="high"' in joined


def test_gemini_timeout_returns_structured_failure(monkeypatch) -> None:
    service = CodeagentService()

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["gemini"], timeout=1)

    monkeypatch.setattr(service, "_spawn_process", raise_timeout)
    result = service.run(
        backend="gemini",
        role="frontend_specialist",
        workspace="/tmp/demo",
        prompt="hello",
    )

    assert result.success is False
    assert result.structured["status"] == "failed"
    assert result.diagnostics["timed_out"] is True
