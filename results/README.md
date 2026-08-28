# Checked-in results

These artifacts were generated on 28 August 2026 by the commands in the repository README.
They contain **500 deterministic benchmark/mechanism-validation episodes**: 5 delegation
conditions × 25 seeds × 4 deterministic policy conditions. This is not an LLM-agent
evaluation or human-agent study; models used: none.

- `episodes/manifest.json`: complete run manifest and episode list.
- `episodes/*/episode.json`: scenario, transitions, canonical trace, result, and metrics.
- `analysis/episode_metrics.csv`: all per-episode metric distributions.
- `analysis/descriptive_statistics.csv`: per-cell N, mean, standard deviation, median,
  range, and fixed-seed 95% percentile bootstrap interval.
- `analysis/failure_cases.json`: all errors, undelivered tasks, violations, and censored
  revocation responses. It is deliberately broader than task failure.
- `analysis/metric_dictionary.json`: machine-readable numerator, denominator, range,
  interpretation, and edge-case definitions for every reported metric.
- `atlas/canonical_events.csv`: canonical event sequence for every episode.
- `atlas/fingerprints.csv`: compact process feature vectors.
- `atlas/outcome_twins.json`: top 20 similar-outcome/high-process-distance pairs.
- `figures/`: five figures in PNG and PDF.
- `website_safe/`: conservative public package with one real trace, clean table, Figure 2,
  Figure 3, revocation figure, Outcome Twins example, and exact-length summary/limitations.

No run was cherry-picked. No model result, participant, statistical significance, or
benchmark comparison is claimed. Re-running the commands overwrites matching seed/condition
episode directories and regenerates all aggregate artifacts deterministically.
