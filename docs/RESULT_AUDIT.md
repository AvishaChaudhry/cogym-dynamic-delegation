# Result audit

## Scope classification

The 500-episode matrix is a **deterministic benchmark/mechanism validation**. It runs four
credential-free, deterministic reference policies against five seeded scenario conditions
(25 seeds each). No language model is prompted or scored, and no human participants or
human-agent study were involved.

## Why task performance and delivery are identical

The equality across the four policy conditions is expected from the current environment
design, not a metric implementation error. All conditions share the same deterministic task
planner, catalog seed, utility function, and inspected-item limit. Delegation changes the
ACT/ASK/STOP trajectory and interruption burden, but the original task utility is computed
only from the final committed item; it has no cost for waiting, confirmations, rework, or
violating-and-being-blocked. The runtime comparator blocks an inconsistent agent action and
then has the scripted human execute that same action, preserving the final task state.

The 20 undelivered episodes are caused by the planner inspecting only three of five items and
waiting when none of those inspected items is within the price constraint. That condition is
paired across policy variants and is independent of delegation behavior. The matching results
therefore reflect a deterministic policy consequence and a task that exposes process/control
differences without exposing a utility/control trade-off. They are not evidence that
delegation strategy cannot affect utility in other tasks.

No results were altered to create separation. Attempted and executed violations are reported
separately: a runtime-ceiling block contributes to attempted violations, while its
`executed=false` event contributes zero executed violations.

## Follow-up design

The pre-specified `bounded_interaction` scenario variant (see `docs/PROSPECTIVE_PROTOCOL.md`) is
implemented but excluded from the original 500-episode claims. It adds a fixed interaction
budget, a small declared cost for unnecessary confirmation, and rework after an executed
violation. These mechanisms can make inappropriate collaboration affect utility naturally;
the variant is a prospective test, not a tuned replacement for the audited benchmark.
