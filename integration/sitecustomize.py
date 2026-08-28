"""Keep the upstream package import focused during the Runner smoke test."""

from __future__ import annotations

import asyncio
import os
import sys
import types
from pathlib import Path

root = Path(os.environ["DELEGATION_GYM_ROOT"])
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
upstream = root / "upstream-collaborative-gym" / "collaborative_gym"
if str(root / "src") not in sys.path:
    sys.path.insert(0, str(root / "src"))

package = types.ModuleType("collaborative_gym")
package.__path__ = [str(upstream)]
sys.modules.setdefault("collaborative_gym", package)
for name in ("envs", "nodes"):
    module = types.ModuleType(f"collaborative_gym.{name}")
    module.__path__ = [str(upstream / name)]
    sys.modules.setdefault(f"collaborative_gym.{name}", module)

from collaborative_gym.envs.config import EnvArgs, EnvConfig  # noqa: E402
from collaborative_gym.envs.registry import EnvFactory  # noqa: E402

envs = sys.modules["collaborative_gym.envs"]
envs.EnvArgs = EnvArgs
envs.EnvConfig = EnvConfig
envs.EnvFactory = EnvFactory

import collaborative_gym.nodes.task_env  # noqa: E402,F401

import delegation_gym.cogym_env  # noqa: E402,F401
