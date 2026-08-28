# Verification record

Executed locally on 28 August 2026 (Asia/Kolkata) against repository commit source and
upstream Collaborative Gym commit `58972c0702412f293e303c3e49b6cc896db2467a`.

The dependency-light GitHub Actions workflow runs the base test, lint, and strict core
type-check suite on Python 3.11 and 3.12. The optional upstream Co-Gym Runner/Redis check is
recorded separately below because it requires the pinned upstream source and Redis; it is
an integration check, not part of the scientific result.

| Check | Actual status |
|---|---|
| Source compile | Passed |
| DelegationGym unit/minimal end-to-end tests | 12 passed; 1 optional upstream-source module skipped in the base run |
| CoEnv adapter integration against pinned upstream core/space/registry | 2 passed |
| Relevant upstream `test_collabskill.py` | 10 passed; 1 dataset-dependent test skipped because the optional released trajectory dataset was not downloaded |
| Ruff | Passed |
| Mypy (strict, core package; optional Co-Gym adapter excluded) | Passed |
| Full model-free evaluation | 500/500 episodes written |
| Analysis and five PNG/PDF figures | Generated successfully and visually inspected |
| Trace Atlas / Outcome Twins | 500 traces canonicalized; 20 top pairs exported |
| Genuine upstream Co-Gym Runner/Redis smoke | Passed; one `stable_broad` session completed through upstream `Runner` and Redis; integration check only, not a scientific result |
| Public-safety credential pattern scan | No credential/private-key pattern found |
| Fresh-clone reproducibility | Full 500-episode matrix rerun; `diff -qr` against checked-in episode artifacts returned no differences; clean-clone tests passed |

The upstream skip is not reported as a pass: reproducing released CollabSkill ratings needs
the optional `SALT-NLP/cogym-collabskill-trajectories` dataset. Upstream LLM-coded Initiative
and Controlled Autonomy analyses were not run because no model credentials were supplied.
