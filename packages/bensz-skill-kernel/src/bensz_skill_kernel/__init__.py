"""Minimal, append-only runtime kernel for Agent Skill task lifecycles."""

from .runtime import (
    CompletionError,
    EventEnvelope,
    EventLog,
    IntegrityError,
    IdempotencyConflict,
    AuthorizationError,
    InvalidTransition,
    KernelError,
    VALID_STATES,
    reduce_events,
)
from .contracts import Artifact, Authorization, Contract, Effect, Requirement, Subject, RUNTIME_PROTOCOL_VERSION
from .verifiers import (
    Evidence,
    CombinedVerifierRegistry,
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
    builtin_verifier_root,
    normalize_result,
    snapshot_evidence,
    summarize_metrics,
    normalize_requirements,
)
from .builtins import CITATION_TRUTH_FIT_SPEC, FILE_SPEC, build_builtin_registry, collect_markdown
from .verifier_ids import validate_verifier_id
from .state_ids import validate_state_id
from .states import CombinedStateRegistry, FilesystemStateRegistry, META_STATE_PROTOCOL_VERSION, SKILL_STATE_DECLARATION_VERSION, SkillStateDeclaration, StateDefinition, StateDefinitionError, StateExecutionError, StateExecutionResult, StateTransitionError, StateMachine, build_builtin_state_registry, build_state_registry, check_state_invariants, execute_state
from .workspace import META_STATE_SNAPSHOT_VERSION, TaskWorkspace, WorkspaceError, WorkspacePaths, WORKSPACE_KINDS, WORKSPACE_PROTOCOL_VERSION, state_snapshot_hash, workspace_path

__all__ = [
    "CompletionError",
    "EventEnvelope",
    "EventLog",
    "IntegrityError",
    "IdempotencyConflict",
    "AuthorizationError",
    "InvalidTransition",
    "KernelError",
    "VALID_STATES",
    "reduce_events",
    "Artifact",
    "Authorization",
    "Contract",
    "Effect",
    "Requirement",
    "Subject",
    "RUNTIME_PROTOCOL_VERSION",
    "Evidence",
    "CombinedVerifierRegistry",
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
    "builtin_verifier_root",
    "normalize_result",
    "snapshot_evidence",
    "summarize_metrics",
    "normalize_requirements",
    "CITATION_TRUTH_FIT_SPEC",
    "FILE_SPEC",
    "build_builtin_registry",
    "collect_markdown",
    "validate_verifier_id",
    "validate_state_id",
    "FilesystemStateRegistry",
    "CombinedStateRegistry",
    "META_STATE_PROTOCOL_VERSION",
    "SKILL_STATE_DECLARATION_VERSION",
    "SkillStateDeclaration",
    "StateDefinition",
    "StateDefinitionError",
    "StateExecutionError",
    "StateExecutionResult",
    "StateTransitionError",
    "StateMachine",
    "build_builtin_state_registry",
    "build_state_registry",
    "execute_state",
    "check_state_invariants",
    "TaskWorkspace",
    "WorkspaceError",
    "WorkspacePaths",
    "WORKSPACE_KINDS",
    "WORKSPACE_PROTOCOL_VERSION",
    "META_STATE_SNAPSHOT_VERSION",
    "workspace_path",
    "state_snapshot_hash",
]

def _distribution_version() -> str:
    """Resolve the runtime version from the source metadata or installed wheel."""
    from pathlib import Path
    import importlib.metadata
    import re

    # During source-tree execution package metadata may describe an older
    # globally installed wheel.  Prefer the adjacent pyproject as the source
    # of truth in that case.
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
        match = re.search(r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]", text)
        if match:
            return match.group(1)
    except OSError:
        pass
    try:
        return importlib.metadata.version("bensz-skill-kernel")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


__version__ = _distribution_version()
