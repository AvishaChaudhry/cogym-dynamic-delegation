import json
from pathlib import Path

from delegation_gym.agents import AgentCondition
from delegation_gym.atlas import build_atlas, outcome_twins
from delegation_gym.experiment import run_experiment
from delegation_gym.scenarios import ScenarioCondition


def test_minimal_experiment_and_atlas(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    args = (
        range(1),
        [ScenarioCondition.REVOCATION],
        [AgentCondition.AUTONOMOUS, AgentCondition.DELEGATION_AWARE],
    )
    first = run_experiment(first_dir, *args)
    second = run_experiment(second_dir, *args)
    assert [trace.to_dict() for trace in first] == [trace.to_dict() for trace in second]
    assert json.loads((first_dir / "manifest.json").read_text())["n_episodes"] == 2
    assert outcome_twins(first, outcome_epsilon=0.01)
    manifest = build_atlas(first_dir, tmp_path / "atlas", tmp_path / "figures", 0.01)
    assert manifest["episodes"] == 2
    assert (tmp_path / "figures" / "figure5_outcome_twins.png").exists()
