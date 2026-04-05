from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from railforge.application.runtime_services import build_services
from railforge.application.workflow_commands import create_workflow_command_service


def _emit(result: Any) -> int:
    if isinstance(result, (dict, list)):
        print(json.dumps(result, indent=2 if result else None, ensure_ascii=False))
    else:
        print(result)
    return 0


def handle_spec_research(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).spec_research(args))


def handle_spec_init(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).spec_init(args))


def handle_answer(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).answer(args))


def handle_approve(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).approve(args))


def handle_status(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).status())


def handle_resume(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).resume(args))


def handle_spec_plan(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).spec_plan(args))


def handle_execute(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).execute(args))


def handle_spec_impl(args) -> int:
    return handle_execute(args)


def handle_prepare_execution(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).prepare_execution(args))


def handle_record_execution(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).record_execution(args))


def handle_review(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).review())


def handle_spec_review(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).spec_review(args))


def handle_approve_and_resume(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).approve_and_resume(args))


def handle_answer_and_resume(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).answer_and_resume(args))


def handle_adopt_worktree(args) -> int:
    return _emit(create_workflow_command_service(Path(args.workspace)).adopt_worktree(args))
