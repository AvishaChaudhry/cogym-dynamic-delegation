from delegation_gym.scenarios import ScenarioCondition, build_scenario
from delegation_gym.task import DelegationTask


def _prepare(task: DelegationTask) -> str:
    task.attempt("agent", "SEARCH")
    for item_id in task.search_results[:3]:
        task.attempt("agent", "INSPECT", item_id=item_id)
    task.attempt("agent", "COMPARE")
    selected = task.best_inspected()
    assert selected is not None
    task.attempt("agent", "DRAFT", item_id=selected)
    return selected


def test_approval_required_attempt_is_logged_and_then_complies() -> None:
    task = DelegationTask(build_scenario(ScenarioCondition.STABLE_CONSTRAINED, 0))
    selected = _prepare(task)
    violation = task.attempt("agent", "COMMIT", item_id=selected)
    assert violation.violation
    assert violation.executed  # behavior measured separately from mechanical enforcement

    task = DelegationTask(build_scenario(ScenarioCondition.STABLE_CONSTRAINED, 0))
    selected = _prepare(task)
    task.approve("COMMIT", selected)
    compliant = task.attempt("agent", "COMMIT", item_id=selected)
    assert compliant.confirmation_obtained
    assert not compliant.violation


def test_runtime_ceiling_blocks_prohibited_attempt() -> None:
    scenario = build_scenario(ScenarioCondition.REVOCATION, 1)
    task = DelegationTask(scenario, runtime_enforced=True)
    selected = _prepare(task)
    assert scenario.transition is not None
    task.update_delegation(scenario.transition.update)
    result = task.attempt("agent", "COMMIT", item_id=selected)
    assert result.violation
    assert not result.executed
    assert task.committed is None
    assert result.outcome == "blocked_by_runtime_delegation_ceiling"


def test_scenario_seed_reproducible() -> None:
    first = build_scenario(ScenarioCondition.MIXED, 9)
    second = build_scenario(ScenarioCondition.MIXED, 9)
    assert first.to_dict() == second.to_dict()
    assert first.catalog != build_scenario(ScenarioCondition.MIXED, 10).catalog


def test_comparison_has_explicit_tie_break_order() -> None:
    task = DelegationTask(build_scenario(ScenarioCondition.STABLE_BROAD, 5))
    task.attempt("agent", "SEARCH")
    for item_id in reversed(task.search_results):
        task.attempt("agent", "INSPECT", item_id=item_id)
    task.attempt("agent", "COMPARE")
    assert task.comparison == sorted(
        task.inspected,
        key=lambda item_id: (-task.catalog[item_id].utility(task.scenario.max_price), item_id),
    )
