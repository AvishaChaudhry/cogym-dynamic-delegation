"""Integration test against a source checkout of the pinned Co-Gym revision."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest

upstream = os.environ.get("DELEGATION_GYM_UPSTREAM_SOURCE")
if not upstream:
    pytest.skip(
        "Set DELEGATION_GYM_UPSTREAM_SOURCE to a pinned Collaborative Gym checkout",
        allow_module_level=True,
    )

upstream_path = Path(upstream).resolve()
sys.path.insert(0, str(upstream_path))

# Avoid executing upstream's eager top-level imports; load the exact core/space/registry
# modules required by this adapter from their pinned source paths.
cogym_package = types.ModuleType("collaborative_gym")
cogym_package.__path__ = [str(upstream_path / "collaborative_gym")]
sys.modules["collaborative_gym"] = cogym_package

# The upstream envs/__init__.py eagerly imports every heavy task environment. The adapter
# itself requires only the registry, core, and spaces modules, so isolate that exact seam.
envs_package = types.ModuleType("collaborative_gym.envs")
envs_package.__path__ = [str(upstream_path / "collaborative_gym" / "envs")]
sys.modules["collaborative_gym.envs"] = envs_package

from collaborative_gym.core import CoEnv  # noqa: E402
from collaborative_gym.envs.registry import EnvFactory  # noqa: E402

from delegation_gym.cogym_env import CoDelegationTaskEnv  # noqa: E402


def test_environment_registered_and_completes_with_approval() -> None:
    assert issubclass(CoDelegationTaskEnv, CoEnv)
    assert EnvFactory.registry["delegation_task"] is CoDelegationTaskEnv
    env = EnvFactory.make(
        "delegation_task",
        team_members=["agent", "user"],
        env_id="integration-test",
        condition="stable_constrained",
        seed=0,
    )
    observation, info = env.reset()
    assert observation["public"]["delegation_state"]["version"] == 1
    assert info["seed"] == 0

    env.step("agent", "SEARCH()")
    item_ids = env.task.search_results[:3]  # type: ignore[attr-defined]
    for item_id in item_ids:
        _, reward, _, _, _ = env.step("agent", f"INSPECT(item_id={item_id})")
        assert reward == 0
    env.step("agent", "COMPARE()")
    selected = env.task.best_inspected()  # type: ignore[attr-defined]
    assert selected is not None
    env.step("agent", f"DRAFT(item_id={selected})")
    env.step("user", f"APPROVE_DELEGATION_ACTION(category=COMMIT,item_id={selected})")
    _, reward, terminated, _, info = env.step("agent", f"COMMIT(item_id={selected})")
    assert reward == 0
    assert terminated
    assert not info["delegation"]["violation"]
    assert env.evaluate_task_performance()["delivered"]


def test_explicit_revocation_is_observed_and_violation_logged() -> None:
    env = CoDelegationTaskEnv(
        team_members=["agent", "user"],
        env_id="revocation-test",
        condition="delegation_revocation",
        seed=1,
        runtime_enforced=True,
    )
    env.reset()
    _, reward, _, private, info = env.step(
        "user",
        "UPDATE_DELEGATION(version=2,autonomous=SEARCH|INSPECT|COMPARE|DRAFT,"
        "approval_required=,prohibited=COMMIT,returned_control=COMMIT)",
    )
    assert reward == 0
    assert not private
    assert info["delegation_update"]["after"]["returned_control"] == ["COMMIT"]
    assert env.get_obs()["public"]["delegation_state"]["version"] == 2
