"""Explicit, versioned delegation state and transition validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class ActionDisposition(StrEnum):
    """The active human delegation boundary for an agent action category."""

    AUTONOMOUS = "autonomous"
    APPROVAL_REQUIRED = "approval_required"
    PROHIBITED = "prohibited"
    UNCLASSIFIED = "unclassified"


def _categories(values: Iterable[str]) -> frozenset[str]:
    normalized = frozenset(value.strip().upper() for value in values)
    if "" in normalized:
        raise ValueError("Action categories cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class DelegationUpdate:
    """A complete replacement state proposed by the human collaborator."""

    autonomous: frozenset[str]
    approval_required: frozenset[str]
    prohibited: frozenset[str]
    version: int
    returned_control: frozenset[str] = field(default_factory=frozenset)
    constraints: Mapping[str, Any] = field(default_factory=dict)
    reason: str = ""

    @classmethod
    def create(
        cls,
        *,
        autonomous: Iterable[str],
        approval_required: Iterable[str],
        prohibited: Iterable[str],
        version: int,
        returned_control: Iterable[str] = (),
        constraints: Mapping[str, Any] | None = None,
        reason: str = "",
    ) -> DelegationUpdate:
        return cls(
            autonomous=_categories(autonomous),
            approval_required=_categories(approval_required),
            prohibited=_categories(prohibited),
            version=version,
            returned_control=_categories(returned_control),
            constraints=MappingProxyType(dict(constraints or {})),
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class DelegationState:
    """The authority currently delegated to the agent, not its capabilities.

    Categories are mutually exclusive. Unlisted capabilities are deliberately
    classified as ``UNCLASSIFIED`` rather than silently treated as authorized.
    """

    autonomous: frozenset[str]
    approval_required: frozenset[str]
    prohibited: frozenset[str]
    version: int = 1
    returned_control: frozenset[str] = field(default_factory=frozenset)
    constraints: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("Delegation version must be at least 1")
        groups = [self.autonomous, self.approval_required, self.prohibited]
        overlaps = (groups[0] & groups[1]) | (groups[0] & groups[2]) | (groups[1] & groups[2])
        if overlaps:
            raise ValueError(f"Delegation categories overlap: {sorted(overlaps)}")
        classified = self.autonomous | self.approval_required | self.prohibited
        if not self.returned_control <= classified:
            unknown = self.returned_control - classified
            raise ValueError(f"Returned-control categories are unclassified: {sorted(unknown)}")
        if self.returned_control & self.autonomous:
            raise ValueError("Returned-control categories cannot remain autonomous")

    @classmethod
    def create(
        cls,
        *,
        autonomous: Iterable[str],
        approval_required: Iterable[str],
        prohibited: Iterable[str],
        version: int = 1,
        returned_control: Iterable[str] = (),
        constraints: Mapping[str, Any] | None = None,
    ) -> DelegationState:
        return cls(
            autonomous=_categories(autonomous),
            approval_required=_categories(approval_required),
            prohibited=_categories(prohibited),
            version=version,
            returned_control=_categories(returned_control),
            constraints=MappingProxyType(dict(constraints or {})),
        )

    @property
    def control_returned(self) -> bool:
        return bool(self.returned_control)

    @property
    def classified_actions(self) -> frozenset[str]:
        return self.autonomous | self.approval_required | self.prohibited

    def disposition(self, action_category: str) -> ActionDisposition:
        category = action_category.strip().upper()
        if category in self.autonomous:
            return ActionDisposition.AUTONOMOUS
        if category in self.approval_required:
            return ActionDisposition.APPROVAL_REQUIRED
        if category in self.prohibited:
            return ActionDisposition.PROHIBITED
        return ActionDisposition.UNCLASSIFIED

    def apply(self, update: DelegationUpdate) -> DelegationState:
        if update.version != self.version + 1:
            raise ValueError(
                f"Delegation update must advance exactly one version "
                f"({self.version} -> {self.version + 1}); got {update.version}"
            )
        candidate = DelegationState(
            autonomous=update.autonomous,
            approval_required=update.approval_required,
            prohibited=update.prohibited,
            version=update.version,
            returned_control=update.returned_control,
            constraints=MappingProxyType(dict(update.constraints)),
        )
        return replace(candidate)

    def to_dict(self) -> dict[str, Any]:
        return {
            "autonomous": sorted(self.autonomous),
            "approval_required": sorted(self.approval_required),
            "prohibited": sorted(self.prohibited),
            "version": self.version,
            "control_returned": self.control_returned,
            "returned_control": sorted(self.returned_control),
            "constraints": dict(self.constraints),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationState:
        return cls.create(
            autonomous=data.get("autonomous", ()),
            approval_required=data.get("approval_required", ()),
            prohibited=data.get("prohibited", ()),
            version=int(data.get("version", 1)),
            returned_control=data.get("returned_control", ()),
            constraints=data.get("constraints", {}),
        )
