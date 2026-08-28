# Analysis artifacts

`scripts/evaluate_delegation.py` writes per-episode distributions, grouped descriptive
statistics, fixed-seed percentile bootstrap intervals, and explicit failure cases.
`scripts/build_trace_atlas.py` writes canonical event rows, collaboration fingerprints,
and the Outcome Twins diagnostic. No significance test is run by default.

Generated outputs come from deterministic simulated collaborators unless an experiment
manifest explicitly says otherwise. They are not a human study.
