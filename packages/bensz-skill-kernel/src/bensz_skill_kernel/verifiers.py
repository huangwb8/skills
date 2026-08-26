"""Offline Verifier Pack contracts and runner.

The module deliberately keeps domain rules outside the kernel.  Packs provide
small rule/prompt callables; the runner only freezes evidence, records versions,
normalises results and applies the gate policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol

VERDICTS = frozenset({"pass", "fail", "uncertain", "unchecked", "error", "timed_out", "skipped"})
EXECUTION_STATUSES = frozenset({"completed", "unchecked", "error", "timed_out", "skipped"})
MODES = frozenset({"rule", "prompt", "hybrid", "human"})


def builtin_verifier_root() -> Path:
    """Return the verifier assets bundled with this installed Python package."""
    return Path(__file__).with_name("verifiers")


def _version_key(version: str) -> tuple[tuple[int, Any], ...]:
    """Sort semantic-ish versions numerically while tolerating labels."""
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in re.split(r"[.-]", version))


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the deliberately small, dependency-free VERIFIER.md header."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, text
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip("\"'")
        metadata[key.strip()] = value
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    return metadata, body


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Evidence:
    ref: str
    source_type: str
    content: Any
    collected_at: str = field(default_factory=_now)
    freshness: str | None = None
    collection_method: str = "local"
    redacted: bool = True
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash:
            object.__setattr__(self, "content_hash", _hash(self.content))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationRequest:
    subject: Mapping[str, Any]
    requirements: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    request_id: str = "request"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerifierSpec:
    verifier_id: str
    version: str
    mode: str
    capabilities: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    uncertainty_policy: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"unsupported verifier mode: {self.mode}")


@dataclass(frozen=True)
class VerifierDefinition:
    """A verifier discovered from a directory containing ``VERIFIER.md``.

    The kernel owns this shape and the stdio protocol only; the Markdown body
    and optional entrypoint own the actual verification method.
    """

    verifier_id: str
    version: str
    path: Path
    instructions: str
    description: str = ""
    entrypoint: str | None = None
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_directory(cls, path: str | os.PathLike[str]) -> "VerifierDefinition":
        root = Path(path).expanduser().resolve()
        document = root / "VERIFIER.md"
        if not document.is_file():
            raise ValueError(f"verifier contract not found: {document}")
        fields, instructions = _parse_frontmatter(document.read_text(encoding="utf-8"))
        verifier_id = fields.get("id") or fields.get("verifier_id")
        version = fields.get("version")
        if not verifier_id or not version:
            raise ValueError(f"VERIFIER.md requires id and version: {document}")
        entrypoint = fields.get("entrypoint") or fields.get("script")
        if entrypoint:
            candidate = (root / entrypoint).resolve()
            if root not in candidate.parents or not candidate.is_file():
                raise ValueError(f"entrypoint must be a file inside verifier directory: {entrypoint}")
            entrypoint = str(candidate.relative_to(root))
        tags = tuple(item.strip() for item in fields.get("tags", "").split(",") if item.strip())
        reserved = {"id", "verifier_id", "version", "description", "entrypoint", "script", "tags"}
        metadata = {key: value for key, value in fields.items() if key not in reserved}
        return cls(verifier_id, version, root, instructions, fields.get("description", ""), entrypoint, tags, metadata)

    @property
    def spec(self) -> VerifierSpec:
        return VerifierSpec(
            verifier_id=self.verifier_id,
            version=self.version,
            mode="rule" if self.entrypoint else "human",
            tags=self.tags,
            metadata={"description": self.description, "path": str(self.path), "entrypoint": self.entrypoint, **dict(self.metadata)},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_id": self.verifier_id,
            "version": self.version,
            "description": self.description,
            "tags": list(self.tags),
            "entrypoint": self.entrypoint,
            "instructions": self.instructions,
            "metadata": dict(self.metadata),
        }


class FilesystemVerifierRegistry:
    """Discover and execute directory-based verifier contracts."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root).expanduser().resolve()
        self._definitions: dict[tuple[str, str], VerifierDefinition] = {}
        self.reload()

    def reload(self) -> None:
        self._definitions.clear()
        if not self.root.is_dir():
            return
        for child in sorted(self.root.iterdir(), key=lambda item: item.name):
            if not child.is_dir() or not (child / "VERIFIER.md").is_file():
                continue
            definition = VerifierDefinition.from_directory(child)
            key = (definition.verifier_id, definition.version)
            if key in self._definitions:
                raise ValueError(f"duplicate verifier: {definition.verifier_id}@{definition.version}")
            self._definitions[key] = definition

    def resolve(self, verifier_id: str, version: str | None = None) -> VerifierDefinition:
        if version:
            try:
                return self._definitions[(verifier_id, version)]
            except KeyError as exc:
                raise KeyError(f"verifier not found: {verifier_id}@{version}") from exc
        candidates = [item for (identifier, _), item in self._definitions.items() if identifier == verifier_id]
        if not candidates:
            raise KeyError(f"verifier not found: {verifier_id}")
        return sorted(candidates, key=lambda item: _version_key(item.version))[-1]

    def definitions(self, *, tag: str | None = None) -> tuple[VerifierDefinition, ...]:
        items = tuple(self._definitions.values())
        if tag:
            items = tuple(item for item in items if tag in item.tags)
        return tuple(sorted(items, key=lambda item: (item.verifier_id, item.version)))

    def specs(self, *, tag: str | None = None) -> tuple[VerifierSpec, ...]:
        return tuple(item.spec for item in self.definitions(tag=tag))

    def describe(self, verifier_id: str, version: str | None = None) -> VerifierDefinition:
        return self.resolve(verifier_id, version)

    def run(self, verifier_id: str, request: Mapping[str, Any] | VerificationRequest, *, version: str | None = None, timeout: int = 30) -> dict[str, Any]:
        if isinstance(request, VerificationRequest):
            request = {
                "request_id": request.request_id,
                "subject": dict(request.subject),
                "requirements": list(request.requirements),
                "evidence": [item.to_dict() for item in request.evidence],
                "context": dict(request.context),
            }
        definition = self.resolve(verifier_id, version)
        base = {"verifier_id": definition.verifier_id, "verifier_version": definition.version, "evidence_refs": tuple(request.get("evidence_refs", ())), "request_id": request.get("request_id")}
        if not definition.entrypoint:
            return {**base, "execution_status": "unchecked", "verdict": "unchecked", "uncertainty_reason": "instruction-only verifier; follow VERIFIER.md manually"}
        command = [sys.executable, str(definition.path / definition.entrypoint)]
        try:
            completed = subprocess.run(command, input=json.dumps(dict(request), ensure_ascii=False), text=True, capture_output=True, cwd=definition.path, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {**base, "execution_status": "timed_out", "verdict": "timed_out", "uncertainty_reason": f"verifier timed out after {timeout}s"}
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"entrypoint exited with status {completed.returncode}"
            return {**base, "execution_status": "error", "verdict": "error", "uncertainty_reason": detail[:1000]}
        try:
            raw = json.loads(completed.stdout)
            if not isinstance(raw, Mapping):
                raise ValueError("verifier output must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            return {**base, "execution_status": "error", "verdict": "error", "uncertainty_reason": f"invalid verifier JSON: {exc}"}
        return {**normalize_result(raw, definition.spec, evidence_refs=base["evidence_refs"]).to_dict(), "request_id": request.get("request_id")}


# Short public name for callers that do not care about the storage backend.
VerifierRegistry = FilesystemVerifierRegistry


@dataclass(frozen=True)
class VerificationResult:
    verifier_id: str
    verifier_version: str
    execution_status: str
    verdict: str
    findings: tuple[Mapping[str, Any], ...] = ()
    facts: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    confidence: float | None = None
    uncertainty_reason: str | None = None
    model_or_engine: str | None = None
    duration_ms: int | None = None

    def __post_init__(self) -> None:
        if self.execution_status not in EXECUTION_STATUSES:
            raise ValueError(f"invalid execution_status: {self.execution_status}")
        if self.verdict not in VERDICTS:
            raise ValueError(f"invalid verdict: {self.verdict}")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateDecision:
    decision: str
    reason: str
    result_refs: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuleCallable(Protocol):
    def __call__(self, request: VerificationRequest, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]: ...


class PromptCallable(Protocol):
    def __call__(self, request: VerificationRequest, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class VerifierPack:
    spec: VerifierSpec
    rules: tuple[tuple[str, RuleCallable], ...] = ()
    prompts: tuple[tuple[str, PromptCallable], ...] = ()
    calibration_set_ref: str | None = None


class PackRegistry:
    """Version-aware registry; registering a new pack never changes the runner."""

    def __init__(self) -> None:
        self._packs: dict[tuple[str, str], VerifierPack] = {}

    def register(self, pack: VerifierPack) -> None:
        key = (pack.spec.verifier_id, pack.spec.version)
        if key in self._packs:
            raise ValueError(f"pack already registered: {key[0]}@{key[1]}")
        self._packs[key] = pack

    def resolve(self, verifier_id: str, version: str | None = None) -> VerifierPack:
        if version:
            try:
                return self._packs[(verifier_id, version)]
            except KeyError as exc:
                raise KeyError(f"pack not found: {verifier_id}@{version}") from exc
        candidates = [p for (identifier, _), p in self._packs.items() if identifier == verifier_id]
        if not candidates:
            raise KeyError(f"pack not found: {verifier_id}")
        return sorted(candidates, key=lambda p: p.spec.version)[-1]

    def specs(self, *, tag: str | None = None) -> tuple[VerifierSpec, ...]:
        """Return a deterministic catalog view, optionally filtered by tag."""
        specs = [pack.spec for pack in self._packs.values()]
        if tag:
            specs = [spec for spec in specs if tag in spec.tags]
        return tuple(sorted(specs, key=lambda spec: (spec.verifier_id, spec.version)))

    def describe(self, verifier_id: str, version: str | None = None) -> VerifierSpec:
        return self.resolve(verifier_id, version).spec


def snapshot_evidence(items: Iterable[Evidence | Mapping[str, Any]]) -> tuple[Evidence, ...]:
    """Freeze and normalise evidence without exposing mutable source objects."""
    frozen: list[Evidence] = []
    for item in items:
        if isinstance(item, Evidence):
            frozen.append(item)
        else:
            data = dict(item)
            frozen.append(Evidence(ref=str(data["ref"]), source_type=str(data.get("source_type", "unknown")), content=data.get("content"), freshness=data.get("freshness"), collection_method=str(data.get("collection_method", "local")), redacted=bool(data.get("redacted", True))))
    return tuple(frozen)


def normalize_result(raw: Mapping[str, Any], spec: VerifierSpec, *, evidence_refs: Iterable[str] = ()) -> VerificationResult:
    """Validate the common output schema and turn malformed provider output into unchecked."""
    try:
        execution = str(raw.get("execution_status", "completed"))
        verdict = str(raw["verdict"])
        if execution not in EXECUTION_STATUSES or verdict not in VERDICTS:
            raise ValueError("invalid status or verdict")
        refs = tuple(raw.get("evidence_refs", evidence_refs))
        return VerificationResult(verifier_id=spec.verifier_id, verifier_version=spec.version, execution_status=execution, verdict=verdict, findings=tuple(raw.get("findings", ())), facts=dict(raw.get("facts", {})), evidence_refs=refs, confidence=raw.get("confidence"), uncertainty_reason=raw.get("uncertainty_reason"), model_or_engine=raw.get("model_or_engine"), duration_ms=raw.get("duration_ms"))
    except (KeyError, TypeError, ValueError):
        return VerificationResult(verifier_id=spec.verifier_id, verifier_version=spec.version, execution_status="unchecked", verdict="unchecked", uncertainty_reason="invalid verifier output", evidence_refs=tuple(evidence_refs))


def apply_gate(results: Iterable[VerificationResult], *, required: bool = True) -> GateDecision:
    """Apply conservative gate semantics; deterministic failures cannot be averaged away."""
    items = tuple(results)
    refs = tuple(f"{r.verifier_id}@{r.verifier_version}" for r in items)
    if not items:
        return GateDecision("wait", "no verification result", refs, ("missing_result",))
    failures = [r for r in items if r.verdict in {"fail", "error", "timed_out"}]
    unknown = [r for r in items if r.verdict in {"unchecked", "uncertain"}]
    if failures and required:
        return GateDecision("reject", "required verifier failure", refs, tuple(r.verifier_id for r in failures))
    if unknown:
        return GateDecision("manual_review", "verification gap or semantic uncertainty", refs, tuple(r.verifier_id for r in unknown))
    if failures:
        return GateDecision("allow_with_warnings", "optional verifier failure", refs, tuple(r.verifier_id for r in failures))
    return GateDecision("allow", "all required verifiers passed", refs)


class VerifierRunner:
    def __init__(self, registry: PackRegistry):
        self.registry = registry

    def run(self, request: VerificationRequest, verifier_id: str, *, version: str | None = None) -> tuple[tuple[VerificationResult, ...], GateDecision]:
        pack = self.registry.resolve(verifier_id, version)
        evidence = {item.ref: item for item in snapshot_evidence(request.evidence)}
        missing = [ref for ref in pack.spec.evidence_requirements if ref not in evidence]
        if missing:
            result = VerificationResult(pack.spec.verifier_id, pack.spec.version, "unchecked", "unchecked", uncertainty_reason="missing required evidence: " + ", ".join(missing), evidence_refs=tuple(evidence))
            return (result,), apply_gate((result,))
        results: list[VerificationResult] = []
        components = list(pack.rules) + list(pack.prompts)
        for component_id, component in components:
            try:
                raw = component(request, evidence)
                raw = {**dict(raw), "facts": {**dict(raw.get("facts", {})), "component": component_id}}
            except TimeoutError:
                raw = {"execution_status": "timed_out", "verdict": "timed_out", "uncertainty_reason": "provider timeout"}
            except Exception as exc:  # provider failures are data, not runner crashes
                raw = {"execution_status": "error", "verdict": "error", "uncertainty_reason": str(exc)}
            results.append(normalize_result(raw, pack.spec, evidence_refs=tuple(evidence)))
        return tuple(results), apply_gate(results)
