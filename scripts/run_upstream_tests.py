"""Run the pinned upstream CollabSkill tests without eager unrelated env imports."""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

import pytest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream_source", type=Path)
    args = parser.parse_args()
    source = args.upstream_source.resolve()
    package = types.ModuleType("collaborative_gym")
    package.__path__ = [str(source / "collaborative_gym")]
    sys.modules["collaborative_gym"] = package
    return pytest.main([str(source / "tests" / "test_collabskill.py"), "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
