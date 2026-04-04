from typing import Dict, Iterable, Set

from .enums import RunState
from .errors import InvalidTransitionError


_ALLOWED_TRANSITIONS = {
    RunState.INTAKE: {RunState.SPEC_EXPANSION, RunState.BLOCKED, RunState.FAILED},
    RunState.SPEC_EXPANSION: {RunState.BACKLOG_BUILD, RunState.BLOCKED, RunState.FAILED},
    RunState.BACKLOG_BUILD: {RunState.TASK_SELECTED, RunState.BLOCKED, RunState.FAILED},
    RunState.TASK_SELECTED: {RunState.CONTRACT_NEGOTIATION, RunState.NEXT_TASK, RunState.BLOCKED, RunState.FAILED},
    RunState.CONTRACT_NEGOTIATION: {RunState.IMPLEMENTING, RunState.BLOCKED, RunState.FAILED},
    RunState.IMPLEMENTING: {RunState.STATIC_REVIEW, RunState.BLOCKED, RunState.FAILED},
    RunState.STATIC_REVIEW: {RunState.RUNTIME_QA, RunState.REPAIRING, RunState.BLOCKED, RunState.FAILED},
    RunState.RUNTIME_QA: {RunState.READY_TO_COMMIT, RunState.REPAIRING, RunState.BLOCKED, RunState.FAILED},
    RunState.REPAIRING: {RunState.IMPLEMENTING, RunState.BLOCKED, RunState.FAILED},
    RunState.READY_TO_COMMIT: {RunState.COMMITTED, RunState.BLOCKED, RunState.FAILED},
    RunState.COMMITTED: {RunState.NEXT_TASK, RunState.BLOCKED, RunState.FAILED},
    RunState.NEXT_TASK: {RunState.TASK_SELECTED, RunState.DONE, RunState.BLOCKED, RunState.FAILED},
    RunState.DONE: set(),
    RunState.BLOCKED: set(),
    RunState.FAILED: set(),
}  # type: Dict[RunState, Set[RunState]]


def terminal_states() -> Set[RunState]:
    return {RunState.DONE, RunState.BLOCKED, RunState.FAILED}


def can_transition(current: RunState, nxt: RunState) -> bool:
    return nxt in _ALLOWED_TRANSITIONS[current]


def ensure_transition(current: RunState, nxt: RunState) -> None:
    if not can_transition(current, nxt):
        raise InvalidTransitionError("invalid transition: %s -> %s" % (current.value, nxt.value))


def transitions_for(state: RunState) -> Iterable[RunState]:
    return _ALLOWED_TRANSITIONS[state]

