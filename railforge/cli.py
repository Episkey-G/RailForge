import argparse
from pathlib import Path
from typing import Optional, Sequence

from railforge.adapters.mock import build_default_mock_services, build_repeated_failure_services
from railforge.orchestrator.run_loop import RailForgeHarness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="railforge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--workspace", required=True)
    run_parser.add_argument("--project", required=True)
    run_parser.add_argument("--request", required=True)
    run_parser.add_argument("--scenario", choices=["default", "repeated-failure"], default="default")

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("--workspace", required=True)
    resume_parser.add_argument("--reason", required=True)
    resume_parser.add_argument("--note", required=True)
    resume_parser.add_argument("--scenario", choices=["default", "repeated-failure"], default="default")
    return parser


def _build_services(scenario: str):
    if scenario == "repeated-failure":
        return build_repeated_failure_services()
    return build_default_mock_services()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    services = _build_services(args.scenario)
    if args.command == "resume" and args.scenario == "repeated-failure" and hasattr(services, "allow_recovery"):
        services.allow_recovery()
    harness = RailForgeHarness(workspace=Path(args.workspace), services=services)

    if args.command == "run":
        result = harness.run(project=args.project, request_text=args.request)
    else:
        result = harness.resume(reason=args.reason, note=args.note)

    print(result.state.value)
    return 0
