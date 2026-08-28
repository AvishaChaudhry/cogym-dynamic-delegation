# Method

## Study object

DelegationGym operationalizes a time-varying boundary between what an agent can do and what
the human has currently delegated. The checked-in run is a **deterministic benchmark/mechanism
validation**, not an LLM-agent evaluation or human-agent study.

## Task

Each seed creates five simulated catalog items with price, quality, and delivery time. A
team must select a resource below a seeded price ceiling. Search, inspection, comparison,
and drafting are reversible. Commitment records a consequential task decision but never
contacts an external system. Utility is:

`0.65 × quality/100 + 0.20 × (max_price-price)/max_price + 0.15 × (8-days)/7`

for an in-budget item, and zero otherwise. The deterministic planner inspects three items,
then ranks eligible inspected items. This intentionally bounded search produced some
undelivered cases and is not described as an optimal agent.

## Delegation manipulation

Every declared action is autonomous, approval-required, or prohibited at a given revision.
An optional returned-control set marks decisions explicitly taken back by the human.
Stable broad, stable constrained, expansion, revocation, and mixed/selective conditions are
constructed deterministically from a seed. Dynamic updates occur after a predeclared number
of agent decisions and are written as human `UPDATE_DELEGATION` events.

## Reference policies

- Autonomous task-completion policy ignores the delegation state.
- Prompt-only policy proxy consumes natural-language delegation text using a lightweight modal-rule
  parser. It is intentionally not given the structured policy.
- Structured delegation policy reads the structured current state and maps disposition to
  `ACT / ASK / WAIT / STOP`.
- Runtime-enforced ceiling comparator runs autonomous behavior while blocking inconsistent execution. Attempts
  remain in the trace as behavioral violations.

The scripted human applies scheduled updates, grants each valid confirmation request, and
completes a returned decision after the agent stops. Neither collaborator is an LLM.

## Executed design

- 5 delegation conditions
- 25 independent catalog seeds per condition
- 4 agent conditions
- 500 episodes total
- deterministic model-free policies
- fixed bootstrap seed 1729, 2,000 episode-resampling replicates
- no significance tests

Seeds are paired across agent conditions to keep task instances comparable. Complete
traces, not selected examples, are saved. The evaluation label is **deterministic
benchmark/mechanism validation**. The metric dictionary at
`results/analysis/metric_dictionary.json` defines exact numerators, denominators, ranges,
interpretations, and edge cases. Runtime-blocked actions are attempted violations but not
executed violations.

## Artifacts

Each episode directory contains `episode.json`, `event_log.jsonl`, `metrics.json`, and
`task_performance.json`. The top-level manifest records the evaluation type, policy and
model fields, seed list, conditions, upstream commit, and every episode ID. Analysis exports
raw distributions, grouped descriptive statistics, bootstrap intervals, and explicit
failure cases.
