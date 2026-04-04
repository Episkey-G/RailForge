from railforge.codeagent.models import AgentRequest


def test_agent_request_keeps_prompt_and_payload() -> None:
    request = AgentRequest(
        backend="codex",
        role="lead_writer",
        workspace="/tmp/demo",
        prompt="请返回 OK",
        payload={"task": {"id": "T-001"}},
    )

    assert request.backend == "codex"
    assert request.role == "lead_writer"
    assert request.payload["task"]["id"] == "T-001"
