"""Canonical event schema used by experiments and the Trace Atlas."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class EventType(StrEnum):
    TASK_ACTION = "task_action"
    CONFIRMATION_REQUEST = "confirmation_request"
    CONFIRMATION_RESPONSE = "confirmation_response"
    DELEGATION_UPDATE = "delegation_update"
    STOP_RETURN_CONTROL = "stop_return_control"
    WAIT = "wait"
    EPISODE_END = "episode_end"


@dataclass(slots=True)
class TrajectoryEvent:
    step: int
    actor: str
    event_type: str
    behavior: str
    delegation_version: int
    action_category: str | None = None
    disposition: str | None = None
    confirmation_required: bool = False
    confirmation_obtained: bool = False
    intervention: bool = False
    violation: bool = False
    attempted: bool = False
    executed: bool = False
    task_state_change: bool = False
    useful_state_preserved: bool = True
    outcome: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TrajectoryEvent:
        return cls(**dict(data))


@dataclass(slots=True)
class EpisodeTrace:
    episode_id: str
    metadata: dict[str, Any]
    scenario: dict[str, Any]
    events: list[TrajectoryEvent] = field(default_factory=list)
    final_result: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def append(self, event: TrajectoryEvent) -> None:
        expected = len(self.events)
        if event.step != expected:
            raise ValueError(f"Event step must be {expected}; got {event.step}")
        self.events.append(event)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "metadata": self.metadata,
            "scenario": self.scenario,
            "events": [event.to_dict() for event in self.events],
            "final_result": self.final_result,
            "metrics": self.metrics,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EpisodeTrace:
        return cls(
            episode_id=str(data["episode_id"]),
            metadata=dict(data["metadata"]),
            scenario=dict(data["scenario"]),
            events=[TrajectoryEvent.from_dict(item) for item in data.get("events", [])],
            final_result=dict(data.get("final_result", {})),
            metrics=dict(data.get("metrics", {})),
            error=data.get("error"),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")

    @classmethod
    def load(cls, path: Path) -> EpisodeTrace:
        return cls.from_dict(json.loads(path.read_text()))


def save_jsonl(events: Iterable[TrajectoryEvent], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in events))
