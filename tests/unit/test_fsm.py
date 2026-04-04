import pytest

from railforge.core.enums import RunState
from railforge.core.errors import InvalidTransitionError
from railforge.core.fsm import can_transition, ensure_transition, terminal_states


def test_terminal_states_are_explicit() -> None:
    assert terminal_states() == {RunState.DONE, RunState.BLOCKED, RunState.FAILED}


def test_known_valid_transition_passes() -> None:
    ensure_transition(RunState.INTAKE, RunState.SPEC_EXPANSION)
    assert can_transition(RunState.RUNTIME_QA, RunState.REPAIRING) is True


def test_invalid_transition_raises() -> None:
    with pytest.raises(InvalidTransitionError):
        ensure_transition(RunState.INTAKE, RunState.DONE)
