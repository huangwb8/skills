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
    FilesystemVerifierRegistry,
    GateDecision,
    PackRegistry,
    VerifierPack,
    VerifierRunner,
    VerifierSpec,
    VerifierDefinition,
    VerifierRegistry,
    VerificationRequest,
    VerificationResult,
    apply_gate,
    normalize_result,
    snapshot_evidence,
)
from .builtins import CITATION_TRUTH_FIT_SPEC, FILE_SPEC, build_builtin_registry, collect_markdown
from .states import FilesystemStateRegistry, StateDefinition, StateDefinitionError, StateTransitionError, StateMachine, build_builtin_state_registry
from .workspace import TaskWorkspace, WorkspaceError, WorkspacePaths, WORKSPACE_KINDS, WORKSPACE_PROTOCOL_VERSION, workspace_path

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
    "FilesystemVerifierRegistry",
    "VerifierRegistry",
    "GateDecision",
    "PackRegistry",
    "VerifierPack",
    "VerifierRunner",
    "VerifierSpec",
    "VerifierDefinition",
    "VerificationRequest",
    "VerificationResult",
    "apply_gate",
    "normalize_result",
    "snapshot_evidence",
    "CITATION_TRUTH_FIT_SPEC",
    "FILE_SPEC",
    "build_builtin_registry",
    "collect_markdown",
    "FilesystemStateRegistry",
    "StateDefinition",
    "StateDefinitionError",
    "StateTransitionError",
    "StateMachine",
    "build_builtin_state_registry",
    "TaskWorkspace",
    "WorkspaceError",
    "WorkspacePaths",
    "WORKSPACE_KINDS",
    "WORKSPACE_PROTOCOL_VERSION",
    "workspace_path",
]

__version__ = "0.7.0"
