"""Assemble a conservative, website-safe result package from checked-in artifacts."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = root / "results"
    out = source / "website_safe"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    traces = sorted((source / "episodes").glob("*/episode.json"))
    chosen = next(
        path
        for path in traces
        if "delegation_revocation" in path.parent.name
        and "structured_delegation_policy" in path.parent.name
    )
    (out / "episode_trace.json").write_text(chosen.read_text())
    shutil.copy2(chosen.parent / "event_log.jsonl", out / "episode_event_log.jsonl")

    rows = list(csv.DictReader((source / "analysis" / "descriptive_statistics.csv").open()))
    keep = (
        "executed_delegation_violation_rate",
        "human_interruption_burden",
        "attempted_delegation_violation_rate",
        "delivery_rate",
        "task_performance",
    )
    agents = sorted({row["agent_condition"] for row in rows})
    table = []
    for agent in agents:
        row = {"agent_condition": agent, "n": "125"}
        for metric in keep:
            matches = [r for r in rows if r["agent_condition"] == agent and r["metric"] == metric]
            row[f"mean_{metric}"] = (
                f"{sum(float(r['mean']) for r in matches) / len(matches):.6f}" if matches else "NA"
            )
        table.append(row)
    with (out / "result_table.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(table)
    (out / "result_table.json").write_text(json.dumps(table, indent=2) + "\n")
    for stem in (
        "figure2_performance_vs_violation",
        "figure3_burden_vs_compliance",
        "figure4_revocation_behavior",
    ):
        shutil.copy2(source / "figures" / f"{stem}.png", out / f"{stem}.png")
    twins = json.loads((source / "atlas" / "outcome_twins.json").read_text())
    (out / "outcome_twins_example.json").write_text(json.dumps(twins["pairs"][0], indent=2) + "\n")
    (out / "summary_100_words.txt").write_text(
        "Dynamic Delegation in Collaborative Gym is a working research prototype extending Collaborative Gym with an explicit, time-varying action-level delegation state. The checked-in 500-episode package is deterministic benchmark/mechanism validation, not an LLM-agent evaluation or human-agent study. Four credential-free reference policies run across five seeded conditions. Results show identical task utility and delivery, while violations, confirmation burden, and revocation responses differ. Runtime ceilings distinguish attempted from executed violations. The package includes a real trace, aggregate table, diagnostic figures, and an Outcome Twins example. No novelty claim, affiliation, causal human claim, or proprietary AIKMATRA/Gateway code is asserted for cautious public inspection today.\n"
    )
    (out / "limitations_100_words.txt").write_text(
        "This package does not evaluate a language model, recruited participant, or human preference. Policies and collaborators are deterministic scripts in one simulated resource-selection task. Utility currently depends on the final committed item, so confirmations, waiting, and blocked actions do not affect original task performance; equal outcomes therefore cannot establish universal delegation safety. The planner inspects only three catalog items, and undelivered cases are genuine but task-specific. Bootstrap intervals describe seeded-instance variation, not population uncertainty. Outcome Twins is diagnostic, not validated. The bounded-interaction variant is pre-specified and separate from the audited 500 episodes, pending independent future collection under its prospective protocol.\n"
    )
    summary_path = out / "summary_100_words.txt"
    summary_path.write_text(
        summary_path.read_text().replace("today.", "today only.")
    )
    (out / "status.txt").write_text("Working research prototype · deterministic validation\n")
    (out / "README.md").write_text(
        "# Website-safe result package\n\nThis package is limited to deterministic benchmark/mechanism validation. It contains one real checked-in episode trace, a clean aggregate table, Figure 2, Figure 3, the revocation figure, and one Outcome Twins example. It is not an LLM-agent evaluation or human-agent study.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
