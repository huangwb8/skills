"""Minimal, append-only runtime kernel for Agent Skill task lifecycles."""

from .runtime import (
    CompletionError,
    EventEnvelope,
    EventLog,
    IntegrityError,
    InvalidTransition,
    KernelError,
    VALID_STATES,
    reduce_events,
)
from .verifiers import (
    Evidence,
    GateDecision,
    PackRegistry,
    VerifierPack,
    VerifierRunner,
    VerifierSpec,
    VerificationRequest,
    VerificationResult,
    apply_gate,
    normalize_result,
    snapshot_evidence,
)
from .builtins import MARKDOWN_SPEC, FILE_SPEC, build_builtin_registry, collect_markdown

__all__ = [
    "CompletionError",
    "EventEnvelope",
    "EventLog",
    "IntegrityError",
    "InvalidTransition",
    "KernelError",
    "VALID_STATES",
    "reduce_events",
    "Evidence",
    "GateDecision",
    "PackRegistry",
    "VerifierPack",
    "VerifierRunner",
    "VerifierSpec",
    "VerificationRequest",
    "VerificationResult",
    "apply_gate",
    "normalize_result",
    "snapshot_evidence",
    "MARKDOWN_SPEC",
    "FILE_SPEC",
    "build_builtin_registry",
    "collect_markdown",
]

__version__ = "0.4.0"
