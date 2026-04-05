from argparse import Namespace

from railforge import commands


class _StubWorkflowService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Namespace | None]] = []

    def spec_plan(self, args: Namespace) -> str:
        self.calls.append(("spec_plan", args))
        return "BLOCKED"

    def status(self) -> dict[str, str]:
        self.calls.append(("status", None))
        return {"state": "READY"}


def test_handle_spec_plan_delegates_to_workflow_service(monkeypatch, capsys) -> None:
    service = _StubWorkflowService()

    monkeypatch.setattr(commands, "create_workflow_command_service", lambda workspace: service)

    args = Namespace(workspace="/tmp/demo", reason="resume", note="continue")
    result = commands.handle_spec_plan(args)

    assert result == 0
    assert service.calls == [("spec_plan", args)]
    assert capsys.readouterr().out.strip() == "BLOCKED"


def test_handle_status_delegates_to_workflow_service(monkeypatch, capsys) -> None:
    service = _StubWorkflowService()

    monkeypatch.setattr(commands, "create_workflow_command_service", lambda workspace: service)

    args = Namespace(workspace="/tmp/demo")
    result = commands.handle_status(args)

    assert result == 0
    assert service.calls == [("status", None)]
    assert '"state": "READY"' in capsys.readouterr().out
