from __future__ import annotations

import argparse
from typing import Callable, Dict, Optional, Sequence

from railforge import __version__
from railforge.command_catalog import COMMAND_SPECS, COMMON_PROFILE_ARGUMENTS
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="railforge")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for spec in COMMAND_SPECS:
        command_parser = subparsers.add_parser(spec.name)
        for argument in spec.arguments:
            command_parser.add_argument(*argument.flags, **argument.kwargs)
        if spec.needs_profile:
            for argument in COMMON_PROFILE_ARGUMENTS:
                command_parser.add_argument(*argument.flags, **argument.kwargs)

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
