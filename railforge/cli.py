from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence

from railforge import __version__
from railforge.command_catalog import COMMAND_SPECS, COMMON_PROFILE_ARGUMENTS
from railforge.commands import (
    handle_answer,
    handle_approve,
    handle_approve_and_resume,
    handle_answer_and_resume,
    handle_adopt_worktree,
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


def _resolve_workspace(explicit: Optional[str]) -> Path:
    """自动推断 workspace：向上查找 .railforge 或 .git 标记，找不到则报错"""
    if explicit:
        return Path(explicit)
    cwd = Path(os.getcwd())
    for parent in [cwd, *cwd.parents]:
        if (parent / ".railforge").is_dir():
            return parent
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            return parent
    raise SystemExit("No RailForge workspace detected. Run rf-spec-init or pass --workspace.")


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
        "approve-and-resume": handle_approve_and_resume,
        "answer-and-resume": handle_answer_and_resume,
        "adopt-worktree": handle_adopt_worktree,
        "status": handle_status,
        "run": handle_spec_research,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "workspace"):
        args.workspace = str(_resolve_workspace(args.workspace))
    return _dispatch_table()[args.command](args)
