"""Offline Verifier Pack contracts and runner.

The module deliberately keeps domain rules outside the kernel.  Packs provide
small rule/prompt callables; the runner only freezes evidence, records versions,
normalises results and applies the gate policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol

from .packs import load_pack_entries, resolve_entrypoint, run_stdio, version_key as _version_key
from .verifier_ids import parse_aliases, validate_verifier_id

VERDICTS = frozenset({"pass", "fail", "uncertain", "unchecked", "error", "timed_out", "skipped"})
EXECUTION_STATUSES = frozenset({"completed", "unchecked", "error", "timed_out", "skipped"})
MODES = frozenset({"rule", "prompt", "hybrid", "human"})
ASSURANCE_TIERS = frozenset({"deterministic", "mixed", "llm_judge", "human"})
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def builtin_verifier_root() -> Path:
    """Return the verifier assets bundled with this installed Python package."""
    return Path(__file__).with_name("verifiers")


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
    protocol: str = "bensz-verification-v1"

    def __post_init__(self) -> None:
        if not isinstance(self.subject, Mapping) or not isinstance(self.context, Mapping):
            raise TypeError("subject and context must be objects")
        if self.protocol != "bensz-verification-v1":
            raise ValueError("unsupported verification protocol")

    def to_dict(self) -> dict[str, Any]:
        return {"protocol": self.protocol, "request_id": self.request_id, "subject": dict(self.subject), "requirements": list(self.requirements), "evidence": [item.to_dict() for item in self.evidence], "context": dict(self.context)}


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
    aliases: tuple[str, ...] = ()
    subject_kinds: tuple[str, ...] = ()
    prompt_pack_ref: str | None = None
    rule_pack_ref: str | None = None
    calibration_set_ref: str | None = None
    classification: str = "domain"
    assurance_tier: str = "deterministic"

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"unsupported verifier mode: {self.mode}")
        validate_verifier_id(self.verifier_id)
        if self.assurance_tier not in ASSURANCE_TIERS:
            raise ValueError(f"unsupported assurance tier: {self.assurance_tier}")
        if self.verifier_id in self.aliases or len(set(self.aliases)) != len(self.aliases):
            raise ValueError("verifier aliases must be unique and differ from the canonical ID")


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
    aliases: tuple[str, ...] = ()
    classification: str = "domain"
    assurance_tier: str = "deterministic"

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
        try:
            validate_verifier_id(verifier_id)
        except ValueError as exc:
            raise ValueError(f"canonical verifier ID required: {verifier_id}") from exc
        entrypoint = fields.get("entrypoint") or fields.get("script")
        if entrypoint:
            entrypoint = resolve_entrypoint(root, entrypoint, label="verifier")
        tags = tuple(item.strip() for item in fields.get("tags", "").split(",") if item.strip())
        aliases = parse_aliases(fields.get("aliases"))
        if verifier_id in aliases:
            raise ValueError("verifier aliases must differ from the canonical ID")
        assurance_tier = fields.get("assurance_tier", "deterministic")
        reserved = {"id", "verifier_id", "version", "description", "entrypoint", "script", "tags", "aliases", "assurance_tier"}
        metadata = {key: value for key, value in fields.items() if key not in reserved}
        return cls(verifier_id, version, root, instructions, fields.get("description", ""), entrypoint, tags, metadata, aliases, fields.get("classification", "domain"), assurance_tier)

    @classmethod
    def from_indexed_directory(cls, path: str | os.PathLike[str], entry: Mapping[str, Any]) -> "VerifierDefinition":
        root = Path(path).expanduser().resolve()
        document = (root / str(entry.get("contract", "VERIFIER.md"))).resolve()
        if root not in document.parents or not document.is_file():
            raise ValueError(f"indexed verifier contract must stay inside its directory: {document}")
        verifier_id, version = str(entry.get("id", "")), str(entry.get("version", ""))
        validate_verifier_id(verifier_id)
        if not version:
            raise ValueError(f"indexed verifier requires version: {root}")
        entrypoint = resolve_entrypoint(root, entry.get("entrypoint"), label="verifier")
        aliases = parse_aliases(",".join(str(item) for item in entry.get("aliases", ())))
        return cls(
            verifier_id=verifier_id,
            version=version,
            path=root,
            instructions=document.read_text(encoding="utf-8").strip(),
            description=str(entry.get("description", "")),
            entrypoint=str(entrypoint) if entrypoint else None,
            tags=tuple(str(item) for item in entry.get("tags", ())),
            metadata={"index": dict(entry), **{key: entry[key] for key in ("subject_kinds", "prompt_pack_ref", "rule_pack_ref", "calibration_set_ref") if key in entry}},
            aliases=aliases,
            classification=str(entry.get("classification", "domain")),
            assurance_tier=str(entry.get("assurance_tier", "deterministic")),
        )

    @property
    def spec(self) -> VerifierSpec:
        return VerifierSpec(
            verifier_id=self.verifier_id,
            version=self.version,
            mode="rule" if self.entrypoint else "human",
            tags=self.tags,
            aliases=self.aliases,
            subject_kinds=tuple(item.strip() for item in str(self.metadata.get("subject_kinds", "")).split(",") if item.strip()),
            prompt_pack_ref=self.metadata.get("prompt_pack_ref"),
            rule_pack_ref=self.metadata.get("rule_pack_ref"),
            calibration_set_ref=self.metadata.get("calibration_set_ref"),
            classification=self.classification,
            assurance_tier=self.assurance_tier,
            metadata={"description": self.description, "path": str(self.path), "entrypoint": self.entrypoint, **dict(self.metadata)},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_id": self.verifier_id,
            "version": self.version,
            "description": self.description,
            "tags": list(self.tags),
            "entrypoint": self.entrypoint,
            "aliases": list(self.aliases),
            "subject_kinds": list(self.spec.subject_kinds),
            "prompt_pack_ref": self.spec.prompt_pack_ref,
            "rule_pack_ref": self.spec.rule_pack_ref,
            "calibration_set_ref": self.spec.calibration_set_ref,
            "instructions": self.instructions,
            "metadata": dict(self.metadata),
            "classification": self.classification,
            "assurance_tier": self.assurance_tier,
        }


class FilesystemVerifierRegistry:
    """Discover and execute directory-based verifier contracts."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root).expanduser().resolve()
        self._definitions: dict[tuple[str, str], VerifierDefinition] = {}
        self._aliases: dict[tuple[str, str], tuple[str, str]] = {}
        self.reload()

    def reload(self) -> None:
        self._definitions.clear()
        self._aliases.clear()
        if not self.root.is_dir():
            return
        indexed = load_pack_entries(
            self.root,
            package_kind="verifier",
            contract_name="VERIFIER.md",
        )
        for contract_or_child, entry in indexed:
            # The shared loader returns the validated contract path for both
            # indexed and legacy roots; the Verifier factory consumes its
            # containing package directory.
            child = contract_or_child.parent
            definition = VerifierDefinition.from_indexed_directory(child, entry) if entry else VerifierDefinition.from_directory(child)
            key = (definition.verifier_id, definition.version)
            if key in self._definitions:
                raise ValueError(f"duplicate verifier: {definition.verifier_id}@{definition.version}")
            self._definitions[key] = definition
            for alias in definition.aliases:
                alias_key = (alias, definition.version)
                if alias_key in self._aliases or alias_key in self._definitions:
                    raise ValueError(f"duplicate verifier alias: {alias}@{definition.version}")
                self._aliases[alias_key] = key
        for alias_key in self._aliases:
            if alias_key in self._definitions:
                raise ValueError(f"verifier alias collides with canonical ID: {alias_key[0]}@{alias_key[1]}")

    def resolve(self, verifier_id: str, version: str | None = None) -> VerifierDefinition:
        if version and (verifier_id, version) in self._aliases:
            verifier_id, version = self._aliases[(verifier_id, version)]
        elif not version:
            alias_versions = [key for key in self._aliases if key[0] == verifier_id]
            if alias_versions:
                alias_version = sorted((key[1] for key in alias_versions), key=_version_key)[-1]
                verifier_id, version = self._aliases[(verifier_id, alias_version)]
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
        explicit_refs = request.get("evidence_refs", ())
        evidence_items = request.get("evidence", ())
        inferred_refs = tuple(str(item.get("ref")) for item in evidence_items if isinstance(item, Mapping) and item.get("ref"))
        base = {"verifier_id": definition.verifier_id, "verifier_version": definition.version,
                "evidence_refs": tuple(explicit_refs) or inferred_refs,
                "request_id": request.get("request_id")}
        if not definition.entrypoint:
            return {**base, "execution_status": "unchecked", "verdict": "unchecked", "uncertainty_reason": "instruction-only verifier; follow VERIFIER.md manually"}
        execution = run_stdio(definition.path, definition.entrypoint, request, timeout=timeout)
        if execution.status == "timed_out":
            return {**base, "execution_status": "timed_out", "verdict": "timed_out", "uncertainty_reason": f"verifier timed out after {timeout}s"}
        if execution.status in {"error", "denied", "input_too_large", "output_too_large", "invalid_input"}:
            return {**base, "execution_status": "error", "verdict": "error", "uncertainty_reason": execution.detail}
        if execution.status == "invalid_json":
            return {**base, "execution_status": "error", "verdict": "error", "uncertainty_reason": f"invalid verifier JSON: {execution.detail}"}
        raw = execution.value
        if not isinstance(raw, Mapping):
            return {**base, "execution_status": "error", "verdict": "error", "uncertainty_reason": "invalid verifier JSON: verifier output must be a JSON object"}
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
    assurance_tier: str = "deterministic"
    protocol: str = "bensz-verification-v1"

    def __post_init__(self) -> None:
        if self.execution_status not in EXECUTION_STATUSES:
            raise ValueError(f"invalid execution_status: {self.execution_status}")
        if self.verdict not in VERDICTS:
            raise ValueError(f"invalid verdict: {self.verdict}")
        if self.execution_status != "completed" and self.verdict == "pass":
            raise ValueError("non-completed execution cannot pass")
        if self.verdict == "timed_out" and self.execution_status != "timed_out":
            raise ValueError("timed_out verdict requires timed_out execution")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.assurance_tier not in ASSURANCE_TIERS:
            raise ValueError(f"unsupported assurance tier: {self.assurance_tier}")

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
        self._aliases: dict[tuple[str, str], tuple[str, str]] = {}

    def register(self, pack: VerifierPack) -> None:
        key = (pack.spec.verifier_id, pack.spec.version)
        if key in self._packs or key in self._aliases:
            raise ValueError(f"pack already registered: {key[0]}@{key[1]}")
        self._packs[key] = pack
        for alias in pack.spec.aliases:
            alias_key = (alias, pack.spec.version)
            if alias_key in self._aliases or alias_key in self._packs:
                raise ValueError(f"duplicate verifier alias: {alias}@{pack.spec.version}")
            self._aliases[alias_key] = key
        for alias_key in self._aliases:
            if alias_key in self._packs:
                raise ValueError(f"verifier alias collides with canonical ID: {alias_key[0]}@{alias_key[1]}")

    def resolve(self, verifier_id: str, version: str | None = None) -> VerifierPack:
        if version and (verifier_id, version) in self._aliases:
            verifier_id, version = self._aliases[(verifier_id, version)]
        elif not version:
            alias_versions = [key for key in self._aliases if key[0] == verifier_id]
            if alias_versions:
                alias_version = sorted((key[1] for key in alias_versions), key=_version_key)[-1]
                verifier_id, version = self._aliases[(verifier_id, alias_version)]
        if version:
            try:
                return self._packs[(verifier_id, version)]
            except KeyError as exc:
                raise KeyError(f"pack not found: {verifier_id}@{version}") from exc
        candidates = [p for (identifier, _), p in self._packs.items() if identifier == verifier_id]
        if not candidates:
            raise KeyError(f"pack not found: {verifier_id}")
        return sorted(candidates, key=lambda p: _version_key(p.spec.version))[-1]

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
        if execution != "completed" and verdict == "pass":
            raise ValueError("non-completed execution cannot pass")
        if verdict == "timed_out" and execution != "timed_out":
            raise ValueError("timed_out verdict requires timed_out execution")
        refs = tuple(raw.get("evidence_refs", evidence_refs))
        return VerificationResult(verifier_id=spec.verifier_id, verifier_version=spec.version, execution_status=execution, verdict=verdict, findings=tuple(raw.get("findings", ())), facts=dict(raw.get("facts", {})), evidence_refs=refs, confidence=raw.get("confidence"), uncertainty_reason=raw.get("uncertainty_reason"), model_or_engine=raw.get("model_or_engine"), duration_ms=raw.get("duration_ms"), assurance_tier=str(raw.get("assurance_tier", spec.assurance_tier)))
    except (KeyError, TypeError, ValueError):
        return VerificationResult(verifier_id=spec.verifier_id, verifier_version=spec.version, execution_status="unchecked", verdict="unchecked", uncertainty_reason="invalid verifier output", evidence_refs=tuple(evidence_refs))


def apply_gate(results: Iterable[VerificationResult], *, required: bool = True,
               required_ids: Iterable[str] | None = None,
               requirements: Mapping[str, bool] | Iterable[Mapping[str, Any]] | None = None) -> GateDecision:
    """Apply conservative gate semantics; deterministic failures cannot be averaged away."""
    items = tuple(results)
    refs = tuple(f"{r.verifier_id}@{r.verifier_version}" for r in items)
    if not items:
        return GateDecision("wait", "no verification result", refs, ("missing_result",))
    if requirements is not None:
        if isinstance(requirements, Mapping):
            required_set = {str(key) for key, value in requirements.items() if bool(value)}
        else:
            required_set = {str(item.get("verifier_id", item.get("id"))) for item in requirements if isinstance(item, Mapping) and item.get("verifier_id", item.get("id")) and bool(item.get("required", False))}
    elif required_ids is not None:
        required_set = {str(item) for item in required_ids}
    else:
        required_set = {r.verifier_id for r in items} if required else set()
    failures = [r for r in items if r.verdict in {"fail", "error"}]
    unknown = [r for r in items if r.verdict in {"unchecked", "uncertain", "timed_out"}]
    required_failures = [r for r in failures if r.verifier_id in required_set]
    if required_failures:
        return GateDecision("reject", "required verifier failure", refs, tuple(r.verifier_id for r in required_failures))
    if unknown:
        return GateDecision("manual_review", "verification gap or semantic uncertainty", refs, tuple(r.verifier_id for r in unknown))
    if failures:
        return GateDecision("allow_with_warnings", "optional verifier failure", refs, tuple(r.verifier_id for r in failures))
    return GateDecision("allow", "all required verifiers passed", refs)


def normalize_requirements(
    requirements: Iterable[Mapping[str, Any]],
    registry: Any,
    *,
    required_ids: Iterable[str] = (),
) -> tuple[dict[str, Any], ...]:
    """Validate and canonicalize a Skill's runtime verifier declaration.

    Unknown IDs, duplicate canonical IDs, malformed versions and non-boolean
    ``required`` flags fail closed before any verifier is executed.  Aliases
    are accepted only as compatibility input and are emitted canonically.
    """
    if requirements is None or isinstance(requirements, (str, bytes, Mapping)):
        raise ValueError("verifier requirements must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    required_set = {str(item) for item in required_ids}
    for item in requirements:
        if not isinstance(item, Mapping) or not item.get("id", item.get("verifier_id")):
            raise ValueError("each verifier requirement requires id")
        requested = str(item.get("id", item.get("verifier_id")))
        version = str(item.get("version", ""))
        if not version or not _VERSION_RE.match(version):
            raise ValueError(f"invalid verifier version for {requested}: {version!r}")
        try:
            definition = registry.resolve(requested, version)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"unknown verifier: {requested}@{version}") from exc
        canonical = definition.verifier_id
        if canonical in seen:
            raise ValueError(f"duplicate verifier requirement: {canonical}")
        raw_required = item.get("required", canonical in required_set)
        if not isinstance(raw_required, bool):
            raise ValueError(f"verifier required must be boolean: {canonical}")
        seen.add(canonical)
        normalized.append({"id": canonical, "version": definition.version, "required": raw_required})
    return tuple(normalized)


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


def summarize_metrics(results: Iterable[VerificationResult], gates: Iterable[GateDecision] = (), *, required_ids: Iterable[str] | None = None) -> dict[str, Any]:
    """Return deterministic P2 assurance and coverage metrics."""
    items = tuple(results)
    gate_items = tuple(gates)
    required_set = set(str(item) for item in required_ids) if required_ids is not None else {item.verifier_id for item in items}
    covered = {item.verifier_id for item in items}
    required = len(required_set)
    passed = sum(item.verdict == "pass" and item.execution_status == "completed" for item in items)
    return {
        "verifier_count": required,
        "required_coverage": len(required_set & covered) / required if required else 0.0,
        "pass_rate": passed / len(items) if items else 0.0,
        "unchecked_ratio": sum(item.verdict == "unchecked" for item in items) / len(items) if items else 0.0,
        "uncertain_ratio": sum(item.verdict == "uncertain" for item in items) / len(items) if items else 0.0,
        "gate_allow_rate": sum(g.decision in {"allow", "allow_with_warnings"} for g in gate_items) / len(gate_items) if gate_items else 0.0,
        "assurance_tiers": {tier: sum(item.assurance_tier == tier for item in items) for tier in sorted(ASSURANCE_TIERS)},
        "duration_ms": sum(item.duration_ms or 0 for item in items),
    }
