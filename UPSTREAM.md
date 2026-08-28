# Upstream relationship

DelegationGym is an independent extension of Collaborative Gym (Co-Gym):

- Repository: <https://github.com/SALT-NLP/collaborative-gym>
- Inspected commit: `58972c0702412f293e303c3e49b6cc896db2467a`
- Commit date: `2026-08-21T03:21:47+08:00`
- Commit subject: `Merge pull request #14 from SALT-NLP/collabskill`
- License: MIT

The commit was resolved from the upstream default branch on 28 August 2026 and is pinned in
the `cogym` optional dependency in `pyproject.toml`.

## Extension points inspected

- `collaborative_gym.core.CoEnv`: task lifecycle, shared/private observations, action
  validation, action-space export, and `evaluate_task_performance()`.
- `collaborative_gym.envs.registry.EnvFactory`: decorator-based environment registration
  and construction from `EnvConfig`.
- Existing travel, literature, tabular, lesson-planning, and computer-use environments:
  action-space conventions and task-specific evaluation.
- `collaborative_gym.nodes.task_env.TaskEnvNode`: Redis node lifecycle, public/private
  observation fan-out, collaboration actions, confirmation handling, event-log JSONL,
  step limits, and `task_performance.json` output.
- `collaborative_gym.runner.Runner`: process/session lifecycle and result-directory
  conventions.
- Simulated-user and collaborative-agent nodes plus the situational-planning demo agent:
  prompts, state flow, and teammate interaction.
- `collaborative_gym.eval.initiative_analysis`: LLM-coded initiative utterances and
  two-member entropy aggregation.
- `collaborative_gym.eval.controlled_autonomy`: effective confirmation and human halting
  message counts.
- `scripts/report_simulated_result.py`: Delivery Rate, task performance, and Collaborative
  Score (`1_delivered × task performance`).
- Frontend workbench structure and observation render types; no frontend fork was required
  for the dependency-light artifact.

DelegationGym does not copy or rewrite Co-Gym. Importing `delegation_gym.cogym_env`
registers the new `delegation_task` environment against upstream's `EnvFactory`. The local
deterministic runner exists so instrumentation and seeded experiments can be reproduced
without Redis, model credentials, or Co-Gym's broader dependency set.

