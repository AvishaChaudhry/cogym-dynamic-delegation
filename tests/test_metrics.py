from delegation_gym.agents import AgentCondition
from delegation_gym.events import EpisodeTrace, EventType, TrajectoryEvent
from delegation_gym.experiment import run_episode
from delegation_gym.metrics import compute_metrics
from delegation_gym.scenarios import ScenarioCondition, build_scenario


def test_metrics_on_hand_constructed_trace() -> None:
    trace = EpisodeTrace(
        episode_id="hand",
        metadata={"agent_condition": "test"},
        scenario={"condition": "test"},
        final_result={
            "task_performance": 0.5,
            "delivery_rate": 1,
            "collaborative_score": 0.5,
            "delivered": True,
        },
    )
    trace.append(
        TrajectoryEvent(
            step=0,
            actor="agent",
            event_type=EventType.TASK_ACTION.value,
            behavior="ACT",
            delegation_version=1,
            action_category="COMMIT",
            confirmation_required=True,
            confirmation_obtained=False,
            violation=True,
            attempted=True,
            executed=True,
        )
    )
    metrics = compute_metrics(trace)
    assert metrics["delegation_violation_rate"] == 1.0
    assert metrics["required_confirmation_compliance"] == 0.0
    assert metrics["agent_task_action_attempts"] == 1


def test_revocation_agent_conditions_separate_behavior_and_enforcement() -> None:
    scenario = build_scenario(ScenarioCondition.REVOCATION, 2)
    autonomous = run_episode(scenario, AgentCondition.AUTONOMOUS)
    aware = run_episode(scenario, AgentCondition.DELEGATION_AWARE)
    enforced = run_episode(scenario, AgentCondition.RUNTIME_ENFORCED)
    assert autonomous.metrics["delegation_violation_count"] == 1
    assert autonomous.metrics["control_return_compliance"] == 0.0
    assert aware.metrics["delegation_violation_count"] == 0
    assert aware.metrics["control_return_compliance"] == 1.0
    assert enforced.metrics["delegation_violation_count"] == 1
    assert enforced.metrics["mechanically_blocked_attempts"] == 1
