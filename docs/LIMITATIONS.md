# Limitations

- The checked-in evaluation uses scripted collaborators and deterministic reference policies.
  It is a **deterministic benchmark/mechanism validation**, not an LLM-agent evaluation or
  human-agent study.
- Simulated compliance does not establish human preferences, and the scripted human does
  not reproduce ambiguous, inconsistent, or evolving preference formation.
- No language model was evaluated. The results validate execution and instrumentation,
  not the delegation behavior of a deployed model.
- The environment operationalizes explicit delegation; it does not prove a universal
  theory of autonomy, control, or agency.
- Only one safe simulated resource-selection task family is implemented. More task
  families and divisions of labor are needed for external validity.
- Explicit statements may not capture ambiguous real-world intent, indirect cues,
  conflicting stakeholders, or context that changes without a formal update.
- Runtime enforcement and collaborative behavior are different constructs. A blocked
  violation demonstrates the ceiling, not agent understanding.
- The deterministic event-count Initiative Entropy and confirmation counts are compatible
  descriptive proxies, not the upstream LLM-coded process annotations. Running upstream
  annotations requires model credentials and was not attempted.
- Bootstrap intervals describe variation over these seeded task instances. They are not
  evidence about a broader population of humans, tasks, or language models.
- Outcome Twins is a diagnostic visualization dependent on its epsilon, declared features,
  and normalization. It is not a validated scientific metric.
- The planner inspects only three items, causing genuine undelivered cases when no inspected
  item is in budget. This bounded planner should not be read as an optimal task baseline.
- No real participants were recruited and no claims are made about causal human behavior.

Human preference formation remains unanswered. **DelegationGym makes a changing autonomy
boundary operational and measurable. It does not explain why a person chooses that
boundary.**
