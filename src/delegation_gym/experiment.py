"""Reproducible deterministic benchmark/mechanism-validation runner."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any

from .agents import AgentCondition, Behavior, DeterministicAgent, state_to_prompt
from .events import EpisodeTrace, EventType, TrajectoryEvent, save_jsonl
from .metrics import compute_metrics
from .scenarios import CORE_SCENARIO_CONDITIONS, Scenario, ScenarioCondition, build_scenario
from .state import ActionDisposition
from .task import ActionResult, DelegationTask

UPSTREAM_COMMIT = "58972c0702412f293e303c3e49b6cc896db2467a"
POLICY_VERSION = "deterministic-policy-v1"


def _event_from_result(
    trace: EpisodeTrace, actor: str, behavior: str, result: ActionResult, rationale: str = ""
) -> None:
    trace.append(
        TrajectoryEvent(
            step=len(trace.events),
            actor=actor,
            event_type=EventType.TASK_ACTION.value,
            behavior=behavior,
            delegation_version=trace.metadata["active_delegation_version"],
            action_category=result.category,
            disposition=result.disposition.value,
            confirmation_required=result.confirmation_required,
            confirmation_obtained=result.confirmation_obtained,
            violation=result.violation,
            attempted=result.attempted,
            executed=result.executed,
            task_state_change=result.task_state_change,
            outcome=result.outcome,
            details={**result.details, "rationale": rationale},
        )
    )


def _apply_transition(trace: EpisodeTrace, task: DelegationTask, scenario: Scenario) -> str:
    assert scenario.transition is not None
    before = task.delegation_state.to_dict()
    state = task.update_delegation(scenario.transition.update)
    trace.metadata["active_delegation_version"] = state.version
    trace.append(
        TrajectoryEvent(
            step=len(trace.events),
            actor="human",
            event_type=EventType.DELEGATION_UPDATE.value,
            behavior="UPDATE_DELEGATION",
            delegation_version=state.version,
            intervention=bool(state.returned_control),
            task_state_change=False,
            outcome="delegation_updated",
            details={
                "message": scenario.transition.message,
                "before": before,
                "after": state.to_dict(),
                "reason": scenario.transition.update.reason,
            },
        )
    )
    return scenario.transition.message


def run_episode(scenario: Scenario, condition: AgentCondition) -> EpisodeTrace:
    runtime_enforced = condition is AgentCondition.RUNTIME_ENFORCED
    task = DelegationTask(scenario, runtime_enforced=runtime_enforced)
    agent = DeterministicAgent(condition, scenario.initial_state)
    episode_id = f"{scenario.scenario_id}--{condition.value}"
    trace = EpisodeTrace(
        episode_id=episode_id,
        metadata={
            "evaluation_type": "deterministic benchmark/mechanism validation",
            "scientific_scope": "mechanism validation only; not an LLM-agent evaluation or human-agent study",
            "agent_condition": condition.value,
            "agent_model": "none",
            "agent_policy": POLICY_VERSION,
            "human_model": "none",
            "human_policy": "deterministic-scripted-collaborator-v1",
            "seed": scenario.seed,
            "python": platform.python_version(),
            "upstream_commit": UPSTREAM_COMMIT,
            "active_delegation_version": scenario.initial_state.version,
            "runtime_enforced": runtime_enforced,
        },
        scenario=scenario.to_dict(),
    )
    if condition is AgentCondition.PROMPT_ONLY:
        trace.metadata["delegation_input"] = state_to_prompt(scenario.initial_state)
    elif condition is AgentCondition.DELEGATION_AWARE:
        trace.metadata["delegation_input"] = scenario.initial_state.to_dict()
    else:
        trace.metadata["delegation_input"] = None

    agent_decisions = 0
    transitioned = False
    max_decisions = 20
    while task.committed is None and agent_decisions < max_decisions:
        if (
            scenario.transition is not None
            and not transitioned
            and agent_decisions >= scenario.transition.after_agent_decisions
        ):
            message = _apply_transition(trace, task, scenario)
            agent.observe_delegation_message(message)
            transitioned = True

        decision = agent.decide(task)
        agent_decisions += 1
        if decision.behavior is Behavior.ACT:
            result = task.attempt("agent", decision.category, item_id=decision.item_id)
            _event_from_result(trace, "agent", decision.behavior.value, result, decision.rationale)
            if runtime_enforced and result.violation and not result.executed:
                trace.append(
                    TrajectoryEvent(
                        step=len(trace.events),
                        actor="runtime",
                        event_type=EventType.STOP_RETURN_CONTROL.value,
                        behavior="ENFORCE_CEILING",
                        delegation_version=task.delegation_state.version,
                        action_category=decision.category,
                        outcome="agent_attempt_blocked",
                    )
                )
                human_result = task.attempt("human", decision.category, item_id=decision.item_id)
                _event_from_result(trace, "human", "ACT_AFTER_RUNTIME_BLOCK", human_result)
        elif decision.behavior is Behavior.ASK:
            unnecessary = (
                task.delegation_state.disposition(decision.category) is ActionDisposition.AUTONOMOUS
            )
            trace.append(
                TrajectoryEvent(
                    step=len(trace.events),
                    actor="agent",
                    event_type=EventType.CONFIRMATION_REQUEST.value,
                    behavior=decision.behavior.value,
                    delegation_version=task.delegation_state.version,
                    action_category=decision.category,
                    disposition=task.delegation_state.disposition(decision.category).value,
                    confirmation_required=True,
                    outcome="confirmation_requested",
                    details={"item_id": decision.item_id, "unnecessary": unnecessary},
                )
            )
            task.register_interaction(unnecessary_confirmation=unnecessary)
            task.approve(decision.category, decision.item_id)
            trace.append(
                TrajectoryEvent(
                    step=len(trace.events),
                    actor="human",
                    event_type=EventType.CONFIRMATION_RESPONSE.value,
                    behavior="APPROVE",
                    delegation_version=task.delegation_state.version,
                    action_category=decision.category,
                    confirmation_obtained=True,
                    outcome="approval_granted",
                    details={"item_id": decision.item_id},
                )
            )
            task.register_interaction()
        elif decision.behavior is Behavior.STOP:
            trace.append(
                TrajectoryEvent(
                    step=len(trace.events),
                    actor="agent",
                    event_type=EventType.STOP_RETURN_CONTROL.value,
                    behavior=decision.behavior.value,
                    delegation_version=task.delegation_state.version,
                    action_category=decision.category,
                    disposition=task.delegation_state.disposition(decision.category).value,
                    outcome="control_return_acknowledged",
                    details={"item_id": decision.item_id},
                )
            )
            task.register_interaction()
            human_result = task.attempt("human", decision.category, item_id=decision.item_id)
            _event_from_result(trace, "human", "ACT_AFTER_CONTROL_RETURN", human_result)
        else:
            trace.append(
                TrajectoryEvent(
                    step=len(trace.events),
                    actor="agent",
                    event_type=EventType.WAIT.value,
                    behavior=decision.behavior.value,
                    delegation_version=task.delegation_state.version,
                    action_category=decision.category,
                    disposition=task.delegation_state.disposition(decision.category).value,
                    outcome="waiting_for_human",
                )
            )
            break

    trace.final_result = task.evaluate_task_performance()
    trace.append(
        TrajectoryEvent(
            step=len(trace.events),
            actor="environment",
            event_type=EventType.EPISODE_END.value,
            behavior="END",
            delegation_version=task.delegation_state.version,
            outcome="delivered" if trace.final_result["delivered"] else "not_delivered",
            details=trace.final_result,
        )
    )
    trace.metrics = compute_metrics(trace)
    trace.metadata.pop("active_delegation_version", None)
    return trace


def run_experiment(
    output_dir: Path,
    seeds: range,
    conditions: list[ScenarioCondition],
    agents: list[AgentCondition],
) -> list[EpisodeTrace]:
    output_dir.mkdir(parents=True, exist_ok=True)
    traces: list[EpisodeTrace] = []
    manifest: dict[str, Any] = {
        "evaluation_type": "deterministic benchmark/mechanism validation",
        "scientific_scope": "mechanism validation only; not an LLM-agent evaluation or human-agent study",
        "llm_agent_evaluation": False,
        "human_study": False,
        "model_used": False,
        "agent_model": "none",
        "upstream_commit": UPSTREAM_COMMIT,
        "conditions": [condition.value for condition in conditions],
        "agent_conditions": [agent.value for agent in agents],
        "seeds": list(seeds),
        "episodes": [],
    }
    for scenario_condition in conditions:
        for seed in seeds:
            scenario = build_scenario(scenario_condition, seed)
            for agent_condition in agents:
                trace = run_episode(scenario, agent_condition)
                episode_dir = output_dir / trace.episode_id
                trace.save(episode_dir / "episode.json")
                save_jsonl(trace.events, episode_dir / "event_log.jsonl")
                (episode_dir / "task_performance.json").write_text(
                    json.dumps(trace.final_result, indent=2, sort_keys=True) + "\n"
                )
                (episode_dir / "metrics.json").write_text(
                    json.dumps(trace.metrics, indent=2, sort_keys=True) + "\n"
                )
                traces.append(trace)
                manifest["episodes"].append(trace.episode_id)
    manifest["n_episodes"] = len(traces)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return traces


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results/episodes"))
    parser.add_argument("--seeds", type=int, default=10, help="Seeds per scenario condition")
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=[condition.value for condition in AgentCondition],
        default=[condition.value for condition in AgentCondition],
    )
    args = parser.parse_args(argv)
    traces = run_experiment(
        args.output_dir,
        range(args.seeds),
        list(CORE_SCENARIO_CONDITIONS),
        [AgentCondition(value) for value in args.agents],
    )
    print(f"Wrote {len(traces)} episodes to {args.output_dir}")
    print("Models used: none (deterministic benchmark/mechanism validation; not an LLM-agent evaluation or human-agent study)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
