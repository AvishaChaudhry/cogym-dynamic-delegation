"""Collaboration Trace Atlas and Outcome Twins diagnostic analysis."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import statistics
from pathlib import Path
from typing import Any

from .analysis import load_traces
from .events import EpisodeTrace, EventType

PROCESS_FEATURES = (
    "initiative_entropy",
    "agent_action_count",
    "human_action_count",
    "confirmation_requests",
    "interventions",
    "attempted_delegation_violations",
    "executed_delegation_violations",
    "delegation_changes",
    "post_revocation_agent_actions",
    "recovery_quality",
)


def fingerprint(trace: EpisodeTrace) -> dict[str, Any]:
    update_index = next(
        (
            i
            for i, event in enumerate(trace.events)
            if event.event_type == EventType.DELEGATION_UPDATE.value
        ),
        None,
    )
    post = trace.events[update_index + 1 :] if update_index is not None else []
    return {
        "episode_id": trace.episode_id,
        "scenario_condition": trace.scenario["condition"],
        "agent_condition": trace.metadata["agent_condition"],
        "seed": trace.metadata["seed"],
        "initiative_entropy": trace.metrics["initiative_entropy"],
        "agent_action_count": sum(event.actor == "agent" for event in trace.events),
        "human_action_count": sum(event.actor == "human" for event in trace.events),
        "confirmation_requests": trace.metrics["confirmation_requests"],
        "interventions": trace.metrics["human_halting_interventions"],
        "attempted_delegation_violations": trace.metrics["attempted_delegation_violation_count"],
        "executed_delegation_violations": trace.metrics["executed_delegation_violation_count"],
        "delegation_changes": sum(
            event.event_type == EventType.DELEGATION_UPDATE.value for event in trace.events
        ),
        "post_revocation_agent_actions": sum(event.actor == "agent" for event in post),
        "recovery_quality": trace.metrics["recovery_quality"] or 0.0,
        "task_score": trace.metrics["task_performance"],
    }


def _z_scores(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    normalized: dict[str, list[float]] = {}
    for feature in PROCESS_FEATURES:
        values = [float(row[feature]) for row in rows]
        mean = statistics.fmean(values)
        std = statistics.pstdev(values)
        normalized[feature] = [(value - mean) / std if std else 0.0 for value in values]
    return normalized


def outcome_twins(
    traces: list[EpisodeTrace], *, outcome_epsilon: float = 0.01, limit: int = 20
) -> list[dict[str, Any]]:
    """Find similar-outcome pairs with large standardized process distance."""

    rows = [fingerprint(trace) for trace in traces]
    normalized = _z_scores(rows)
    pairs: list[dict[str, Any]] = []
    for left, right in itertools.combinations(range(len(rows)), 2):
        first, second = rows[left], rows[right]
        outcome_delta = abs(float(first["task_score"]) - float(second["task_score"]))
        if outcome_delta > outcome_epsilon:
            continue
        distance = math.sqrt(
            sum(
                (normalized[feature][left] - normalized[feature][right]) ** 2
                for feature in PROCESS_FEATURES
            )
        )
        pairs.append(
            {
                "left_episode_id": first["episode_id"],
                "right_episode_id": second["episode_id"],
                "outcome_delta": outcome_delta,
                "process_distance": distance,
                "left_fingerprint": first,
                "right_fingerprint": second,
            }
        )
    return sorted(pairs, key=lambda pair: (-pair["process_distance"], pair["left_episode_id"]))[
        :limit
    ]


def _canonical_rows(traces: list[EpisodeTrace]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trace in traces:
        for event in trace.events:
            rows.append(
                {
                    "episode_id": trace.episode_id,
                    "step": event.step,
                    "actor": event.actor,
                    "event_type": event.event_type,
                    "behavior": event.behavior,
                    "task_action": event.action_category,
                    "delegation_state_version": event.delegation_version,
                    "disposition": event.disposition,
                    "confirmation_required": event.confirmation_required,
                    "confirmation_obtained": event.confirmation_obtained,
                    "intervention": event.intervention,
                    "violation": event.violation,
                    "task_state_change": event.task_state_change,
                    "outcome": event.outcome,
                }
            )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]) if rows else [], lineterminator="\n"
        )
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def figure_outcome_twins(
    traces: list[EpisodeTrace], twins: list[dict[str, Any]], output_dir: Path
) -> None:
    if not twins:
        return
    import matplotlib.pyplot as plt

    by_id = {trace.episode_id: trace for trace in traces}
    pair = twins[0]
    selected = [by_id[pair["left_episode_id"]], by_id[pair["right_episode_id"]]]
    colors = {
        "agent": "#4C78A8",
        "human": "#E45756",
        "runtime": "#72B7B2",
        "environment": "#777777",
    }
    fig, axes = plt.subplots(2, 1, figsize=(9.2, 5.8), sharex=False)
    for ax, trace in zip(axes, selected, strict=True):
        events = [
            event for event in trace.events if event.event_type != EventType.EPISODE_END.value
        ]
        for event in events:
            marker = "x" if event.violation else "o"
            ax.scatter(event.step, 0, color=colors.get(event.actor, "#333333"), marker=marker, s=38)
            if event.event_type == EventType.CONFIRMATION_REQUEST.value:
                label = f"ASK {event.action_category}"
            elif event.event_type == EventType.CONFIRMATION_RESPONSE.value:
                label = f"APPROVE {event.action_category}"
            elif event.event_type == EventType.DELEGATION_UPDATE.value:
                label = "DELEGATION UPDATE"
            else:
                label = event.action_category or event.behavior
            ax.annotate(
                label,
                (event.step, 0),
                xytext=(0, 8),
                textcoords="offset points",
                rotation=35,
                ha="left",
                fontsize=7,
            )
        ax.axhline(0, color="#999999", linewidth=0.8)
        ax.set_yticks([])
        ax.set_ylim(-0.35, 0.55)
        ax.set_xlim(-0.3, max(event.step for event in events) + 0.55)
        ax.set_title(
            f"{trace.metadata['agent_condition']} — task score {trace.metrics['task_performance']:.3f}, "
            f"attempted violations {trace.metrics['attempted_delegation_violation_count']}; "
            f"executed {trace.metrics['executed_delegation_violation_count']}",
            loc="left",
            fontsize=9,
        )
    fig.suptitle(
        "Outcome Twins: similar task outcome, different collaboration process\n"
        f"standardized process distance = {pair['process_distance']:.2f}",
        fontsize=11,
        y=0.98,
    )
    axes[-1].set_xlabel("Canonical event step")
    fig.subplots_adjust(hspace=0.55, top=0.82)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "figure5_outcome_twins.png", dpi=220, bbox_inches="tight")
    fig.savefig(output_dir / "figure5_outcome_twins.pdf", bbox_inches="tight")
    plt.close(fig)


def build_atlas(
    episodes_dir: Path, output_dir: Path, figures_dir: Path, epsilon: float
) -> dict[str, Any]:
    traces = load_traces(episodes_dir)
    if not traces:
        raise ValueError(f"No episode traces found under {episodes_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    fingerprints = [fingerprint(trace) for trace in traces]
    twins = outcome_twins(traces, outcome_epsilon=epsilon)
    _write_csv(output_dir / "canonical_events.csv", _canonical_rows(traces))
    _write_csv(output_dir / "fingerprints.csv", fingerprints)
    (output_dir / "outcome_twins.json").write_text(
        json.dumps(
            {
                "status": "diagnostic analysis; not a validated scientific metric",
                "outcome_epsilon": epsilon,
                "normalization": "z-score over predeclared process features",
                "process_features": PROCESS_FEATURES,
                "pairs": twins,
            },
            indent=2,
        )
        + "\n"
    )
    figure_outcome_twins(traces, twins, figures_dir)
    manifest = {
        "episodes": len(traces),
        "outcome_twin_pairs": len(twins),
        "outcome_epsilon": epsilon,
    }
    (output_dir / "atlas_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-dir", type=Path, default=Path("results/episodes"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/atlas"))
    parser.add_argument("--figures-dir", type=Path, default=Path("results/figures"))
    parser.add_argument("--outcome-epsilon", type=float, default=0.01)
    args = parser.parse_args(argv)
    manifest = build_atlas(
        args.episodes_dir, args.output_dir, args.figures_dir, args.outcome_epsilon
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
