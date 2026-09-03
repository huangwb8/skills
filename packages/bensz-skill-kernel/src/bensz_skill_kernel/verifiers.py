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

from .contract_packs import ContractExecutionError, ContractExecutionReport, ContractPack, ContractPackExecutor, EXECUTION_MODES
from .packs import load_pack_entries, resolve_entrypoint, run_stdio, version_key as _version_key
from .verifier_ids import parse_aliases, validate_verifier_id

VERDICTS = frozenset({"pass", "fail", "uncertain", "unchecked", "error", "timed_out", "skipped"})
EXECUTION_STATUSES = frozenset({"completed", "unchecked", "error", "timed_out", "skipped"})
MODES = EXECUTION_MODES
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
    mode: str = "human"

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
        mode = fields.get("mode", "rule" if entrypoint else "human")
        if mode not in MODES:
            raise ValueError(f"unsupported verifier mode: {mode}")
        reserved = {"id", "verifier_id", "version", "description", "entrypoint", "script", "tags", "aliases", "assurance_tier", "mode"}
        metadata = {key: value for key, value in fields.items() if key not in reserved}
        return cls(verifier_id, version, root, instructions, fields.get("description", ""), entrypoint, tags, metadata, aliases, fields.get("classification", "domain"), assurance_tier, mode)

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
        mode = str(entry.get("mode", "rule" if entrypoint else "human"))
        if mode not in MODES:
            raise ValueError(f"unsupported verifier mode: {mode}")
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
            mode=mode,
        )

    @property
    def spec(self) -> VerifierSpec:
        return VerifierSpec(
            verifier_id=self.verifier_id,
            version=self.version,
            mode=self.mode,
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
            "mode": self.mode,
            "execution_contract": self.contract_pack().audit_dict(),
        }

    def contract_pack(self) -> ContractPack:
        """Return the shared executable descriptor for this filesystem Pack."""
        index = self.metadata.get("index")
        if isinstance(index, Mapping):
            entry = dict(index)
        else:
            entry = {
                "id": self.verifier_id,
                "version": self.version,
                "contract": "VERIFIER.md",
                "entrypoint": self.entrypoint,
                "mode": self.mode,
                "assurance_tier": self.assurance_tier,
                "aliases": list(self.aliases),
            }
        return ContractPack.from_directory(
            self.path,
            package_kind="verifier",
            contract_name="VERIFIER.md",
            entry=entry,
        )


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
        if not isinstance(request, Mapping):
            return {
                "verifier_id": definition.verifier_id,
                "verifier_version": definition.version,
                "evidence_refs": (),
                "request_id": None,
                "execution_status": "error",
                "verdict": "error",
                "uncertainty_reason": "invalid verifier request: request must be a JSON object",
            }
        explicit_refs = request.get("evidence_refs", ())
        evidence_items = request.get("evidence", ())
        inferred_refs = tuple(str(item.get("ref")) for item in evidence_items if isinstance(item, Mapping) and item.get("ref"))
        base = {"verifier_id": definition.verifier_id, "verifier_version": definition.version,
                "evidence_refs": tuple(explicit_refs) or inferred_refs,
                "request_id": request.get("request_id")}
        index = definition.metadata.get("index")
        if isinstance(index, Mapping) and "components" in index:
            try:
                execution = self.run_contract(
                    verifier_id,
                    request,
                    version=version,
                    timeout=timeout,
                    run_id=str(request.get("run_id", request.get("request_id", "run"))),
                    attempt_id=str(request.get("attempt_id", "default")),
                    submissions=request.get("component_results", request.get("submissions", ())),
                )
                return {**execution.to_event_payload(), "request_id": request.get("request_id")}
            except ContractExecutionError as exc:
                return {**base, "execution_status": "error", "verdict": "error", "uncertainty_reason": str(exc)}
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

    def run_contract(
        self,
        verifier_id: str,
        request: Mapping[str, Any] | VerificationRequest,
        *,
        version: str | None = None,
        timeout: int = 30,
        run_id: str = "run",
        attempt_id: str = "default",
        submissions: Iterable[Mapping[str, Any]] = (),
    ) -> "VerifierContractExecution":
        """Execute a filesystem Pack through the shared component protocol."""
        definition = self.resolve(verifier_id, version)
        if isinstance(request, VerificationRequest):
            request = request.to_dict()
        if not isinstance(request, Mapping):
            raise TypeError("verifier request must be an object")
        report = ContractPackExecutor().execute(
            definition.contract_pack(),
            request=request,
            submissions=submissions,
            run_id=run_id,
            attempt_id=attempt_id,
            timeout=timeout,
        )
        return VerifierContractAdapter().adapt(definition.spec, report)


class CombinedVerifierRegistry:
    """Read-only union of built-in and Skill-local Verifier Pack roots."""

    def __init__(self, *registries: FilesystemVerifierRegistry):
        self.registries = registries
        self._definitions: dict[tuple[str, str], VerifierDefinition] = {}
        self._aliases: dict[tuple[str, str], tuple[str, str]] = {}
        for registry in registries:
            for definition in registry.definitions():
                key = (definition.verifier_id, definition.version)
                if key in self._definitions or key in self._aliases:
                    raise ValueError(f"duplicate verifier: {definition.verifier_id}@{definition.version}")
                self._definitions[key] = definition
                for alias in definition.aliases:
                    alias_key = (alias, definition.version)
                    if alias_key in self._definitions or alias_key in self._aliases:
                        raise ValueError(f"duplicate verifier alias: {alias}@{definition.version}")
                    self._aliases[alias_key] = key

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
    contract_hash: str | None = None
    plan_hash: str | None = None
    component_id: str | None = None
    component_type: str | None = None
    component_hash: str | None = None
    handoff_hash: str | None = None
    run_id: str | None = None
    attempt_id: str | None = None
    executor: Mapping[str, Any] = field(default_factory=dict)
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


@dataclass(frozen=True)
class VerifierContractExecution:
    """Verifier-specific view over a domain-neutral component execution."""

    aggregate: VerificationResult
    components: tuple[VerificationResult, ...]
    gate: GateDecision
    report: ContractExecutionReport

    def to_event_payload(self) -> dict[str, Any]:
        return {
            **self.aggregate.to_dict(),
            "protocol": "bensz-verification-v2",
            "contract_hash": self.report.contract_hash,
            "plan_hash": self.report.plan_hash,
            "run_id": self.report.run_id,
            "attempt_id": self.report.attempt_id,
            "execution_plan": dict(self.report.execution_plan),
            # Persist the shared Contract component shape so the runtime can
            # independently verify every binding before it records a Gate.
            "component_results": [item.to_dict() for item in self.report.results],
            "execution_decision": self.report.decision,
            "unresolved_components": list(self.report.unresolved),
        }


class VerifierContractAdapter:
    """Interpret shared component results as a Verifier verdict and Gate."""

    def adapt(self, spec: VerifierSpec, report: ContractExecutionReport) -> VerifierContractExecution:
        if report.pack_id != spec.verifier_id or report.pack_version != spec.version:
            raise ValueError("Verifier Contract Pack identity mismatch")
        components = tuple(
            VerificationResult(
                verifier_id=spec.verifier_id,
                verifier_version=spec.version,
                execution_status="unchecked" if item.execution_status == "pending" else item.execution_status,
                verdict=item.verdict,
                findings=item.findings,
                facts=item.facts,
                evidence_refs=item.evidence_refs,
                uncertainty_reason=item.uncertainty_reason,
                model_or_engine=str(item.executor.get("model")) if item.executor.get("model") else None,
                assurance_tier=item.assurance,
                contract_hash=item.contract_hash,
                plan_hash=item.plan_hash,
                component_id=item.component_id,
                component_type=item.component_type,
                component_hash=item.component_hash,
                handoff_hash=item.handoff_hash,
                run_id=item.run_id,
                attempt_id=item.attempt_id,
                executor=dict(item.executor),
                protocol="bensz-verification-v2",
            )
            for item in report.results
        )
        if report.decision in {"completed", "completed_with_warnings"}:
            status, verdict = "completed", "pass"
        elif report.decision == "reject":
            status, verdict = "completed", "fail"
        elif any(item.verdict == "timed_out" for item in report.results):
            status, verdict = "timed_out", "timed_out"
        elif any(item.verdict == "error" for item in report.results):
            status, verdict = "error", "error"
        elif report.decision == "manual_review":
            status, verdict = "completed", "uncertain"
        else:
            status, verdict = "unchecked", "unchecked"
        refs = tuple(dict.fromkeys(ref for item in report.results for ref in item.evidence_refs))
        findings = tuple(finding for item in report.results for finding in item.findings)
        if len(report.results) == 1:
            facts: Mapping[str, Any] = dict(report.results[0].facts)
        else:
            facts = {item.component_id: dict(item.facts) for item in report.results}
        aggregate = VerificationResult(
            verifier_id=spec.verifier_id,
            verifier_version=spec.version,
            execution_status=status,
            verdict=verdict,
            findings=findings,
            facts=facts,
            evidence_refs=refs,
            uncertainty_reason=("unresolved components: " + ", ".join(report.unresolved)) if report.unresolved else None,
            assurance_tier=spec.assurance_tier,
            contract_hash=report.contract_hash,
            plan_hash=report.plan_hash,
            run_id=report.run_id,
            attempt_id=report.attempt_id,
            protocol="bensz-verification-v2",
        )
        decision = {
            "completed": "allow",
            "completed_with_warnings": "allow_with_warnings",
            "reject": "reject",
            "manual_review": "manual_review",
            "wait": "wait",
        }[report.decision]
        gate = GateDecision(
            decision,
            f"Contract components {report.decision}",
            (f"{spec.verifier_id}@{spec.version}",),
            report.unresolved,
        )
        return VerifierContractExecution(aggregate, components, gate, report)


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
        return VerificationResult(verifier_id=spec.verifier_id, verifier_version=spec.version, execution_status=execution, verdict=verdict, findings=tuple(raw.get("findings", ())), facts=dict(raw.get("facts", {})), evidence_refs=refs, confidence=raw.get("confidence"), uncertainty_reason=raw.get("uncertainty_reason"), model_or_engine=raw.get("model_or_engine"), duration_ms=raw.get("duration_ms"), assurance_tier=str(raw.get("assurance_tier", spec.assurance_tier)), contract_hash=raw.get("contract_hash"), plan_hash=raw.get("plan_hash"), component_id=raw.get("component_id"), component_type=raw.get("component_type"), component_hash=raw.get("component_hash"), handoff_hash=raw.get("handoff_hash"), run_id=raw.get("run_id"), attempt_id=raw.get("attempt_id"), executor=dict(raw.get("executor", {})), protocol=str(raw.get("protocol", "bensz-verification-v1")))
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
    invalid_requirements: list[str] = []
    required_versions: dict[str, str | None] = {}
    if requirements is not None:
        if isinstance(requirements, Mapping):
            required_set = set()
            for key, value in requirements.items():
                if not isinstance(value, bool):
                    invalid_requirements.append("invalid_requirement")
                    continue
                if value:
                    required_set.add(str(key))
            required_versions = {key: None for key in required_set}
        else:
            required_set = set()
            for item in requirements:
                if not isinstance(item, Mapping):
                    invalid_requirements.append("invalid_requirement")
                    continue
                identifier = item.get("verifier_id", item.get("id"))
                required_flag = item.get("required", False)
                if not identifier or not isinstance(required_flag, bool):
                    invalid_requirements.append("invalid_requirement")
                    continue
                version = item.get("version")
                if version is not None and (not isinstance(version, str) or not _VERSION_RE.match(version)):
                    invalid_requirements.append("invalid_requirement")
                    continue
                if required_flag:
                    canonical = str(identifier)
                    required_set.add(canonical)
                    required_versions[canonical] = version
    elif required_ids is not None:
        required_set = {str(item) for item in required_ids}
    else:
        required_set = {r.verifier_id for r in items} if required else set()
    actual_ids = {r.verifier_id for r in items}
    if invalid_requirements:
        return GateDecision("manual_review", "invalid verifier requirements", refs, tuple(sorted(set(invalid_requirements))))
    missing_required = tuple(sorted(required_set - actual_ids))
    if missing_required:
        return GateDecision(
            "manual_review",
            "required verifier result missing",
            refs,
            missing_required,
        )
    mismatched_versions = tuple(sorted(
        f"{verifier_id}@{version}"
        for verifier_id, version in required_versions.items()
        if version is not None
        and not any(r.verifier_id == verifier_id and r.verifier_version == version for r in items)
    ))
    if mismatched_versions:
        return GateDecision("manual_review", "required verifier version mismatch", refs, mismatched_versions)
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
    components = tuple(item for item in items if item.component_id is not None)
    bound_components = tuple(
        item for item in components
        if item.contract_hash and item.plan_hash and item.component_hash and item.run_id and item.attempt_id
    )
    identified_executors = tuple(item for item in components if item.executor.get("id") and item.executor.get("type"))
    return {
        "verifier_count": required,
        "required_coverage": len(required_set & covered) / required if required else 0.0,
        "pass_rate": passed / len(items) if items else 0.0,
        "unchecked_ratio": sum(item.verdict == "unchecked" for item in items) / len(items) if items else 0.0,
        "uncertain_ratio": sum(item.verdict == "uncertain" for item in items) / len(items) if items else 0.0,
        "gate_allow_rate": sum(g.decision in {"allow", "allow_with_warnings"} for g in gate_items) / len(gate_items) if gate_items else 0.0,
        "assurance_tiers": {tier: sum(item.assurance_tier == tier for item in items) for tier in sorted(ASSURANCE_TIERS)},
        "duration_ms": sum(item.duration_ms or 0 for item in items),
        "component_count": len(components),
        "bound_component_ratio": len(bound_components) / len(components) if components else 0.0,
        "executor_identity_ratio": len(identified_executors) / len(components) if components else 0.0,
    }
