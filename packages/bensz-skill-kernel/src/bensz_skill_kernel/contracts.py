"""Small, domain-neutral hand-off objects shared by runtime adapters.

These objects intentionally describe facts and requirements only.  A Skill still
owns its domain terminology and phase graph; the kernel merely transports and
validates the common shape.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


RUNTIME_PROTOCOL_VERSION = "bensz-skill-runtime-v1"
EFFECT_STATUSES = frozenset(
    {"none", "prepared", "authorized", "applied", "reconciled", "unknown", "conflicted", "compensated"}
)


@dataclass(frozen=True)
class Subject:
    """A reference to the object a verifier is asked to inspect."""

    kind: str
    ref: str | None = None
    snapshot_hash: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Requirement:
    """One check requested by a Skill contract."""

    id: str
    verifier_id: str | None = None
    verifier_version: str | None = None
    required: bool = True
    phase: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Artifact:
    """A produced file or logical artifact, represented without its contents."""

    artifact_id: str
    path: str | None = None
    content_hash: str | None = None
    required: bool = False
    phase: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Effect:
    """An externally visible side effect tracked independently of lifecycle."""

    effect_id: str
    status: str = "none"
    idempotency_key: str | None = None
    authorized: bool = False
    actor: str | None = None
    delegator: str | None = None
    authorization_scope: tuple[str, ...] = ()
    approval_ref: str | None = None
    policy_version: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in EFFECT_STATUSES:
            raise ValueError(f"unsupported effect status: {self.status}")
        if self.status in {"applied", "reconciled"} and not self.authorized:
            raise ValueError("applied effects require explicit authorization")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Authorization:
    """Optional responsibility and approval chain attached to an execution."""

    actor: str
    delegator: str | None = None
    scope: tuple[str, ...] = ()
    approval_ref: str | None = None
    policy_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Contract:
    """A minimal Skill completion contract consumed by the kernel."""

    skill_id: str
    skill_version: str | None = None
    required_artifacts: tuple[str, ...] = ()
    required_phases: tuple[str, ...] = ()
    requirements: tuple[Requirement, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_version": self.skill_version,
            "required_artifacts": list(self.required_artifacts),
            "required_phases": list(self.required_phases),
            "requirements": [item.to_dict() for item in self.requirements],
            "metadata": dict(self.metadata),
        }
