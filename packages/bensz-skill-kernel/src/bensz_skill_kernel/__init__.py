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

__all__ = [
    "CompletionError",
    "EventEnvelope",
    "EventLog",
    "IntegrityError",
    "InvalidTransition",
    "KernelError",
    "VALID_STATES",
    "reduce_events",
]

__version__ = "0.1.0"
