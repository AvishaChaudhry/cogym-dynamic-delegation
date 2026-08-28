"""Descriptive analysis and restrained publication-style figures."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .events import EpisodeTrace, EventType
from .metric_dictionary import metric_dictionary

SUMMARY_METRICS = (
    "task_performance",
    "collaborative_score",
    "attempted_delegation_violation_rate",
    "attempted_delegation_violation_count",
    "executed_delegation_violation_rate",
    "executed_delegation_violation_count",
    "unnecessary_confirmation_count",
    "required_confirmation_compliance",
    "revocation_response_steps",
    "control_return_compliance",
    "human_interruption_burden",
    "recovery_quality",
    "initiative_entropy",
    "delivery_rate",
)


def load_traces(episodes_dir: Path) -> list[EpisodeTrace]:
    return [EpisodeTrace.load(path) for path in sorted(episodes_dir.glob("*/episode.json"))]


def bootstrap_mean_ci(
    values: list[float], *, samples: int = 2000, seed: int = 1729
) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choice(values) for _ in values) for _ in range(samples))
    return means[int(0.025 * samples)], means[min(samples - 1, int(0.975 * samples))]


def descriptive_statistics(traces: Iterable[EpisodeTrace]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[EpisodeTrace]] = defaultdict(list)
    for trace in traces:
        groups[(trace.scenario["condition"], trace.metadata["agent_condition"])].append(trace)
    rows: list[dict[str, Any]] = []
    for (scenario, agent), grouped in sorted(groups.items()):
        for metric in SUMMARY_METRICS:
            values = [
                float(trace.metrics[metric])
                for trace in grouped
                if trace.metrics.get(metric) is not None
            ]
            if not values:
                continue
            ci_low, ci_high = bootstrap_mean_ci(values)
            rows.append(
                {
                    "scenario_condition": scenario,
                    "agent_condition": agent,
                    "metric": metric,
                    "n": len(values),
                    "mean": statistics.fmean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "bootstrap_95_ci_low": ci_low,
                    "bootstrap_95_ci_high": ci_high,
                }
            )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_analysis(traces: list[EpisodeTrace], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    statistics_rows = descriptive_statistics(traces)
    _write_csv(output_dir / "descriptive_statistics.csv", statistics_rows)
    raw_rows: list[dict[str, Any]] = []
    for trace in traces:
        raw_rows.append(
            {
                "episode_id": trace.episode_id,
                "scenario_condition": trace.scenario["condition"],
                "seed": trace.metadata["seed"],
                "agent_condition": trace.metadata["agent_condition"],
                **trace.metrics,
            }
        )
    _write_csv(output_dir / "episode_metrics.csv", raw_rows)
    failures = [
        {
            "episode_id": trace.episode_id,
            "error": trace.error,
            "delivered": trace.final_result.get("delivered"),
            "attempted_violation_count": trace.metrics.get("attempted_delegation_violation_count"),
            "executed_violation_count": trace.metrics.get("executed_delegation_violation_count"),
            "censored_revocation_response": trace.metrics.get("revocation_response_censored"),
        }
        for trace in traces
        if trace.error
        or not trace.final_result.get("delivered")
        or trace.metrics.get("attempted_delegation_violation_count", 0) > 0
        or trace.metrics.get("revocation_response_censored")
    ]
    (output_dir / "failure_cases.json").write_text(json.dumps(failures, indent=2) + "\n")
    (output_dir / "metric_dictionary.json").write_text(
        json.dumps(metric_dictionary(), indent=2, sort_keys=True) + "\n"
    )
    report = {
        "evaluation_type": "deterministic benchmark/mechanism validation",
        "scientific_scope": "mechanism validation only; not an LLM-agent evaluation or human-agent study",
        "llm_agent_evaluation": False,
        "human_study": False,
        "model_used": False,
        "n_episodes": len(traces),
        "models_used": sorted({trace.metadata["agent_model"] for trace in traces}),
        "bootstrap": {"samples": 2000, "seed": 1729, "method": "episode resampling percentile CI"},
        "significance_tests": "not performed",
        "failure_case_count": len(failures),
    }
    (output_dir / "analysis_manifest.json").write_text(json.dumps(report, indent=2) + "\n")


def _plot_style() -> None:
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
        }
    )


def _save(fig: Any, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f"{stem}.png", dpi=220)
    fig.savefig(output_dir / f"{stem}.pdf")


def figure_delegation_concept(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(9.6, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    boxes = [
        (
            0.2,
            1.15,
            2.45,
            1.65,
            "CAPABILITY",
            "Technically available actions\nSEARCH · DRAFT · COMMIT",
        ),
        (
            3.25,
            1.15,
            3.0,
            1.65,
            "CURRENT DELEGATION",
            "Autonomous · Ask first\nProhibited · Versioned",
        ),
        (6.85, 1.15, 2.95, 1.65, "BEHAVIOR", "ACT · ASK · WAIT\nSTOP / RETURN CONTROL"),
    ]
    for x, y, width, height, title, body in boxes:
        patch = FancyBboxPatch(
            (x, y), width, height, boxstyle="round,pad=0.03", facecolor="white", edgecolor="#333333"
        )
        ax.add_patch(patch)
        ax.text(x + 0.15, y + 1.2, title, weight="bold", va="center", fontsize=9)
        ax.text(x + 0.15, y + 0.58, body, va="center", color="#333333", fontsize=8.5)
    ax.annotate(
        "",
        xy=(3.15, 1.97),
        xytext=(2.72, 1.97),
        arrowprops={"arrowstyle": "->", "color": "#555555"},
    )
    ax.annotate(
        "",
        xy=(6.75, 1.97),
        xytext=(6.32, 1.97),
        arrowprops={"arrowstyle": "->", "color": "#555555"},
    )
    ax.text(5, 3.35, "DelegationGym decision abstraction", ha="center", weight="bold", size=11)
    ax.text(
        5,
        0.48,
        "Capability does not imply current delegated authority.",
        ha="center",
        style="italic",
    )
    _save(fig, output_dir, "figure1_delegation_concept")
    plt.close(fig)


def _agent_label(value: str) -> str:
    return {
        "autonomous_task_completion_policy": "Autonomous task-completion policy",
        "prompt_only_policy_proxy": "Prompt-only policy proxy",
        "structured_delegation_policy": "Structured delegation policy",
        "runtime_enforced_ceiling_comparator": "Runtime-enforced ceiling comparator",
    }.get(value, value)


def figure_performance_violation(traces: list[EpisodeTrace], output_dir: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    colors = ["#222222", "#4C78A8", "#E45756", "#72B7B2"]
    agents = sorted({trace.metadata["agent_condition"] for trace in traces})
    for agent_index, (color, agent) in enumerate(zip(colors, agents, strict=True)):
        selected = [trace for trace in traces if trace.metadata["agent_condition"] == agent]
        jitter = (agent_index - (len(agents) - 1) / 2) * 0.0012
        ax.scatter(
            [trace.metrics["attempted_delegation_violation_rate"] + jitter for trace in selected],
            [trace.metrics["task_performance"] for trace in selected],
            s=22,
            alpha=0.52,
            color=color,
            label=_agent_label(agent),
        )
    ax.set(
        xlabel="Attempted delegation violation rate",
        ylabel="Task performance",
        title="Task utility and delegation compliance",
    )
    ax.legend(frameon=False, fontsize=8)
    ax.text(
        0.01,
        0.01,
        "Small horizontal offsets separate overlapping policy points.",
        transform=ax.transAxes,
        fontsize=7,
        color="#555555",
    )
    _save(fig, output_dir, "figure2_performance_vs_violation")
    plt.close(fig)


def figure_burden_compliance(traces: list[EpisodeTrace], output_dir: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    agents = sorted({trace.metadata["agent_condition"] for trace in traces})
    for index, agent in enumerate(agents):
        selected = [trace for trace in traces if trace.metadata["agent_condition"] == agent]
        x = statistics.fmean(trace.metrics["human_interruption_burden"] for trace in selected)
        y = statistics.fmean(1 - trace.metrics["attempted_delegation_violation_rate"] for trace in selected)
        display_x = x + (index - (len(agents) - 1) / 2) * 0.003
        ax.scatter(
            display_x,
            y,
            s=55,
            color=["#222222", "#4C78A8", "#E45756", "#72B7B2"][index],
        )
        ax.annotate(
            _agent_label(agent),
            (display_x, y),
            xytext=(5, 4 + (index % 2) * 8),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set(
        xlabel="Mean human interruption burden per episode",
        ylabel="Mean action-level compliance (1 − violation rate)",
        title="Interruption burden and compliance",
        ylim=(-0.03, 1.08),
    )
    ax.text(
        0.01,
        0.01,
        "Small horizontal offsets separate overlapping policy means.",
        transform=ax.transAxes,
        fontsize=7,
        color="#555555",
    )
    _save(fig, output_dir, "figure3_burden_vs_compliance")
    plt.close(fig)


def figure_revocation_behavior(traces: list[EpisodeTrace], output_dir: Path) -> None:
    import matplotlib.pyplot as plt

    revocations = [
        trace for trace in traces if trace.scenario["condition"] == "delegation_revocation"
    ]
    agents = sorted({trace.metadata["agent_condition"] for trace in revocations})
    behaviors = ["ACT violation", "ASK", "STOP", "Runtime block"]
    counts: dict[str, list[float]] = {}
    for agent in agents:
        selected = [trace for trace in revocations if trace.metadata["agent_condition"] == agent]
        totals = [0, 0, 0, 0]
        for trace in selected:
            update = next(
                i
                for i, event in enumerate(trace.events)
                if event.event_type == EventType.DELEGATION_UPDATE.value
            )
            after = trace.events[update + 1 :]
            totals[0] += sum(event.actor == "agent" and event.violation for event in after)
            totals[1] += sum(event.actor == "agent" and event.behavior == "ASK" for event in after)
            totals[2] += sum(
                event.actor == "agent" and event.behavior == "STOP_RETURN_CONTROL"
                for event in after
            )
            totals[3] += sum(
                event.actor == "runtime" and event.behavior == "ENFORCE_CEILING" for event in after
            )
        counts[agent] = [value / len(selected) for value in totals]
    fig, ax = plt.subplots(figsize=(7.2, 4.1))
    width = 0.18
    x = list(range(len(behaviors)))
    colors = ["#222222", "#4C78A8", "#E45756", "#72B7B2"]
    for index, agent in enumerate(agents):
        offsets = [value + (index - (len(agents) - 1) / 2) * width for value in x]
        ax.bar(offsets, counts[agent], width, label=_agent_label(agent), color=colors[index])
    ax.set_xticks(x, behaviors)
    ax.set(
        ylabel="Mean events per revocation episode", title="Behavior after delegation revocation"
    )
    ax.legend(frameon=False, fontsize=8)
    _save(fig, output_dir, "figure4_revocation_behavior")
    plt.close(fig)


def generate_figures(traces: list[EpisodeTrace], output_dir: Path) -> None:
    _plot_style()
    figure_delegation_concept(output_dir)
    figure_performance_violation(traces, output_dir)
    figure_burden_compliance(traces, output_dir)
    figure_revocation_behavior(traces, output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-dir", type=Path, default=Path("results/episodes"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/analysis"))
    parser.add_argument("--figures-dir", type=Path, default=Path("results/figures"))
    args = parser.parse_args(argv)
    traces = load_traces(args.episodes_dir)
    if not traces:
        parser.error(f"No episode.json files found under {args.episodes_dir}")
    write_analysis(traces, args.output_dir)
    generate_figures(traces, args.figures_dir)
    print(f"Analyzed {len(traces)} episodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
