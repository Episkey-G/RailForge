from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class ArgumentSpec:
    flags: tuple[str, ...]
    kwargs: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandSpec:
    name: str
    arguments: tuple[ArgumentSpec, ...]
    needs_profile: bool = False


COMMON_PROFILE_ARGUMENTS: tuple[ArgumentSpec, ...] = (
    ArgumentSpec(("--profile",), {"choices": ["mock", "real"], "default": "mock"}),
    ArgumentSpec(
        ("--scenario",),
        {"choices": ["default", "repeated-failure", "hosted-smoke"], "default": "default"},
    ),
)


COMMAND_SPECS: Sequence[CommandSpec] = (
    CommandSpec(
        "spec-research",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--request",), {"required": True}),
            ArgumentSpec(("--project",), {}),
        ),
        needs_profile=True,
    ),
    CommandSpec("spec-init", (ArgumentSpec(("--workspace",), {"default": None}),)),
    CommandSpec(
        "spec-plan",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--reason",), {}),
            ArgumentSpec(("--note",), {}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "spec-impl",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--reason",), {}),
            ArgumentSpec(("--note",), {}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "spec-review",
        (ArgumentSpec(("--workspace",), {"default": None}),),
        needs_profile=True,
    ),
    CommandSpec(
        "execute",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--reason",), {}),
            ArgumentSpec(("--note",), {}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "prepare-execution",
        (
            ArgumentSpec(("--workspace",), {"required": True}),
            ArgumentSpec(("--reason",), {}),
            ArgumentSpec(("--note",), {}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "record-execution",
        (
            ArgumentSpec(("--workspace",), {"required": True}),
            ArgumentSpec(("--file",), {"required": True}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "review",
        (ArgumentSpec(("--workspace",), {"default": None}),),
        needs_profile=True,
    ),
    CommandSpec(
        "resume",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--reason",), {"required": True}),
            ArgumentSpec(("--note",), {"required": True}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "answer",
        (
            ArgumentSpec(("--workspace",), {"required": True}),
            ArgumentSpec(("--file",), {"required": True}),
        ),
    ),
    CommandSpec(
        "approve",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--target",), {"choices": ["spec", "backlog", "contract"], "required": True}),
            ArgumentSpec(("--task-id",), {}),
            ArgumentSpec(("--approved-by",), {}),
            ArgumentSpec(("--note",), {}),
        ),
    ),
    CommandSpec("status", (ArgumentSpec(("--workspace",), {"default": None}),)),
    CommandSpec(
        "approve-and-resume",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--target",), {"choices": ["spec", "backlog", "contract"], "required": True}),
            ArgumentSpec(("--task-id",), {}),
            ArgumentSpec(("--approved-by",), {}),
            ArgumentSpec(("--note",), {}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "answer-and-resume",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--file",), {"required": True}),
            ArgumentSpec(("--note",), {}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "adopt-worktree",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--task-id",), {"required": True}),
            ArgumentSpec(("--note",), {"default": "manual repair adopted"}),
        ),
        needs_profile=True,
    ),
    CommandSpec(
        "run",
        (
            ArgumentSpec(("--workspace",), {"default": None}),
            ArgumentSpec(("--request",), {"required": True}),
            ArgumentSpec(("--project",), {}),
        ),
        needs_profile=True,
    ),
)
