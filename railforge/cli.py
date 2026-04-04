from __future__ import annotations

import argparse
from typing import Callable, Dict, Optional, Sequence

from railforge import __version__
from railforge.commands import (
    handle_answer,
    handle_approve,
    handle_execute,
    handle_prepare_execution,
    handle_record_execution,
    handle_resume,
    handle_review,
    handle_spec_impl,
    handle_spec_init,
    handle_spec_plan,
    handle_spec_review,
    handle_spec_research,
    handle_status,
)


CommandHandler = Callable[[argparse.Namespace], int]


def _add_profile_and_scenario(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", choices=["mock", "real"], default="mock")
    parser.add_argument("--scenario", choices=["default", "repeated-failure", "hosted-smoke"], default="default")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="railforge")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    research_parser = subparsers.add_parser("spec-research")
    research_parser.add_argument("--workspace", required=True)
    research_parser.add_argument("--request", required=True)
    research_parser.add_argument("--project")
    _add_profile_and_scenario(research_parser)

    init_parser = subparsers.add_parser("spec-init")
    init_parser.add_argument("--workspace", required=True)

    plan_parser = subparsers.add_parser("spec-plan")
    plan_parser.add_argument("--workspace", required=True)
    plan_parser.add_argument("--reason")
    plan_parser.add_argument("--note")
    _add_profile_and_scenario(plan_parser)

    spec_impl_parser = subparsers.add_parser("spec-impl")
    spec_impl_parser.add_argument("--workspace", required=True)
    spec_impl_parser.add_argument("--reason")
    spec_impl_parser.add_argument("--note")
    _add_profile_and_scenario(spec_impl_parser)

    spec_review_parser = subparsers.add_parser("spec-review")
    spec_review_parser.add_argument("--workspace", required=True)
    _add_profile_and_scenario(spec_review_parser)

    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--workspace", required=True)
    execute_parser.add_argument("--reason")
    execute_parser.add_argument("--note")
    _add_profile_and_scenario(execute_parser)

    prepare_parser = subparsers.add_parser("prepare-execution")
    prepare_parser.add_argument("--workspace", required=True)
    prepare_parser.add_argument("--reason")
    prepare_parser.add_argument("--note")
    _add_profile_and_scenario(prepare_parser)

    record_parser = subparsers.add_parser("record-execution")
    record_parser.add_argument("--workspace", required=True)
    record_parser.add_argument("--file", required=True)
    _add_profile_and_scenario(record_parser)

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--workspace", required=True)
    _add_profile_and_scenario(review_parser)

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("--workspace", required=True)
    resume_parser.add_argument("--reason", required=True)
    resume_parser.add_argument("--note", required=True)
    _add_profile_and_scenario(resume_parser)

    answer_parser = subparsers.add_parser("answer")
    answer_parser.add_argument("--workspace", required=True)
    answer_parser.add_argument("--file", required=True)

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("--workspace", required=True)
    approve_parser.add_argument("--target", choices=["spec", "backlog", "contract"], required=True)
    approve_parser.add_argument("--task-id")
    approve_parser.add_argument("--approved-by")
    approve_parser.add_argument("--note")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--workspace", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--workspace", required=True)
    run_parser.add_argument("--request", required=True)
    run_parser.add_argument("--project")
    _add_profile_and_scenario(run_parser)

    return parser


def _dispatch_table() -> Dict[str, CommandHandler]:
    return {
        "spec-init": handle_spec_init,
        "spec-research": handle_spec_research,
        "spec-plan": handle_spec_plan,
        "spec-impl": handle_spec_impl,
        "spec-review": handle_spec_review,
        "execute": handle_execute,
        "prepare-execution": handle_prepare_execution,
        "record-execution": handle_record_execution,
        "review": handle_review,
        "resume": handle_resume,
        "answer": handle_answer,
        "approve": handle_approve,
        "status": handle_status,
        "run": handle_spec_research,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return _dispatch_table()[args.command](args)
