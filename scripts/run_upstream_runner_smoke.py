"""Run one real upstream Co-Gym Runner/Redis session as an integration check."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from aact import Message
from collaborative_gym.core import TeamMemberConfig
from collaborative_gym.nodes.commons import JsonObj
from collaborative_gym.runner import Runner
from redis import Redis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/upstream_runner_smoke"))
    parser.add_argument("--redis-url", default="redis://localhost:6379/15")
    args = parser.parse_args()
    venv_bin = Path(sys.executable).parent
    os.environ["PATH"] = f"{venv_bin}{os.pathsep}" + os.environ.get("PATH", "")
    redis_bin = shutil.which("redis-server")
    if not redis_bin:
        raise SystemExit("redis-server not found; install Redis to run this integration check")
    redis = subprocess.Popen(
        [redis_bin, "--port", "6379", "--save", "", "--appendonly", "no"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    runner = None
    session = f"smoke_{uuid.uuid4().hex[:10]}"
    env_uuid = f"env_{session}"
    try:
        time.sleep(0.8)
        client = Redis.from_url(args.redis_url)
        client.flushdb()
        runner = Runner(result_dir=str(args.output_dir), redis_url=args.redis_url)
        runner.start_session(
            session,
            str(Path("configs/delegation/stable_broad.toml").resolve()),
            [TeamMemberConfig(name="agent", type="gui_user", start_node_base_command="")],
            max_steps=30,
            disable_collaboration=True,
        )
        time.sleep(2.5)  # allow the genuine upstream node to subscribe before publishing
        actions = [
            "SEARCH()",
            "INSPECT(item_id=R000-1)",
            "INSPECT(item_id=R000-2)",
            "INSPECT(item_id=R000-3)",
            "COMPARE()",
            "DRAFT(item_id=R000-2)",
            "COMMIT(item_id=R000-2)",
        ]
        for action in actions:
            payload = Message[JsonObj](
                data=JsonObj(object={"role": "agent", "action": action})
            ).model_dump_json()
            client.publish(f"{env_uuid}/step", payload)
            time.sleep(0.35)
        result_path = args.output_dir / env_uuid / "task_performance.json"
        deadline = time.time() + 10
        while time.time() < deadline and not result_path.exists():
            time.sleep(0.2)
        summary = {
            "integration_type": "upstream Co-Gym Runner/Redis smoke session",
            "upstream_commit": "58972c0702412f293e303c3e49b6cc896db2467a",
            "session_uuid": session,
            "event_count": len(actions),
            "result_path": str(result_path),
            "scientific_result": False,
            "status": "passed" if result_path.exists() else "failed",
        }
        if result_path.exists():
            summary["task_performance"] = json.loads(result_path.read_text())
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "smoke_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        return 0 if result_path.exists() else 1
    finally:
        if runner is not None:
            runner.cleanup_subprocesses()
        redis.terminate()
        redis.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
