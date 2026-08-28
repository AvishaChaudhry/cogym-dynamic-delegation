import pytest

from delegation_gym.state import ActionDisposition, DelegationState, DelegationUpdate


def base_state() -> DelegationState:
    return DelegationState.create(
        autonomous={"SEARCH", "DRAFT"},
        approval_required={"COMMIT"},
        prohibited={"DELETE"},
        constraints={"max_price": 100},
    )


def test_state_classifies_actions() -> None:
    state = base_state()
    assert state.disposition("search") is ActionDisposition.AUTONOMOUS
    assert state.disposition("COMMIT") is ActionDisposition.APPROVAL_REQUIRED
    assert state.disposition("DELETE") is ActionDisposition.PROHIBITED
    assert state.disposition("UNKNOWN") is ActionDisposition.UNCLASSIFIED


def test_transition_advances_version_and_returns_control() -> None:
    state = base_state()
    update = DelegationUpdate.create(
        autonomous={"SEARCH", "DRAFT"},
        approval_required=set(),
        prohibited={"COMMIT", "DELETE"},
        returned_control={"COMMIT"},
        version=2,
        constraints=state.constraints,
    )
    changed = state.apply(update)
    assert changed.version == 2
    assert changed.control_returned
    assert state.version == 1


def test_invalid_overlap_rejected() -> None:
    with pytest.raises(ValueError, match="overlap"):
        DelegationState.create(
            autonomous={"COMMIT"}, approval_required={"COMMIT"}, prohibited=set()
        )


def test_invalid_return_control_rejected() -> None:
    with pytest.raises(ValueError, match="unclassified"):
        DelegationState.create(
            autonomous={"SEARCH"},
            approval_required=set(),
            prohibited=set(),
            returned_control={"COMMIT"},
        )


def test_stale_or_skipped_transition_rejected() -> None:
    state = base_state()
    for version in (1, 3):
        update = DelegationUpdate.create(
            autonomous=state.autonomous,
            approval_required=state.approval_required,
            prohibited=state.prohibited,
            version=version,
        )
        with pytest.raises(ValueError, match="advance exactly one"):
            state.apply(update)
